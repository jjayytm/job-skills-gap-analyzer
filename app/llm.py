"""
app/llm.py
==========
AI-powered recommendations on top of the resume gap analysis.

Two main features:
  1. Skill recommendations  — converts raw gap phrases into real, resume-worthy skills
  2. Resume rewrite         — returns structured JSON with suggested bullets per role

Uses the Anthropic API (Claude). Drop ANTHROPIC_API_KEY into your .env file and you're good to go.
Optional ANTHROPIC_MODEL env var overrides the default model for skill recommendations.

Ground rules baked into every prompt:
  - Never invent employers, titles, dates, or tools
  - Use placeholders like [X%] when specific metrics are missing
  - Output valid JSON only — no markdown, no extra commentary
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.nlp import SkillMatch

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

DEFAULT_MODEL         = "claude-haiku-4-5-20251001"   # fast, cheap — skill recommendations
DEFAULT_MODEL_REWRITE = "claude-sonnet-4-6"            # better reasoning — resume rewrites

MAX_JOB_DESC_CHARS  = 6000
MAX_RESUME_CHARS    = 12000
MAX_PARTIAL_PHRASES = 30
MAX_MISSING_PHRASES = 40

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH     = _PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """Pull in .env from the project root (and cwd as a fallback)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH)
        load_dotenv()
    except Exception:
        pass


def _get_key() -> str:
    """Return the Anthropic API key, or empty string if not set / placeholder."""
    _load_env()
    key = (os.environ.get(ANTHROPIC_API_KEY_ENV) or "").strip().strip('"').strip("'")
    bad_values = {"none", "your-key", "sk-ant-your-key-here", "your-anthropic-api-key-here"}
    if not key or key.lower() in bad_values:
        return ""
    return key


def _pick_model(explicit: str | None, default: str) -> str:
    """Resolve which model to use — explicit arg > env var > built-in default."""
    if explicit and explicit.strip():
        return explicit.strip()
    _load_env()
    from_env = (os.environ.get("ANTHROPIC_MODEL") or "").strip()
    return from_env or default


def get_llm_status() -> dict:
    """Quick debug helper — tells you if the key is loaded without exposing it."""
    _load_env()
    key = _get_key()
    return {
        "env_path":   str(_ENV_PATH),
        "env_exists": _ENV_PATH.is_file(),
        "cwd":        str(Path.cwd()),
        "key_set":    bool(key),
    }


def _get_client() -> Any | None:
    """Build an Anthropic client. Returns None if the library isn't installed or key is missing."""
    try:
        import anthropic
    except ImportError:
        return None
    key = _get_key()
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def _chat(client: Any, *, model: str, system: str, user: str,
          max_tokens: int, temperature: float = 0.3) -> str:
    """Single-turn chat completion via the Anthropic Messages API. Returns the assistant text."""
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return (message.content[0].text or "").strip()


def _strip_fences(text: str) -> str:
    """Strip ```json ... ``` wrappers that some models insist on adding."""
    if not text:
        return ""
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_json(text: str) -> dict:
    """Strip fences then parse. Raises json.JSONDecodeError on bad input."""
    return json.loads(_strip_fences(text))


# ---------------------------------------------------------------------------
# Skill recommendations
# ---------------------------------------------------------------------------

def _skill_prompt(
    job_title: str,
    job_description: str,
    partial_matches: list[SkillMatch],
    missing_matches: list[SkillMatch],
) -> str:
    """Build the Claude prompt for skill recommendations from partial and missing match data."""
    job_desc        = (job_description or "")[:MAX_JOB_DESC_CHARS]
    partial_phrases = [m.job_skill for m in partial_matches[:MAX_PARTIAL_PHRASES]]
    missing_phrases = [m.job_skill for m in missing_matches[:MAX_MISSING_PHRASES]]

    return f"""You are a career coach and resume expert. Based on the job posting and gap analysis below, \
suggest only REAL, HIREABLE SKILLS the candidate should add or strengthen on their resume.

RULES:
- Only suggest actual skills: tools (Python, Power BI, Excel), methodologies (financial modeling, DCF), \
certifications (CFA, PMP), or competencies (stakeholder communication, project management).
- Exclude filler words, locations, company names, single generic words like "clients" or "success", \
or long sentence fragments.
- If the raw phrases have no real skills, infer the most important ones from the job description.
- Keep skill names short (2–5 words). Each suggestion should be one concise sentence.

Job title: {job_title}

Job description (excerpt):
{job_desc}

Partial matches (candidate is close — suggest how to strengthen these):
{json.dumps(partial_phrases)}

Missing skills (candidate needs these — suggest the top ones to add):
{json.dumps(missing_phrases)}

Reply with valid JSON only:
{{
  "strengthen": [
    {{ "skill": "Skill name", "suggestion": "One short actionable suggestion." }}
  ],
  "add": [
    {{ "skill": "Skill name", "suggestion": "One short actionable suggestion." }}
  ]
}}

Return 4–8 items in "strengthen" and 6–12 in "add". Real skills only."""


def get_skill_recommendations(
    job_title: str,
    job_description: str,
    partial_matches: list[SkillMatch],
    missing_matches: list[SkillMatch],
    model: str = DEFAULT_MODEL,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], str | None]:
    """
    Ask the LLM for resume-worthy skills the candidate should work on.

    Returns (strengthen_list, add_list, error_message).
    Both lists are [(skill_name, suggestion), ...].
    error_message is None on success.
    """
    client = _get_client()
    if not client:
        return [], [], (
            "No API key found. Add ANTHROPIC_API_KEY to your .env file "
            "or Streamlit secrets to enable AI recommendations."
        )

    prompt    = _skill_prompt(job_title, job_description, partial_matches, missing_matches)
    use_model = _pick_model(model, DEFAULT_MODEL)

    try:
        raw  = _chat(
            client,
            model=use_model,
            system="Output only valid JSON. No markdown, no extra text.",
            user=prompt,
            max_tokens=1500,
            temperature=0.3,
        )
        data = _parse_json(raw)

        strengthen = [
            (item["skill"], item.get("suggestion", "Add or strengthen on your resume."))
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
        return [], [], f"Couldn't parse the AI response: {e}"
    except Exception as e:
        return [], [], str(e)


# ---------------------------------------------------------------------------
# Resume rewrite suggestions
# ---------------------------------------------------------------------------

def get_resume_rewrite_suggestions(
    job_title: str,
    job_description: str,
    resume_text: str,
    model: str = DEFAULT_MODEL_REWRITE,
) -> tuple[str, str | None]:
    """
    Rewrite the candidate's resume bullets to better match the target role.

    Returns (json_string, error_message).
    The JSON follows this schema:
      {
        "gap_summary": { "core_technical": [...], "domain_knowledge": [...],
                         "implicit_senior_skills": [...], "narrative_gaps": [...] },
        "roles": [
          { "role_title": "...", "company": "...",
            "suggested_bullets": [...], "evidence_needed": [...] }
        ]
      }
    """
    client = _get_client()
    if not client:
        return "", "No API key found. Add ANTHROPIC_API_KEY to enable resume suggestions."

    job_desc       = (job_description or "")[:MAX_JOB_DESC_CHARS]
    resume_excerpt = (resume_text     or "")[:MAX_RESUME_CHARS]

    prompt = f"""You are a senior resume strategist and hiring manager.

Goal:
Strengthen my resume to maximize my chances of getting an interview for this role.

Constraints:
- Do NOT invent employers, titles, dates, tools, or achievements.
- Only reframe or expand on what is already in my resume.
- Write bullets that are ATS-friendly, concise, and action-oriented.
- Keep bullets under 30 words where possible.

Output format:
Return ONLY valid JSON — no markdown, no explanation:
{{
  "gap_summary": {{
    "core_technical": ["..."],
    "domain_knowledge": ["..."],
    "implicit_senior_skills": ["..."],
    "narrative_gaps": ["..."]
  }},
  "roles": [
    {{
      "role_title": "Exact role title from my resume",
      "company": "Exact company from my resume",
      "suggested_bullets": ["Strong verb-led bullet 1", "Strong verb-led bullet 2"],
      "evidence_needed": ["What metric or context would strengthen this bullet"]
    }}
  ]
}}

Rules:
- Only reference roles that actually appear in my resume.
- If resume formatting makes roles hard to detect, use role_title = "General" and company = "".
- No disclaimers. No preamble.

--- JOB POSTING ---
Title: {job_title}

{job_desc}

--- MY RESUME ---
{resume_excerpt}
"""

    use_model = _pick_model(model, DEFAULT_MODEL_REWRITE)

    try:
        raw  = _chat(
            client,
            model=use_model,
            system="Return only valid JSON. Never invent employers, titles, dates, tools, or achievements.",
            user=prompt,
            max_tokens=2500,
            temperature=0.35,
        )
        data = _parse_json(raw)
        return json.dumps(data, ensure_ascii=False, indent=2), None

    except json.JSONDecodeError as e:
        return "", f"Couldn't parse the AI JSON response: {e}"
    except Exception as e:
        return "", str(e)
