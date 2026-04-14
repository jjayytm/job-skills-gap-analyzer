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

import textwrap


def _dedent_html(block: str) -> str:
    """
    Normalize multiline HTML for ``st.markdown(..., unsafe_allow_html=True)``.

    Streamlit runs Markdown first: any line starting with 4+ spaces becomes a
    code block. ``dedent`` alone is not enough because nested HTML lines still
    often begin with 4 spaces. Strip leading whitespace from every line.
    """
    text = textwrap.dedent(block).strip()
    return "\n".join(line.lstrip() for line in text.splitlines())


# ---------------------------------------------------------------------------
# Fullscreen intro (injected into parent document via components.html)
# ---------------------------------------------------------------------------

def intro_splash_component_html() -> str:
    """
    Premium fullscreen intro splash.
    Injected into window.parent.document so it covers Streamlit once per session.

    Timeline:
      0ms    → overlay appears
      40ms   → letters stagger in (55ms apart), tagline fades up
      400ms  → scanline sweeps top→bottom (2.2s)
      680ms  → subtitle fades in
      850ms  → accent underline reveals
      3200ms → word blurs out + echo drifts
      3950ms → screen fades + scales down (cinematic)
      4600ms → DOM cleaned up
    """
    return r"""<script>
(function () {
  var w   = window.parent;
  var doc = w.document;
  if (!doc || doc.getElementById("skillsync-intro-overlay")) return;

  var prevOverflow = doc.body.style.overflow;
  doc.body.style.overflow = "hidden";

  /* ── CSS ─────────────────────────────────────────────────── */
  var css = doc.createElement("style");
  css.id  = "skillsync-intro-style";
  css.textContent = [
    /* Keyframes */
    "@keyframes ssAurora {",
    "  0%   { background-position: 78% 6%,  92% 38%, 14% 86%, 36% 52%, center; }",
    "  33%  { background-position: 72% 18%, 86% 46%, 18% 80%, 42% 60%, center; }",
    "  66%  { background-position: 82% 22%, 90% 34%, 10% 90%, 38% 46%, center; }",
    "  100% { background-position: 78% 6%,  92% 38%, 14% 86%, 36% 52%, center; }",
    "}",
    "@keyframes ssLetterIn {",
    "  0%   { opacity: 0; transform: translateY(0.55em); filter: blur(8px); }",
    "  65%  { opacity: 1; filter: blur(1px); }",
    "  100% { opacity: 1; transform: translateY(0);      filter: blur(0); }",
    "}",
    "@keyframes ssGemIn {",
    "  0%   { opacity: 0; transform: scale(0.3) rotate(-40deg); filter: blur(6px); }",
    "  70%  { opacity: 1; transform: scale(1.2) rotate(6deg);   filter: blur(0); }",
    "  100% { opacity: 1; transform: scale(1)   rotate(0deg);   filter: blur(0); }",
    "}",
    "@keyframes ssTagIn {",
    "  0%   { opacity: 0; transform: translateY(10px); letter-spacing: 0.16em; }",
    "  100% { opacity: 1; transform: translateY(0);    letter-spacing: 0.32em; }",
    "}",
    "@keyframes ssScan {",
    "  0%   { transform: translateY(-10px); opacity: 0; }",
    "  6%   { opacity: 1; }",
    "  94%  { opacity: 0.5; }",
    "  100% { transform: translateY(100vh);  opacity: 0; }",
    "}",
    "@keyframes ssLineReveal {",
    "  0%   { width: 0;    opacity: 0; }",
    "  100% { width: 56px; opacity: 1; }",
    "}",
    "@keyframes ssProgress {",
    "  0%   { width: 0%; }",
    "  100% { width: 100%; }",
    "}",
    "@keyframes ssWordOut {",
    "  0%   { opacity: 1; transform: translateX(0)    scaleX(1);     filter: blur(0); }",
    "  100% { opacity: 0; transform: translateX(-4%)  scaleX(0.985); filter: blur(14px); }",
    "}",
    "@keyframes ssEchoOut {",
    "  0%   { opacity: 0;    transform: translateX(0);  filter: blur(10px); }",
    "  28%  { opacity: 0.20; transform: translateX(2%); filter: blur(7px); }",
    "  100% { opacity: 0;    transform: translateX(5%); filter: blur(2px); }",
    "}",
    "@keyframes ssScreenFade {",
    "  0%   { opacity: 1; transform: scale(1); }",
    "  100% { opacity: 0; transform: scale(0.97); filter: blur(4px); }",
    "}",
    /* Overlay */
    "#skillsync-intro-overlay {",
    "  position: fixed; inset: 0; z-index: 99999;",
    "  display: flex; flex-direction: column; align-items: center; justify-content: center;",
    "  background-color: #060a0d;",
    "  background-image:",
    "    radial-gradient(ellipse 110% 55% at 50% -22%, rgba(62,207,142,0.10) 0%, transparent 55%),",
    "    radial-gradient(ellipse 85%  50% at 100% 108%, rgba(62,207,142,0.07) 0%, transparent 50%),",
    "    linear-gradient(170deg, #020406 0%, #060a0d 40%, #080e14 65%, #040810 100%);",
    "  box-shadow: inset 0 0 130px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.04), inset 0 0 0 1px rgba(62,207,142,0.10);",
    "  overflow: hidden;",
    "  font-family: 'DM Sans', system-ui, sans-serif;",
    "}",
    /* Aurora layer */
    "#skillsync-intro-overlay::before {",
    "  content: ''; position: absolute; inset: 0; z-index: 0; pointer-events: none;",
    "  background-image:",
    "    radial-gradient(ellipse 54% 46% at 80%  6%,  rgba(62,207,142,0.24) 0%, transparent 54%),",
    "    radial-gradient(ellipse 46% 38% at 94%  46%, rgba(96,212,176,0.13) 0%, transparent 50%),",
    "    radial-gradient(ellipse 58% 48% at 10%  90%, rgba(62,207,142,0.15) 0%, transparent 58%),",
    "    radial-gradient(ellipse 44% 38% at 36%  54%, rgba(96,212,176,0.08) 0%, transparent 52%),",
    "    radial-gradient(ellipse 96% 80% at 50%  50%, transparent 0%, rgba(0,0,0,0.52) 100%);",
    "  background-size: 200% 200%, 200% 200%, 200% 200%, 200% 200%, 100% 100%;",
    "  animation: ssAurora 20s ease-in-out infinite;",
    "}",
    /* Grain layer */
    "#skillsync-intro-overlay::after {",
    "  content: ''; position: absolute; inset: 0; z-index: 0; pointer-events: none;",
    "  opacity: 0.42; mix-blend-mode: overlay;",
    "  background-image:",
    "    repeating-linear-gradient(0deg,  transparent 0, transparent 1px, rgba(255,255,255,0.026) 1px, rgba(255,255,255,0.026) 2px),",
    "    repeating-linear-gradient(90deg, transparent 0, transparent 1px, rgba(255,255,255,0.026) 1px, rgba(255,255,255,0.026) 2px);",
    "  background-size: 2px 2px;",
    "}",
    /* Scanline */
    ".ss-scanline {",
    "  position: absolute; left: 0; top: 0; width: 100%; height: 1px; z-index: 3; pointer-events: none;",
    "  background: linear-gradient(90deg, transparent 0%, rgba(62,207,142,0.6) 25%, rgba(168,240,208,1) 50%, rgba(62,207,142,0.6) 75%, transparent 100%);",
    "  box-shadow: 0 0 20px 3px rgba(62,207,142,0.55), 0 0 50px rgba(62,207,142,0.20);",
    "  animation: ssScan 2.4s cubic-bezier(0.4,0,0.6,1) 0.38s forwards;",
    "}",
    /* Inner */
    ".ss-inner { position: relative; z-index: 1; text-align: center; }",
    /* Tagline */
    ".ss-tagline {",
    "  font-size: clamp(0.5rem, 1.3vw, 0.63rem); font-weight: 600;",
    "  letter-spacing: 0.32em; text-transform: uppercase; color: rgba(136,152,168,0.80);",
    "  margin-bottom: 1.5rem; opacity: 0;",
    "  animation: ssTagIn 0.85s cubic-bezier(0.22,1,0.36,1) 0.04s both;",
    "}",
    /* Mark wrapper */
    ".ss-mark-wrap { position: relative; display: inline-block; }",
    /* Word container */
    ".ss-word {",
    "  font-size: clamp(3.4rem,14vw,7.5rem); font-weight: 800; letter-spacing: 0.04em;",
    "  color: #e8edf2; line-height: 1;",
    "  display: inline-flex; align-items: center; justify-content: center;",
    "}",
    /* Individual letters */
    ".ss-letter { display: inline-block; opacity: 0; }",
    ".ss-word.ss-in .ss-letter { animation: ssLetterIn 0.72s cubic-bezier(0.22,1,0.36,1) both; }",
    /* Gem wrapper */
    ".ss-gem-wrap { display: inline-flex; align-items: center; justify-content: center; margin: 0 0.06em; opacity: 0; }",
    ".ss-word.ss-in .ss-gem-wrap { animation: ssGemIn 0.55s cubic-bezier(0.34,1.56,0.64,1) both; }",
    /* Gem shape */
    ".ss-gem {",
    "  display: inline-block; width: 0.6em; height: 0.6em;",
    "  background: linear-gradient(135deg, #3ecf8e 0%, #60d4b0 45%, #a8f0d8 100%);",
    "  clip-path: polygon(50% 0%, 100% 35%, 80% 100%, 20% 100%, 0% 35%);",
    "  filter: drop-shadow(0 0 8px rgba(62,207,142,0.9)) drop-shadow(0 0 20px rgba(62,207,142,0.4));",
    "}",
    /* Word exit */
    ".ss-word.ss-out { animation: ssWordOut 0.78s cubic-bezier(0.4,0,0.8,0.6) forwards; }",
    /* Echo */
    ".ss-echo {",
    "  position: absolute; inset: 0;",
    "  font-size: inherit; font-weight: 800; letter-spacing: 0.04em;",
    "  color: #e8edf2; line-height: 1; opacity: 0; pointer-events: none; filter: blur(10px);",
    "  display: flex; align-items: center; justify-content: center;",
    "}",
    ".ss-echo.ss-out { animation: ssEchoOut 0.78s cubic-bezier(0.4,0,0.8,0.6) forwards; }",
    /* Accent underline */
    ".ss-accent-line {",
    "  height: 2px; margin: 1rem auto 0; border-radius: 999px; opacity: 0;",
    "  background: linear-gradient(90deg, transparent, #3ecf8e 30%, #a8f0d8 60%, transparent);",
    "  box-shadow: 0 0 12px rgba(62,207,142,0.7), 0 0 4px rgba(168,240,208,0.9);",
    "  animation: ssLineReveal 0.7s cubic-bezier(0.22,1,0.36,1) 0.9s both;",
    "}",
    /* Subtitle */
    ".ss-sub {",
    "  font-size: clamp(0.58rem, 1.4vw, 0.72rem); font-weight: 500;",
    "  letter-spacing: 0.2em; text-transform: uppercase;",
    "  color: rgba(62,207,142,0.50); margin-top: 1.1rem; opacity: 0;",
    "  transition: opacity 0.9s ease;",
    "}",
    /* Bottom-left version */
    ".ss-version {",
    "  position: absolute; bottom: 1.8rem; left: 2.4rem;",
    "  font-family: 'DM Mono', 'Courier New', monospace;",
    "  font-size: 0.58rem; color: rgba(92,107,122,0.50); letter-spacing: 0.14em; text-transform: uppercase;",
    "}",
    /* Bottom-right counter */
    ".ss-counter {",
    "  position: absolute; bottom: 1.8rem; right: 2.4rem;",
    "  font-family: 'DM Mono', 'Courier New', monospace;",
    "  font-size: 0.68rem; color: rgba(62,207,142,0.40); letter-spacing: 0.08em;",
    "}",
    /* Progress track */
    ".ss-progress-track { position: absolute; bottom: 0; left: 0; width: 100%; height: 2px; background: rgba(62,207,142,0.06); }",
    /* Progress fill */
    ".ss-progress-fill {",
    "  height: 100%;",
    "  background: linear-gradient(90deg, rgba(62,207,142,0.25) 0%, #3ecf8e 55%, #a8f0d8 100%);",
    "  box-shadow: 0 0 16px rgba(62,207,142,0.75), 0 0 5px rgba(168,240,208,0.95);",
    "  width: 0%; animation: ssProgress 2.9s cubic-bezier(0.2,0,0.85,1) 0.1s forwards;",
    "}",
    /* Screen exit */
    "#skillsync-intro-overlay.ss-fade { animation: ssScreenFade 0.65s cubic-bezier(0.4,0,0.2,1) forwards; pointer-events: none; }",
  ].join("");

  doc.head.appendChild(css);

  /* ── Build staggered letter HTML ──────────────────────────── */
  var skillChars = ["S","K","I","L","L"];
  var syncChars  = ["S","Y","N","C"];
  var wordInner  = "";
  var d = 0;
  for (var i = 0; i < skillChars.length; i++) {
    wordInner += '<span class="ss-letter" style="animation-delay:' + d + 'ms">' + skillChars[i] + "</span>";
    d += 55;
  }
  wordInner += '<span class="ss-gem-wrap" style="animation-delay:' + d + 'ms"><span class="ss-gem"></span></span>';
  d += 60;
  for (var j = 0; j < syncChars.length; j++) {
    wordInner += '<span class="ss-letter" style="animation-delay:' + d + 'ms">' + syncChars[j] + "</span>";
    d += 55;
  }

  /* ── DOM ──────────────────────────────────────────────────── */
  var el = doc.createElement("div");
  el.id  = "skillsync-intro-overlay";
  el.innerHTML =
    '<div class="ss-scanline"></div>' +
    '<div class="ss-inner">' +
      '<div class="ss-tagline" id="ssTag">Where your resume meets the job market</div>' +
      '<div class="ss-mark-wrap">' +
        '<div class="ss-word" id="ssWord">' + wordInner + '</div>' +
        '<div class="ss-echo"  id="ssEcho">SKILLSYNC</div>' +
      '</div>' +
      '<div class="ss-accent-line"></div>' +
      '<p class="ss-sub" id="ssSub">Know the gap \u00b7 Bridge it</p>' +
    '</div>' +
    '<div class="ss-version">NLP \u00b7 v1.0</div>' +
    '<div class="ss-counter" id="ssCnt">00</div>' +
    '<div class="ss-progress-track"><div class="ss-progress-fill"></div></div>';

  doc.body.appendChild(el);

  /* ── Refs ─────────────────────────────────────────────────── */
  var word = doc.getElementById("ssWord");
  var echo = doc.getElementById("ssEcho");
  var tag  = doc.getElementById("ssTag");
  var sub  = doc.getElementById("ssSub");
  var cnt  = doc.getElementById("ssCnt");

  /* ── Timeline ─────────────────────────────────────────────── */
  /* Stage 1 — letters stagger in */
  setTimeout(function () { if (word) word.classList.add("ss-in"); }, 40);

  /* Stage 1b — subtitle */
  setTimeout(function () { if (sub) sub.style.opacity = "1"; }, 680);

  /* Counter 00 → 100 over ~2.9s */
  setTimeout(function () {
    var n = 0;
    var t = setInterval(function () {
      n++;
      if (cnt) cnt.textContent = n < 10 ? "0" + n : "" + n;
      if (n >= 100) clearInterval(t);
    }, 29);
  }, 100);

  /* Stage 2 — exit word */
  setTimeout(function () {
    if (word) { word.classList.remove("ss-in"); word.classList.add("ss-out"); }
    if (echo) echo.classList.add("ss-out");
    if (sub)  { sub.style.transition  = "opacity 0.5s ease"; sub.style.opacity  = "0"; }
    if (tag)  { tag.style.transition  = "opacity 0.5s ease"; tag.style.opacity  = "0"; }
  }, 3200);

  /* Stage 3 — fade screen */
  setTimeout(function () { el.classList.add("ss-fade"); }, 3950);

  /* Stage 4 — cleanup */
  setTimeout(function () {
    el.remove();
    if (css.parentNode) css.remove();
    doc.body.style.overflow = prevOverflow || "";
  }, 4650);
})();
</script>"""


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def hero_left(strong_threshold: float, partial_threshold: float) -> str:
    """Left column: headline + sub-text with premium entrance."""
    return _dedent_html(f"""
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
    """)


def hero_right(strong_threshold: float, partial_threshold: float) -> str:
    """Right column: tech-stack info card with premium entrance."""
    return _dedent_html(f"""
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
    """)


# ---------------------------------------------------------------------------
# Step heading
# ---------------------------------------------------------------------------

def step_badge(number: str, label: str) -> str:
    """Coloured step indicator above each section heading."""
    return f'<p class="step-badge">Step {number} &nbsp; {label}</p>'


def section_heading(text: str) -> str:
    """Render a styled section heading for use inside step cards."""
    return (
        f"<h3 style='font-size:1.15rem; font-weight:600; "
        f"color:var(--text-primary); margin-bottom:1rem;'>{text}</h3>"
    )


# ---------------------------------------------------------------------------
# Active-job indicator
# ---------------------------------------------------------------------------

def job_active_strip(title: str, company: str) -> str:
    """Green confirmation strip shown after a job is selected."""
    return _dedent_html(f"""
    <div class="job-active-strip">
        <span class="tick">✓</span>
        <div>
            <span class="job-title">{title}</span>
            <span class="job-company">{company}</span>
        </div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Resume upload confirmation
# ---------------------------------------------------------------------------

def resume_strip(filename: str, char_count: int) -> str:
    """Green confirmation strip shown after resume is parsed."""
    return _dedent_html(f"""
    <div class="resume-strip">
        <span style="color:var(--accent);">✓</span>
        <span class="filename">{filename}</span>
        <span class="char-count">{char_count:,} chars</span>
    </div>
    """)


# ---------------------------------------------------------------------------
# Results dashboard
# ---------------------------------------------------------------------------

def results_header(job_title: str) -> str:
    """Render the results section heading and anchor div for the analysis dashboard."""
    return _dedent_html(f"""
    <div id="analysis-results-anchor" class="analysis-results-start">
    <div class="divider"></div>
    <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.2rem;">
        Results for
    </p>
    <h2 style="font-size:1.35rem; font-weight:600;
               color:var(--text-primary); margin-bottom:1.4rem;">
        {job_title}
    </h2>
    </div>
    """)


def stat_tile(title: str, count: int, pct: float, color: str) -> str:
    """Single KPI tile with animated entrance and internal progress bar."""
    return _dedent_html(f"""
    <div class="stat animate-in delay-3">
        <p class="label">{title}</p>
        <p class="stat-value" style="color:{color};">{count}</p>
        <p class="stat-pct">{pct:.1f}% of required skills</p>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%; background:{color};"></div>
        </div>
    </div>
    """)


def pill_group_header(heading: str) -> str:
    """Render an uppercase label above a group of skill pills."""
    return _dedent_html(f"""
    <p style="font-size:0.8rem; font-weight:600; color:var(--text-dim);
              margin-bottom:0.5rem; text-transform:uppercase;
              letter-spacing:0.08em;">
        {heading}
    </p>
    """)


def pill(job_skill: str, best_resume_skill: str | None, similarity: float, css_class: str) -> str:
    """Single skill pill with dot indicator and similarity metadata."""
    sim_pct = f"{similarity * 100:.0f}%"
    meta = f"{sim_pct} · {best_resume_skill}" if best_resume_skill else "no match"
    return _dedent_html(f"""
    <span class="pill {css_class}">
        <span class="pill-dot"></span>
        <span>{job_skill}</span>
        <span class="pill-meta">{meta}</span>
    </span>
    """)


def pills_wrap(pills_html: list[str]) -> str:
    """Wrap a list of pill HTML strings in a flex container div."""
    return f'<div class="pills-wrap">{"".join(pills_html)}</div>'


# ---------------------------------------------------------------------------
# Next steps & recommended skills (post-results)
# ---------------------------------------------------------------------------

def next_steps_card(steps: list[str]) -> str:
    """Actionable next steps for the user after viewing the gap report."""
    items = "".join(f"<li>{s}</li>" for s in steps)
    return _dedent_html(f"""
    <div class="next-steps-card">
        <p class="next-steps-label">What to do next</p>
        <ol class="next-steps-list">
            {items}
        </ol>
    </div>
    """)


def recommended_skills_section(
    strengthen_items: list[tuple[str, str]],
    add_items: list[tuple[str, str]],
) -> str:
    """
    Two-column block: skills to strengthen (partial) and skills to add (missing).
    Each item is (job_skill, short_hint).
    """
    def row(skill: str, hint: str, is_partial: bool) -> str:
        """Build a single recommendation row div with skill name and hint text."""
        cls = "rec-row rec-partial" if is_partial else "rec-row rec-missing"
        return (
            f'<div class="{cls}">'
            f'<div class="rec-skill">{skill}</div>'
            f'<p class="rec-hint">{hint}</p>'
            f"</div>"
        )

    strengthen_html = "".join(row(s, h, True) for s, h in strengthen_items)
    add_html = "".join(row(s, h, False) for s, h in add_items)

    return _dedent_html(f"""
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
    """)


# ---------------------------------------------------------------------------
# Misc layout helpers
# ---------------------------------------------------------------------------

def divider() -> str:
    """Render a horizontal divider line."""
    return '<div class="divider"></div>'


def spacer(rem: float = 1.5) -> str:
    """Render an empty div used as vertical whitespace between sections."""
    return f'<div style="height:{rem}rem;"></div>'
