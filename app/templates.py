"""
app/templates.py
================
Pure-HTML snippet builders.

All visual markup lives here so that:
  - app.py contains zero raw HTML strings
  - styles.css contains zero inline style attributes
  - Each snippet function has a single, documented responsibility

Every function returns a plain str intended to be passed to
``st.markdown(..., unsafe_allow_html=True)``.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def hero_left(strong_threshold: float, partial_threshold: float) -> str:
    """Left column: headline + sub-text with premium entrance."""
    return f"""
    <div class="animate-in delay-1">
        <p class="label">SkillSync · AI-Driven Skills Gap Assessment</p>
        <h1 class="headline">
            Know exactly<br>where you <span>stand</span>.
        </h1>
        <p class="subtext" style="margin-top:0.75rem;">
            Paste any job description, upload your resume, and let semantic NLP
            surface the skills gap between where you are and where you need to be.
        </p>
    </div>
    """

def hero_right(strong_threshold: float, partial_threshold: float) -> str:
    """Right column: tech-stack info card with premium entrance."""
    return f"""
    <div class="card animate-in delay-2">
        <p class="label">Powered by</p>
        <p style="font-size:0.88rem; color:var(--text-primary);
                  margin:0.3rem 0 0.8rem; font-weight:500;">
            spaCy &nbsp;·&nbsp; Sentence-Transformers &nbsp;·&nbsp; Streamlit
        </p>
        <p class="label" style="margin-top:0.6rem;">Similarity thresholds</p>
        <div style="display:flex; gap:1.2rem; margin-top:0.3rem;">
            <div>
                <span style="color:var(--accent); font-family:var(--font-mono);
                             font-size:0.82rem;">≥ {strong_threshold:.2f}</span>
                <span style="color:var(--text-muted); font-size:0.75rem;"> strong</span>
            </div>
            <div>
                <span style="color:var(--warn); font-family:var(--font-mono);
                             font-size:0.82rem;">≥ {partial_threshold:.2f}</span>
                <span style="color:var(--text-muted); font-size:0.75rem;"> partial</span>
            </div>
            <div>
                <span style="color:var(--danger); font-family:var(--font-mono);
                             font-size:0.82rem;">&lt; {partial_threshold:.2f}</span>
                <span style="color:var(--text-muted); font-size:0.75rem;"> missing</span>
            </div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Step heading
# ---------------------------------------------------------------------------

def step_badge(number: str, label: str) -> str:
    """Coloured step indicator above each section heading."""
    return f'<p class="step-badge">Step {number} &nbsp; {label}</p>'


def section_heading(text: str) -> str:
    return (
        f"<h3 style='font-size:1.15rem; font-weight:600; "
        f"color:var(--text-primary); margin-bottom:1rem;'>{text}</h3>"
    )


# ---------------------------------------------------------------------------
# Active-job indicator
# ---------------------------------------------------------------------------

def job_active_strip(title: str, company: str) -> str:
    """Green confirmation strip shown after a job is selected."""
    return f"""
    <div class="job-active-strip">
        <span class="tick">✓</span>
        <div>
            <span class="job-title">{title}</span>
            <span class="job-company">{company}</span>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Resume upload confirmation
# ---------------------------------------------------------------------------

def resume_strip(filename: str, char_count: int) -> str:
    """Green confirmation strip shown after resume is parsed."""
    return f"""
    <div class="resume-strip">
        <span style="color:var(--accent);">✓</span>
        <span class="filename">{filename}</span>
        <span class="char-count">{char_count:,} chars</span>
    </div>
    """


# ---------------------------------------------------------------------------
# Results dashboard
# ---------------------------------------------------------------------------

def results_header(job_title: str) -> str:
    return f"""
    <div class="divider"></div>
    <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.2rem;">
        Results for
    </p>
    <h2 style="font-size:1.35rem; font-weight:600;
               color:var(--text-primary); margin-bottom:1.4rem;">
        {job_title}
    </h2>
    """


def stat_tile(title: str, count: int, pct: float, color: str) -> str:
    """Single KPI tile with animated entrance and internal progress bar."""
    return f"""
    <div class="stat animate-in delay-3">
        <p class="label">{title}</p>
        <p class="stat-value" style="color:{color};">{count}</p>
        <p class="stat-pct">{pct:.1f}% of required skills</p>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%; background:{color};"></div>
        </div>
    </div>
    """


def pill_group_header(heading: str) -> str:
    return f"""
    <p style="font-size:0.8rem; font-weight:600; color:var(--text-dim);
              margin-bottom:0.5rem; text-transform:uppercase;
              letter-spacing:0.08em;">
        {heading}
    </p>
    """


def pill(job_skill: str, best_resume_skill: str | None, similarity: float, css_class: str) -> str:
    """Single skill pill with dot indicator and similarity metadata."""
    sim_pct = f"{similarity * 100:.0f}%"
    meta = f"{sim_pct} · {best_resume_skill}" if best_resume_skill else "no match"
    return f"""
    <span class="pill {css_class}">
        <span class="pill-dot"></span>
        <span>{job_skill}</span>
        <span class="pill-meta">{meta}</span>
    </span>
    """


def pills_wrap(pills_html: list[str]) -> str:
    return f'<div class="pills-wrap">{"".join(pills_html)}</div>'


# ---------------------------------------------------------------------------
# Next steps & recommended skills (post-results)
# ---------------------------------------------------------------------------

def next_steps_card(steps: list[str]) -> str:
    """Actionable next steps for the user after viewing the gap report."""
    items = "".join(f"<li>{s}</li>" for s in steps)
    return f"""
    <div class="next-steps-card">
        <p class="next-steps-label">What to do next</p>
        <ol class="next-steps-list">
            {items}
        </ol>
    </div>
    """


def recommended_skills_section(
    strengthen_items: list[tuple[str, str]],
    add_items: list[tuple[str, str]],
) -> str:
    """
    Two-column block: skills to strengthen (partial) and skills to add (missing).
    Each item is (job_skill, short_hint).
    """
    def row(skill: str, hint: str, is_partial: bool) -> str:
        # These classes must match the updated styles.css exactly
        cls = "rec-row rec-partial" if is_partial else "rec-row rec-missing"
        return f'<div class="{cls}"><span class="rec-skill">{skill}</span><span class="rec-hint">{hint}</span></div>'
    
    strengthen_html = "".join(row(s, h, True) for s, h in strengthen_items)
    add_html = "".join(row(s, h, False) for s, h in add_items)
    
    return f"""
    <div id="top-skills-anchor" class="recommended-skills-block">
        <p class="recommended-skills-label">Top skills to add or strengthen on your resume</p>
        <div class="recommended-skills-grid">
            <div class="rec-column">
                <p class="rec-column-title">Strengthen these</p>
                <p class="rec-column-sub">You're close — add a bullet or keyword so they match strongly.</p>
                <div class="rec-rows">{strengthen_html or '<p class="rec-empty">None</p>'}</div>
            </div>
            <div class="rec-column">
                <p class="rec-column-title">Consider adding</p>
                <p class="rec-column-sub">High impact for this role. Add only where you have real experience.</p>
                <div class="rec-rows">{add_html or '<p class="rec-empty">None</p>'}</div>
            </div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Misc layout helpers
# ---------------------------------------------------------------------------

def divider() -> str:
    return '<div class="divider"></div>'


def spacer(rem: float = 1.5) -> str:
    return f'<div style="height:{rem}rem;"></div>'
