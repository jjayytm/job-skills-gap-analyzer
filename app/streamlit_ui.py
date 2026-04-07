"""
app/streamlit_ui.py
==================
Streamlit UI for the Skills Gap Analyzer.

- Load and inject static/styles.css
- Orchestrate the three-step flow: job → resume → analysis
- All HTML is delegated to app/templates.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Load .env from project root (ANTHROPIC_API_KEY, etc.) — .env is in .gitignore
_load_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_load_env_path)

from app.config import CONFIG
from app.llm import (
    ANTHROPIC_API_KEY_ENV,
    get_resume_rewrite_suggestions,
    get_skill_recommendations,
)
from app.nlp import SkillMatch, compute_skill_matches, extract_skills_from_text, summarize_gap
from app.resume_parser import extract_resume_text
from app.models import JobPosting
from app import templates as T

# [cite_start]Static assets: streamlit_ui.py lives in app/, so project root is parent.parent [cite: 583-585]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_FILE = PROJECT_ROOT / "static" / "styles.css"

# [cite_start]Page config must be the first Streamlit call [cite: 586-592]
st.set_page_config(
    page_title="Skills Gap Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _load_css() -> None:
    """Read static/styles.css and inject it once into the page."""
    if CSS_FILE.is_file():
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _intro_splash() -> None:
    """
    One-time fullscreen logo intro (aurum-opt–style), aligned with emerald/dark theme.
    Injects into the parent document; overlay removes itself after the animation.
    """
    if st.query_params.get("nosplash") == "1":
        st.session_state["_skillsync_intro_done"] = True
    if st.session_state.get("_skillsync_intro_done"):
        return
    st.session_state["_skillsync_intro_done"] = True
    components.html(T.intro_splash_component_html(), height=0, scrolling=False)


def _hero() -> None:
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown(
            T.hero_left(
                CONFIG.nlp.similarity_threshold_strong,
                CONFIG.nlp.similarity_threshold_partial,
            ),
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            T.hero_right(
                CONFIG.nlp.similarity_threshold_strong,
                CONFIG.nlp.similarity_threshold_partial,
            ),
            unsafe_allow_html=True,
        )


def _step_job() -> None:
    st.markdown(T.step_badge("01", "Job Description"), unsafe_allow_html=True)
    st.markdown(T.section_heading("Choose a target role"), unsafe_allow_html=True)

    # Only allow pasting a description (Search Indeed removed)
    _tab_paste()

    job: JobPosting | None = st.session_state.get("selected_job")
    if job:
        st.markdown(
            T.job_active_strip(job.title, job.company),
            unsafe_allow_html=True,
        )


def _tab_paste() -> None:
    col_title, col_company = st.columns(2)
    with col_title:
        manual_title = st.text_input(
            "Job title",
            value="",
            placeholder="Target role",
            key="paste_title",
        )
    with col_company:
        manual_company = st.text_input("Company (optional)", key="paste_company")
    manual_desc = st.text_area(
        "Job description",
        height=200,
        placeholder="Paste the full job posting here…",
        key="paste_desc",
    )
    if st.button("Use this description", key="btn_paste"):
        if not manual_desc.strip():
            st.warning("Please paste a job description first.")
        else:
            st.session_state["selected_job"] = JobPosting(
                title=manual_title or "Target Role",
                company=manual_company or "—",
                location="—",
                url="",
                description=manual_desc,
            )
            st.success("Job description saved.")


def _step_resume() -> str:
    st.markdown(T.step_badge("02", "Your Resume"), unsafe_allow_html=True)
    st.markdown(T.section_heading("Upload your CV / resume"), unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drag & drop or click to browse — PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
    )
    resume_text = ""
    if uploaded is None:
        return resume_text
    with st.spinner("Parsing resume…"):
        resume_text = extract_resume_text(uploaded)
    if not resume_text.strip():
        st.error("Could not extract text. Try a different file format.")
        return resume_text
    st.markdown(
        T.resume_strip(uploaded.name, len(resume_text)),
        unsafe_allow_html=True,
    )
    with st.expander("Preview extracted text"):
        st.write(resume_text[:4000] + ("…" if len(resume_text) > 4000 else ""))
    return resume_text


def _step_analysis(job: JobPosting | None, resume_text: str) -> None:
    st.markdown(T.step_badge("03", "Skills Gap Analysis"), unsafe_allow_html=True)
    st.markdown(T.section_heading("Run comparison"), unsafe_allow_html=True)
    if job is None:
        st.info("Complete Step 1 to select a job posting.")
        return
    if not resume_text.strip():
        st.info("Complete Step 2 to upload your resume.")
        return

    job_sig = (job.title, job.company, (job.description or "")[:500])
    resume_sig = (len(resume_text), resume_text[:500])
    sig = (job_sig, resume_sig)
    if st.session_state.get("analysis_sig") != sig:
        st.session_state["analysis_sig"] = sig
        st.session_state.pop("analysis_ready", None)
        st.session_state.pop("analysis_matches", None)
        st.session_state.pop("analysis_summary", None)
        st.session_state.pop("resume_rewrite_md", None)
        st.session_state.pop("resume_rewrite_err", None)
        st.session_state.pop("skill_recommendations", None)

    if st.button("Analyse skills gap", type="primary"):
        with st.spinner("Extracting skills and computing semantic similarity…"):
            job_skills = extract_skills_from_text(job.description)
            resume_skills = extract_skills_from_text(resume_text)
            if not job_skills:
                st.error("No skills could be extracted from the job description.")
                return
            matches = compute_skill_matches(job_skills, resume_skills)
            summary = summarize_gap(matches)
        st.session_state["analysis_ready"] = True
        st.session_state["analysis_matches"] = matches
        st.session_state["analysis_summary"] = summary
        st.session_state["scroll_to_analysis_results"] = True

    if st.session_state.get("analysis_ready"):
        matches = st.session_state.get("analysis_matches", [])
        summary = st.session_state.get("analysis_summary", {})
        _render_results(job, matches, summary, resume_text)


def _scroll_to_element(element_id: str) -> None:
    """Scroll the page to the element with the given id (only when a button triggered the update)."""
    components.html(
        """
        <script>
        (function scrollToEl() {
            var parent = window.parent;
            try {
                var doc = parent.document;
                var el = doc.getElementById('""" + element_id + """');
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    var scrollParent = el.parentElement;
                    while (scrollParent && scrollParent !== doc.body) {
                        var style = parent.getComputedStyle(scrollParent);
                        var oy = style.overflowY || style.overflow;
                        if (oy === 'auto' || oy === 'scroll' || oy === 'overlay') {
                            var top = el.getBoundingClientRect().top + scrollParent.scrollTop;
                            scrollParent.scrollTop = Math.max(0, top - 24);
                            break;
                        }
                        scrollParent = scrollParent.parentElement;
                    }
                    return;
                }
            } catch (e) {}
            if (typeof scrollToEl.n === 'undefined') scrollToEl.n = 0;
            scrollToEl.n++;
            if (scrollToEl.n < 20) setTimeout(scrollToEl, 150);
        })();
        setTimeout(scrollToEl, 400);
        </script>
        """,
        height=0,
        scrolling=False,
    )


def _render_results(
    job: JobPosting,
    matches: List[SkillMatch],
    summary: dict,
    resume_text: str,
) -> None:
    # 1. Results Header & Primary Stats (scroll anchor is on header wrapper in templates)
    st.markdown(T.results_header(job.title), unsafe_allow_html=True)

    tile_config = [
        ("Strong match",  "strong",  "var(--accent)"),
        ("Partial match", "partial", "var(--warn)"),
        ("Missing",       "missing", "var(--danger)"),
    ]

    cols = st.columns(3)
    for col, (title, label, color) in zip(cols, tile_config):
        count = summary["counts"][label]
        pct = summary["percentages"][label] * 100
        with col:
            st.markdown(T.stat_tile(title, count, pct, color), unsafe_allow_html=True)

    if st.session_state.pop("scroll_to_analysis_results", False):
        _scroll_to_element("analysis-results-anchor")

    st.markdown(T.spacer(1.5), unsafe_allow_html=True)

    # 2. Skill Pills (Grouped by Match Strength)
    MAX_PARTIAL_PILLS = 30  # Users mainly scan the top overlaps
    MAX_MISSING_PILLS = 30  # Focus on top missing; AI section below has prioritized list
    pill_config = [
        ("strong",  "Covered skills",           "pill-strong"),
        ("partial", "Partially covered skills", "pill-partial"),
        ("missing", "Missing skills",           "pill-missing"),
    ]
    for label, heading, css_class in pill_config:
        subset: List[SkillMatch] = summary[label]
        if not subset:
            continue
        if label == "partial":
            subset = sorted(subset, key=lambda m: -m.similarity)[:MAX_PARTIAL_PILLS]
        if label == "missing":
            subset = sorted(subset, key=lambda m: -m.similarity)[:MAX_MISSING_PILLS]
        pills = [
            T.pill(m.job_skill, m.best_resume_skill, m.similarity, css_class)
            for m in subset
        ]
        st.markdown(
            T.pill_group_header(heading) + T.pills_wrap(pills),
            unsafe_allow_html=True,
        )
        if label == "partial" and len(summary["partial"]) > MAX_PARTIAL_PILLS:
            st.caption(
                f"Showing top {MAX_PARTIAL_PILLS} partially covered skills (by relevance). "
                "Use the AI recommendations below for the most important ones to strengthen on your resume."
            )
        if label == "missing" and len(summary["missing"]) > MAX_MISSING_PILLS:
            st.caption(
                f"Showing top {MAX_MISSING_PILLS} missing skills (by relevance). "
                "Use **Top skills to add or strengthen** below for what to prioritize on your resume."
            )

    # 3. Next Steps & Skill Recommendations
    st.markdown(T.spacer(1.5), unsafe_allow_html=True)
    steps = [
        "Focus on <strong>partially covered</strong> skills first — add concrete examples or keywords to your resume.",
        "For <strong>missing</strong> skills, add the suggested skills below where you have real experience.",
        "Re-run this analysis after updating your resume to track your progress.",
    ]
    st.markdown(T.next_steps_card(steps), unsafe_allow_html=True)

    # Load API Key logic
    if ANTHROPIC_API_KEY_ENV not in os.environ:
        try:
            key = getattr(st.secrets, ANTHROPIC_API_KEY_ENV, None) or (
                st.secrets.get(ANTHROPIC_API_KEY_ENV) if hasattr(st.secrets, "get") else None
            )
            if key:
                os.environ[ANTHROPIC_API_KEY_ENV] = str(key)
        except Exception:
            pass

    partial_list = summary.get("partial", [])
    missing_list = summary.get("missing", [])
    scroll_top_skills = False

    # Fetch AI Skill Recommendations (cached so resume-rewrite click doesn't re-run spinner)
    cache_key = "skill_recommendations"
    cached = st.session_state.get(cache_key)
    if cached is not None:
        strengthen, add_to_resume, llm_error = cached
    else:
        with st.spinner("Generating resume-worthy skill suggestions…"):
            strengthen, add_to_resume, llm_error = get_skill_recommendations(
                job_title=job.title,
                job_description=job.description or "",
                partial_matches=partial_list,
                missing_matches=missing_list,
            )
        st.session_state[cache_key] = (strengthen, add_to_resume, llm_error)

    if not llm_error:
        st.markdown(T.recommended_skills_section(strengthen, add_to_resume), unsafe_allow_html=True)
        scroll_top_skills = st.session_state.pop("scroll_to_top_skills", False)
        if scroll_top_skills:
            _scroll_to_element("top-skills-anchor")
    else:
        st.error(f"AI Recommendations Error: {llm_error}")

    st.markdown(T.spacer(2), unsafe_allow_html=True)

    # 4. PREMIUM GAP SUMMARY & REWRITE SECTION (single, non-expander block)
    st.markdown(
        '<div id="resume-rewrite-anchor"></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### AI resume rewrite suggestions for this role")
    st.caption("Suggestions reframe your existing experience. They never invent facts.")

    if st.button("Generate resume rewrite suggestions", key="btn_resume_rewrite"):
        # Premium skeleton-style loading state
        _scroll_to_element("resume-rewrite-anchor")
        loading_container = st.empty()
        with loading_container.container():
            st.markdown(
                '<p class="label" style="color:var(--accent); text-transform:uppercase;">AI is analyzing your experience...</p>',
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            for col in cols:
                with col:
                    st.markdown(
                        """
                        <div class="skeleton-card">
                            <div class="shimmer"></div>
                            <div class="skeleton-line" style="width: 40%; background: var(--accent-soft);"></div>
                            <div class="skeleton-line" style="width: 80%;"></div>
                            <div class="skeleton-line" style="width: 70%;"></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        suggestions, err = get_resume_rewrite_suggestions(
            job_title=job.title,
            job_description=job.description or "",
            resume_text=resume_text,
        )
        loading_container.empty()
        st.session_state["resume_rewrite_md"] = suggestions
        st.session_state["resume_rewrite_err"] = err
        st.session_state["scroll_to_rewrite_result"] = True

    # Display AI Rewrite Results (with anchor for auto-scroll only when button was just clicked)
    err = st.session_state.get("resume_rewrite_err")
    md = st.session_state.get("resume_rewrite_md")
    scroll_rewrite = st.session_state.pop("scroll_to_rewrite_result", False)

    if err:
        st.markdown(
            '<div id="resume-rewrite-anchor"></div>',
            unsafe_allow_html=True,
        )
        st.error(f"AI suggestions failed: {err}")
        if scroll_rewrite:
            _scroll_to_element("resume-rewrite-anchor")
    elif md:
        st.markdown(
            '<div id="resume-rewrite-anchor"></div>',
            unsafe_allow_html=True,
        )
        import json
        data = json.loads(md)

        # SLEEK DASHBOARD: Gap Summary Grid
        st.markdown("### Gap Analysis Dashboard")
        
        gap_keys = list(data["gap_summary"].keys())
        gap_cols = st.columns(len(gap_keys))
        
        for i, key in enumerate(gap_keys):
            items = data["gap_summary"][key]
            items_html = "".join([f'<div class="gap-list-item">{x}</div>' for x in items])
            
            with gap_cols[i]:
                st.markdown(f"""
                <div class="gap-tile-card animate-in delay-{i+1}">
                    <div class="gap-tile-title">{key.replace("_", " ").title()}</div>
                    {items_html}
                </div>
                """, unsafe_allow_html=True)

        st.markdown(T.spacer(2), unsafe_allow_html=True)

        # Suggested Bullets (Copy-ready Glass Cards)
        st.markdown("### Suggested Bullets (Copy-ready)")
        for i, r in enumerate(data["roles"]):
            with st.container():
                st.markdown(f"""
                <div style="margin-bottom:1.5rem; border-bottom:1px solid var(--border); padding-bottom:10px;">
                    <span style="font-weight:600; color:white;">{r['role_title']}</span>
                    <span style="color:var(--text-muted); font-size:0.9rem;"> — {r['company']}</span>
                </div>
                """, unsafe_allow_html=True)

                bullets_text = "\n".join([f"• {b}" for b in r["suggested_bullets"]])
                st.code(bullets_text, language="markdown")

                if r.get("evidence_needed"):
                        with st.expander("What evidence to add"):
                            for e in r["evidence_needed"]:
                                st.write("• " + e)

        if scroll_rewrite:
            _scroll_to_element("resume-rewrite-anchor")

    # 5. Technical Match Table
    with st.expander("Detailed technical match table"):
        df = pd.DataFrame([{
            "Job skill": m.job_skill,
            "Best resume skill": m.best_resume_skill,
            "Similarity": round(m.similarity, 3),
            "Coverage": m.coverage_label
        } for m in matches])
        st.dataframe(df, use_container_width=True)


def main() -> None:
    _load_css()
    _intro_splash()
    _hero()
    st.markdown(T.divider(), unsafe_allow_html=True)
    col_left, col_right = st.columns([1.55, 1.45], gap="large")
    with col_left:
        _step_job()
    with col_right:
        resume_text = _step_resume()
    st.markdown(T.divider(), unsafe_allow_html=True)
    selected_job: JobPosting | None = st.session_state.get("selected_job")
    _step_analysis(selected_job, resume_text)


if __name__ == "__main__":
    main()