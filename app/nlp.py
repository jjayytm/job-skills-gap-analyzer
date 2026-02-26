from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer, util as st_util

from .config import CONFIG


@lru_cache(maxsize=1)
def get_spacy_model():
    return spacy.load(CONFIG.nlp.spacy_model)


@lru_cache(maxsize=1)
def get_sentence_transformer():
    return SentenceTransformer(CONFIG.nlp.sentence_transformer_model)


COMMON_SKILLS = {
    "python",
    "java",
    "c++",
    "c#",
    "javascript",
    "html",
    "css",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "nlp",
    "natural language processing",
    "machine learning",
    "deep learning",
    "data analysis",
    "data visualization",
    "git",
    "docker",
    "kubernetes",
    "linux",
    "communication",
    "teamwork",
    "problem solving",
    "time management",
}


def _normalize_skill(text: str) -> str:
    return " ".join(text.lower().strip().split())


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract candidate skills from free text using simple heuristics and
    a curated list of common skills. This is intentionally transparent
    and easy to extend for a capstone project.
    """
    if not text:
        return []

    nlp = get_spacy_model()
    doc = nlp(text)

    candidates = set()

    # Direct matches from curated skill list
    lowered = text.lower()
    for skill in COMMON_SKILLS:
        if skill in lowered:
            candidates.add(_normalize_skill(skill))

    # Noun chunks and entities as additional candidates
    for chunk in doc.noun_chunks:
        normalized = _normalize_skill(chunk.text)
        if len(normalized) < 3:
            continue
        if any(ch.isdigit() for ch in normalized):
            continue
        candidates.add(normalized)

    for ent in doc.ents:
        normalized = _normalize_skill(ent.text)
        if len(normalized) < 3:
            continue
        candidates.add(normalized)

    return sorted(candidates)


@dataclass
class SkillMatch:
    job_skill: str
    best_resume_skill: str | None
    similarity: float

    @property
    def coverage_label(self) -> str:
        if self.similarity >= CONFIG.nlp.similarity_threshold_strong:
            return "strong"
        if self.similarity >= CONFIG.nlp.similarity_threshold_partial:
            return "partial"
        return "missing"


def _encode_sentences(sentences: Sequence[str]) -> np.ndarray:
    model = get_sentence_transformer()
    return model.encode(list(sentences), convert_to_tensor=True, normalize_embeddings=True)


def compute_skill_matches(
    job_skills: Sequence[str],
    resume_skills: Sequence[str],
) -> List[SkillMatch]:
    job_skills = [s for s in {_normalize_skill(s) for s in job_skills} if s]
    resume_skills = [s for s in {_normalize_skill(s) for s in resume_skills} if s]

    if not job_skills:
        return []

    if not resume_skills:
        return [
            SkillMatch(job_skill=skill, best_resume_skill=None, similarity=0.0)
            for skill in job_skills
        ]

    job_emb = _encode_sentences(job_skills)
    resume_emb = _encode_sentences(resume_skills)

    cosine_scores = st_util.cos_sim(job_emb, resume_emb).cpu().numpy()

    matches: List[SkillMatch] = []
    for i, job_skill in enumerate(job_skills):
        row = cosine_scores[i]
        best_idx = int(np.argmax(row))
        best_score = float(row[best_idx])
        matches.append(
            SkillMatch(
                job_skill=job_skill,
                best_resume_skill=resume_skills[best_idx],
                similarity=best_score,
            )
        )

    return matches


def summarize_gap(matches: Iterable[SkillMatch]) -> dict:
    matches = list(matches)
    strong = [m for m in matches if m.coverage_label == "strong"]
    partial = [m for m in matches if m.coverage_label == "partial"]
    missing = [m for m in matches if m.coverage_label == "missing"]

    total = len(matches) or 1

    return {
        "counts": {
            "strong": len(strong),
            "partial": len(partial),
            "missing": len(missing),
        },
        "percentages": {
            "strong": len(strong) / total,
            "partial": len(partial) / total,
            "missing": len(missing) / total,
        },
        "strong": strong,
        "partial": partial,
        "missing": missing,
    }

