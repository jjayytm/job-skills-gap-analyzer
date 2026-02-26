## NLP Pipeline Overview

This app’s NLP pipeline turns raw text (job descriptions and resumes) into a structured **skills gap analysis**. The core logic lives in `app/nlp.py`, with LLM helpers in `app/llm.py`.

---

### 1. Skill Extraction (`extract_skills_from_text`)

**Goal:** convert messy text into a clean list of candidate skills.

**Inputs**

- Job description text
- Resume text

**Process**

- **Normalize text**
  - Lowercase, trim whitespace, collapse multiple spaces.

- **Direct matches from curated list**
  - `COMMON_SKILLS` contains common technical and soft skills (e.g. `python`, `sql`, `docker`, `communication`, `time management`).
  - If a skill string appears in the text, its normalized form is added to the candidate set.

- **Linguistic parsing with spaCy**
  - Load spaCy model once via `get_spacy_model()` (cached with `@lru_cache`).
  - Run `doc = nlp(text)`.
  - From `doc`:
    - Take **noun chunks** (`doc.noun_chunks`).
    - Take **named entities** (`doc.ents`).
  - For each chunk/entity:
    - Normalize (lowercase, trim).
    - Discard if:
      - Length \< 3 characters, or
      - Contains digits (likely IDs, dates, etc.).
    - Otherwise add to the candidate set.

- **Output**
  - Combine all candidates into a `set` (no duplicates), sort, and return as a `List[str]`.

---

### 2. Semantic Skill Matching (`compute_skill_matches`)

**Goal:** measure how well each **job skill** is covered by **resume skills**.

**Key types**

- **`SkillMatch` dataclass**
  - `job_skill: str`
  - `best_resume_skill: str | None`
  - `similarity: float` (cosine similarity in \[0, 1\])
  - `coverage_label` property:
    - `"strong"` if similarity ≥ `CONFIG.nlp.similarity_threshold_strong`
    - `"partial"` if similarity ≥ `CONFIG.nlp.similarity_threshold_partial`
    - `"missing"` otherwise

**Process**

- **Normalize & deduplicate**
  - Both job and resume skill strings are normalized via `_normalize_skill` (lowercase, trimmed, single spaces).
  - Convert to sets then back to lists to remove duplicates.

- **Edge cases**
  - No job skills → return `[]`.
  - No resume skills → for each job skill, create a `SkillMatch` with:
    - `best_resume_skill = None`
    - `similarity = 0.0`.

- **Sentence embeddings**
  - Load SentenceTransformer once via `get_sentence_transformer()` (also cached).
  - Compute embeddings:
    - `job_emb = model.encode(job_skills, normalize_embeddings=True)`
    - `resume_emb = model.encode(resume_skills, normalize_embeddings=True)`

- **Cosine similarity matrix**
  - `cosine_scores = cos_sim(job_emb, resume_emb)` → matrix with one row per job skill and one column per resume skill.

- **Best match per job skill**
  - For each job skill row:
    - Find `best_idx = argmax(row)`.
    - `best_score = row[best_idx]`.
    - Create `SkillMatch(job_skill, resume_skills[best_idx], best_score)`.

**Output**

- A list of `SkillMatch` objects, one per job skill, each tied to its best-matching resume skill with a similarity score and coverage label.

---

### 3. Gap Summary (`summarize_gap`)

**Goal:** turn individual `SkillMatch` records into an easy-to-visualize **skills gap summary**.

**Process**

- Split matches by coverage label:
  - `strong = [m for m in matches if m.coverage_label == "strong"]`
  - `partial = [...]`
  - `missing = [...]`

- Compute totals and percentages:
  - `total = len(matches) or 1` (avoid division by zero).
  - Counts per group.
  - Percentages per group (count / total).

**Return structure**

```python
{
  "counts": {
    "strong": <int>,
    "partial": <int>,
    "missing": <int>,
  },
  "percentages": {
    "strong": <float 0–1>,
    "partial": <float 0–1>,
    "missing": <float 0–1>,
  },
  "strong":   [SkillMatch, ...],
  "partial":  [SkillMatch, ...],
  "missing":  [SkillMatch, ...],
}
```

The UI uses this to power:

- Stat tiles (counts and percentages).
- Skill “pills” grouped by **covered**, **partially covered**, and **missing**.
- Inputs to the LLM prompts (see next section).

---

### 4. LLM Layer on Top of NLP (`app/llm.py`)

The classical NLP above is deterministic and explainable. On top of that, the app uses LLMs for two higher-level tasks:

#### 4.1 Skill Recommendations (`get_skill_recommendations`)

- **Inputs**
  - Job title and description.
  - Lists of **partial** and **missing** `SkillMatch` objects.

- **LLM task**
  - Propose:
    - **Skills to strengthen** (improve how existing skills are described on the resume).
    - **Skills to add** (only if the candidate truly has them).

- **Output**
  - JSON arrays `strengthen` and `add`, each entry describing:
    - The skill.
    - A short suggestion for how to reflect it on the resume.

- **UI**
  - Rendered as “Top skills to add or strengthen” with short, actionable tips.

#### 4.2 Resume Rewrite Suggestions (`get_resume_rewrite_suggestions`)

- **Inputs**
  - Job title.
  - Truncated job description (to control token usage).
  - Truncated resume text.

- **LLM prompt**
  - Acts as a **senior resume strategist and hiring manager**.
  - Strict rules:
    - **Never** invent employers, titles, dates, tools, or achievements.
    - Only refactor / expand what is already in the resume.
    - ATS-friendly, action-oriented bullets (prefer ≤ 30 words when possible).
  - Must return **valid JSON only**, with schema:

```json
{
  "gap_summary": {
    "core_technical": ["..."],
    "domain_knowledge": ["..."],
    "implicit_senior_skills": ["..."],
    "narrative_gaps": ["..."]
  },
  "roles": [
    {
      "role_title": "Existing role title",
      "company": "Existing company name",
      "suggested_bullets": ["Copy-ready bullet 1", "Copy-ready bullet 2"],
      "evidence_needed": ["What metric/proof to add", "What context to clarify"]
    }
  ]
}
```

- **Output handling**
  - The raw model response is JSON-parsed and then re-serialized to a stable JSON string for the UI.

- **UI**
  - `gap_summary` → shown as the **Gap Analysis Dashboard**.
  - `roles[*].suggested_bullets` → “Suggested Bullets (Copy-ready)” per role.
  - `roles[*].evidence_needed` → “What evidence to add” expanders.

---

### 5. End-to-End Flow

1. User selects or pastes a **job description** and uploads a **resume**.
2. `extract_skills_from_text` runs on both texts to get job skills and resume skills.
3. `compute_skill_matches` uses SentenceTransformer + cosine similarity to pair each job skill with the closest resume skill.
4. `summarize_gap` groups matches into **strong**, **partial**, and **missing** with counts and percentages.
5. The Streamlit UI:
   - Shows stats and skill pills.
   - Calls `get_skill_recommendations` to propose prioritized skills to add/strengthen.
   - Optionally calls `get_resume_rewrite_suggestions` to produce a structured “AI resume rewrite” with copy-ready bullets aligned to the role.

This combination of transparent NLP and constrained LLM prompts gives you both **explainable metrics** (similarity, coverage labels) and **practical advice** (which skills and bullets to change) for closing the skills gap.

