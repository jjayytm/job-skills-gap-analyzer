"""
app/llm.py
==========
LLM-powered recommendations for the resume gap report.

- Skill recommendations: turns raw gap phrases into real, hireable skills.
- Resume rewrite suggestions: returns structured JSON (copy/paste friendly) for
  suggested bullets grouped by role + gap summary.

Uses the Anthropic API (Claude). Set ANTHROPIC_API_KEY; optional ANTHROPIC_MODEL
overrides the default model id.

Notes:
- Never invent employers, titles, dates, tools, or achievements.
- Use placeholders like [X%] / [metric] when impact data is missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.nlp import SkillMatch

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
# Fast, cost-effective; see https://docs.anthropic.com/en/docs/about-claude/models
# (Older ids like claude-3-5-haiku-20241022 may 404 on the current API.)
DEFAULT_MODEL = "claude-haiku-4-5-20251001"          # skill recommendations: fast, cheap, JSON-heavy
DEFAULT_MODEL_REWRITE = "claude-sonnet-4-6"          # resume rewrites: better reasoning needed

MAX_JOB_DESC_CHARS = 6000
MAX_RESUME_CHARS = 12000

MAX_PARTIAL_PHRASES = 30
MAX_MISSING_PHRASES = 40

# Project root (app/llm.py -> app/ -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """Load .env from project root and from current working directory."""
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH)
        load_dotenv()  # also try cwd (e.g. when run from project root)
    except Exception:
        pass


def _get_key() -> str:
    """Return the API key (empty if missing or placeholder)."""
    _load_env()
    key = (os.environ.get(ANTHROPIC_API_KEY_ENV) or "").strip().strip('"').strip("'")
    placeholders = (
        "none",
        "your-key",
        "sk-your-anthropic-api-key-here",
        "your-anthropic-api-key-here",
    )
    if not key or key.lower() in placeholders:
        return ""
    return key


def _resolved_model(explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    _load_env()
    env_model = (os.environ.get("ANTHROPIC_MODEL") or "").strip()
    return env_model or DEFAULT_MODEL


def get_llm_status() -> dict:
    """
    For debugging: return status of .env and API key (never the key value).
    Keys: env_path, env_exists, cwd, key_set
    """
    _load_env()
    key = _get_key()
    cwd = Path.cwd()
    return {
        "env_path": str(_ENV_PATH),
        "env_exists": _ENV_PATH.is_file(),
        "cwd": str(cwd),
        "key_set": bool(key),
    }


def _get_client():
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    key = _get_key()
    if not key:
        return None
    return Anthropic(api_key=key)


def _anthropic_text_response(
    client,
    *,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float | None = None,
) -> str:
    """Run a single user turn with optional system prompt; return assistant text."""
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    msg = client.messages.create(**kwargs)
    blocks = getattr(msg, "content", None) or []
    parts: list[str] = []
    for block in blocks:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _strip_code_fences(text: str) -> str:
    """Remove ``` or ```json fences if the model returns them."""
    if not text:
        return ""
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    # drop first fence line
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    # drop last fence line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _safe_json_load(text: str) -> dict:
    """
    Parse JSON safely, after removing code fences.
    Raises json.JSONDecodeError if invalid.
    """
    cleaned = _strip_code_fences(text)
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Skill recommendations (gap phrases -> hireable skills)
# ---------------------------------------------------------------------------

def _build_skill_prompt(
    job_title: str,
    job_description: str,
    partial_matches: list[SkillMatch],
    missing_matches: list[SkillMatch],
) -> str:
    job_desc = (job_description or "")[:MAX_JOB_DESC_CHARS]
    partial_phrases = [m.job_skill for m in partial_matches[:MAX_PARTIAL_PHRASES]]
    missing_phrases = [m.job_skill for m in missing_matches[:MAX_MISSING_PHRASES]]

    return f"""You are a career coach and resume expert. Based on the job posting and the gap analysis below, suggest only REAL, HIREABLE SKILLS that the candidate should add or strengthen on their resume.

RULES:
- Output ONLY actual skills: tools (Excel, Python, Power BI), methodologies (financial modeling, DCF, valuation), certifications (CFA, CPA), and competencies (stakeholder communication, project management).
- EXCLUDE: common words, filler, locations, company names, single generic words (e.g. "day", "company", "clients", "success"), demographic terms, or long sentence fragments.
- If the raw phrases contain no real skills, infer the most important skills for this role from the job description and suggest those.
- Keep each skill name short (2–5 words). Suggestions should be one short sentence.

Job title: {job_title}

Job description (excerpt):
{job_desc}

Raw "partial match" phrases from our system (candidate is close; suggest how to strengthen):
{json.dumps(partial_phrases)}

Raw "missing" phrases from our system (candidate is missing; suggest top skills to add):
{json.dumps(missing_phrases)}

Respond with valid JSON only, no markdown or explanation:
{{
  "strengthen": [
    {{ "skill": "Skill name", "suggestion": "One short actionable suggestion." }}
  ],
  "add": [
    {{ "skill": "Skill name", "suggestion": "One short actionable suggestion." }}
  ]
}}

Return 4–8 items in "strengthen" and 6–12 items in "add". Only include real skills that would help the candidate get hired for this role."""


def get_skill_recommendations(
    job_title: str,
    job_description: str,
    partial_matches: list[SkillMatch],
    missing_matches: list[SkillMatch],
    model: str = DEFAULT_MODEL,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], str | None]:
    """
    Call the LLM to get resume-worthy skills and suggestions.

    Returns:
        (strengthen_list, add_list, error_message)
        - strengthen_list: [(skill, suggestion), ...]
        - add_list: [(skill, suggestion), ...]
        - error_message: None on success, else a short message for the UI
    """
    client = _get_client()
    if not client:
        return [], [], "No API key. Set ANTHROPIC_API_KEY in environment or in Streamlit secrets to enable AI recommendations."

    prompt = _build_skill_prompt(job_title, job_description, partial_matches, missing_matches)
    use_model = _resolved_model(model)

    try:
        text = _anthropic_text_response(
            client,
            model=use_model,
            system="You output only valid JSON. No markdown code blocks, no extra text.",
            user=prompt,
            max_tokens=1500,
            temperature=0.3,
        )
        data = _safe_json_load(text)

        strengthen = [
            (item["skill"], item.get("suggestion", "Add or strengthen on resume."))
            for item in (data.get("strengthen") or [])
            if isinstance(item, dict) and item.get("skill")
        ]
        add = [
            (item["skill"], item.get("suggestion", "Consider adding if you have experience."))
            for item in (data.get("add") or [])
            if isinstance(item, dict) and item.get("skill")
        ]
        return strengthen, add, None

    except json.JSONDecodeError as e:
        return [], [], f"Could not parse AI response: {e}"
    except Exception as e:
        return [], [], str(e)


# ---------------------------------------------------------------------------
# Resume rewrite suggestions (structured JSON for sleek UI)
# ---------------------------------------------------------------------------

def get_resume_rewrite_suggestions(
    job_title: str,
    job_description: str,
    resume_text: str,
    model: str = DEFAULT_MODEL_REWRITE,
) -> tuple[str, str | None]:
    """
    LLM as senior resume strategist: returns structured JSON for:
      - gap summary
      - suggested bullets grouped by role
      - evidence/metrics the user should add

    Returns:
        (json_text, error_message)

    NOTE:
    - This function now returns JSON (string). Render it in the UI as cards
      and copy-ready bullet blocks.
    """
    client = _get_client()
    if not client:
        return "", "No API key. Set ANTHROPIC_API_KEY to enable AI resume suggestions."

    job_desc = (job_description or "")[:MAX_JOB_DESC_CHARS]
    resume_excerpt = (resume_text or "")[:MAX_RESUME_CHARS]

    prompt = f"""You are a senior resume strategist and hiring manager.

Goal:
Strengthen my resume to maximize interview probability for this role.

Constraints:
- Do NOT invent employers, titles, dates, tools, or achievements.
- Only expand/reframe existing experience.
- ATS-friendly, concise, action-oriented.
- Prefer 1-line bullets when possible (aim for <= 30 words; ok to exceed if needed).

Output:
Return ONLY valid JSON (no markdown, no explanation) in this schema:
{{
  "gap_summary": {{
    "core_technical": ["..."],
    "domain_knowledge": ["..."],
    "implicit_senior_skills": ["..."],
    "narrative_gaps": ["..."]
  }},
  "roles": [
    {{
      "role_title": "Exact existing role title from my resume",
      "company": "Exact existing company from my resume",
      "suggested_bullets": ["Copy-ready bullet 1", "Copy-ready bullet 2"],
      "evidence_needed": ["What metric/proof to add", "What context to clarify"]
    }}
  ]
}}

Rules:
- Use ONLY roles that already exist in MY RESUME.
- If you cannot find roles reliably due to formatting, return a single role with:
  role_title = "General (place under most relevant role)" and company = "".
- Bullets must be copy/paste ready (start with a strong verb, no filler).
- Do not mention that you are an AI. Do not include disclaimers.

--- JOB POSTING ---
Title: {job_title}

Description:
{job_desc}

--- MY RESUME ---
{resume_excerpt}
"""

    use_model = _resolved_model(model)

    try:
        text = _anthropic_text_response(
            client,
            model=use_model,
            system="Return only valid JSON. Do not invent employers, titles, dates, tools, or achievements.",
            user=prompt,
            max_tokens=2500,
            temperature=0.35,
        )
        data = _safe_json_load(text)

        # Normalize to a stable JSON string (pretty-printed) for UI parsing/debugging
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        return json_text, None

    except json.JSONDecodeError as e:
        return "", f"Could not parse AI JSON: {e}"
    except Exception as e:
        return "", str(e)