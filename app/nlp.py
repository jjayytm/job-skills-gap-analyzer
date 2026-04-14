from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, List, Sequence, Tuple

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer

from .config import CONFIG


@lru_cache(maxsize=1)
def get_spacy_model() -> Any:
    """Load and cache the spaCy model defined in AppConfig (default: en_core_web_sm)."""
    return spacy.load(CONFIG.nlp.spacy_model)


@lru_cache(maxsize=1)
def get_sentence_transformer() -> SentenceTransformer:
    """Load and cache the Sentence Transformer model defined in AppConfig (default: all-MiniLM-L6-v2)."""
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

MAX_CANDIDATE_SKILLS = 320
MAX_JOB_SKILLS_FOR_MATCHING = 300
MAX_RESUME_SKILLS_FOR_MATCHING = 420


def _normalize_skill(text: str) -> str:
    """Lowercase and collapse internal whitespace in a skill string."""
    return " ".join(text.lower().strip().split())


def _is_reasonable_skill_candidate(text: str) -> bool:
    """Return True if the text looks like a plausible skill phrase (length and content checks)."""
    if len(text) < 2 or len(text) > 64:
        return False
    if text.count(" ") > 7:
        return False
    if not any(ch.isalpha() for ch in text):
        return False
    return True


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
        if not _is_reasonable_skill_candidate(normalized):
            continue
        if any(ch.isdigit() for ch in normalized):
            continue
        candidates.add(normalized)

    for ent in doc.ents:
        normalized = _normalize_skill(ent.text)
        if not _is_reasonable_skill_candidate(normalized):
            continue
        candidates.add(normalized)

    ordered = sorted(candidates)
    common_hits = [s for s in ordered if s in COMMON_SKILLS]
    others = [s for s in ordered if s not in COMMON_SKILLS]
    others.sort(key=lambda s: (s.count(" "), len(s), s))
    return (common_hits + others)[:MAX_CANDIDATE_SKILLS]


@dataclass
class SkillMatch:
    """Holds the result of matching one job skill against the best resume skill."""

    job_skill: str
    best_resume_skill: str | None
    similarity: float

    @property
    def coverage_label(self) -> str:
        """Return 'strong', 'partial', or 'missing' based on cosine similarity thresholds."""
        if self.similarity >= CONFIG.nlp.similarity_threshold_strong:
            return "strong"
        if self.similarity >= CONFIG.nlp.similarity_threshold_partial:
            return "partial"
        return "missing"


@lru_cache(maxsize=128)
def _encode_sentences_cached(sentences: Tuple[str, ...]) -> np.ndarray:
    """Encode a tuple of sentences into L2-normalized embedding vectors (cached by input)."""
    model = get_sentence_transformer()
    return model.encode(
        list(sentences),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )


def _encode_sentences(sentences: Sequence[str]) -> np.ndarray:
    """Convert a sequence of strings to a cached numpy embedding matrix."""
    return _encode_sentences_cached(tuple(sentences))


def compute_skill_matches(
    job_skills: Sequence[str],
    resume_skills: Sequence[str],
) -> List[SkillMatch]:
    """
    Compute pairwise cosine similarity between job skills and resume skills.

    Each job skill is matched to the highest-scoring resume skill above the
    applicable threshold and wrapped in a SkillMatch dataclass. L2-normalized
    embeddings allow cosine similarity via simple matrix multiplication.
    """
    def _prepare(skills: Sequence[str], limit: int) -> List[str]:
        """Deduplicate, normalize, filter, and cap a skill list to `limit` entries."""
        cleaned = [s for s in {_normalize_skill(s) for s in skills} if _is_reasonable_skill_candidate(s)]
        cleaned.sort(key=lambda s: (s.count(" "), len(s), s))
        return cleaned[:limit]

    job_skills = _prepare(job_skills, MAX_JOB_SKILLS_FOR_MATCHING)
    resume_skills = _prepare(resume_skills, MAX_RESUME_SKILLS_FOR_MATCHING)

    if not job_skills:
        return []

    if not resume_skills:
        return [
            SkillMatch(job_skill=skill, best_resume_skill=None, similarity=0.0)
            for skill in job_skills
        ]

    job_emb = _encode_sentences(job_skills)
    resume_emb = _encode_sentences(resume_skills)

    cosine_scores = np.matmul(job_emb, resume_emb.T)

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
    """
    Aggregate SkillMatch results into counts, percentages, and grouped lists.

    Returns a dict with keys: counts, percentages, strong, partial, missing.
    """
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

