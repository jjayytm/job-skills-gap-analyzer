# Job Posting Skills Gap Analyzer

An **NLP capstone project** that compares a job description to your resume and shows where you stand: which skills are covered, partially covered, or missing. It uses semantic similarity (sentence-transformers) and optional AI (OpenAI) for actionable recommendations and resume rewrite suggestions.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Features

- **Paste any job description** — no scraping; you paste the full posting and optional job title/company.
- **Resume upload** — PDF, DOCX, or TXT; text is extracted and used for skill matching.
- **Semantic skills gap** — skills are extracted (spaCy + curated list), then matched using **sentence-transformers** and cosine similarity. Each job skill is labeled:
  - **Strong match** — well covered on your resume
  - **Partial match** — related but could be strengthened
  - **Missing** — not clearly present
- **Adjustable thresholds** — in the UI (Advanced section) you can tune the strong/partial similarity thresholds before running analysis.
- **AI recommendations** — “Top skills to add or strengthen” with short, actionable hints (OpenAI).
- **AI resume rewrite suggestions** — copy-ready bullets and gap summary aligned to the role (OpenAI); never invents facts.
- **Dark, modern UI** — glassmorphism, skeleton loading, and smooth auto-scroll to results.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| NLP / parsing | spaCy (`en_core_web_sm`) |
| Semantic similarity | sentence-transformers (`all-MiniLM-L6-v2`) |
| AI suggestions | OpenAI API (gpt-4o-mini or configurable) |
| Resume parsing | PyPDF2, python-docx |
| Config | python-dotenv, `app/config.py` |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/jjayytm/job-skills-gap-analyzer.git
cd job-skills-gap-analyzer
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy model

```bash
python -m spacy download en_core_web_sm
```

### 5. Environment variables (for AI features)

Copy the example env file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Without `OPENAI_API_KEY`, the app still runs; skill matching and stats work, but “Top skills to add or strengthen” and “AI resume rewrite suggestions” will show an error until the key is set.

---

## Run the app

From the project root:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

---

## How to use

1. **Step 01 — Job description**  
   Paste the full job posting (and optionally job title + company). Click **Use this description**. You’ll see a single confirmation strip for the selected role.

2. **Step 02 — Resume**  
   Upload your resume (PDF, DOCX, or TXT). The app extracts text for analysis.

3. **Step 03 — Analyse**  
   (Optional) Open **Advanced: adjust similarity thresholds** and change the strong/partial thresholds if you want.  
   Click **Analyse skills gap**. The page auto-scrolls to the results (job title, stats, covered/partial/missing skills). After AI recommendations load, it scrolls to “Top skills to add or strengthen.”

4. **Resume rewrite (optional)**  
   Scroll to **AI resume rewrite suggestions**, click **Generate resume rewrite suggestions**, and wait for the skeleton loader. When done, you’ll see a gap summary and copy-ready bullets; the view auto-scrolls to the result.

---

## Project structure

```
job-skills-gap-analyzer/
├── app.py                 # Entry point: streamlit run app.py
├── app/
│   ├── __init__.py
│   ├── config.py          # CONFIG (NLP thresholds, models, etc.)
│   ├── streamlit_ui.py    # Streamlit layout, steps, and widgets
│   ├── templates.py       # HTML snippets (hero, cards, pills)
│   ├── nlp.py             # Skill extraction, matching, summarize_gap
│   ├── llm.py             # OpenAI: skill recommendations + resume rewrite
│   ├── resume_parser.py  # PDF/DOCX/TXT text extraction
│   └── models.py         # JobPosting dataclass
├── static/
│   └── styles.css        # Dark theme, glass cards, skeleton animations
├── requirements.txt
├── .env.example
├── NLP_OVERVIEW.md        # Detailed NLP pipeline description
└── README.md
```

---

## Configuration

- **Similarity thresholds** — Defaults are in `app/config.py` (`similarity_threshold_strong`, `similarity_threshold_partial`). Users can override them in the app via **Advanced: adjust similarity thresholds** before each analysis.
- **OpenAI** — API key from `.env` or Streamlit secrets. Model and limits are set in `app/llm.py`.

---

## Deployment (e.g. Streamlit Community Cloud)

1. Push the repo to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io), create a new app and point it to this repo.
3. Set **Main file path** to `app.py`.
4. Add **Secrets** → `OPENAI_API_KEY` = your key.
5. Deploy. No need to install spaCy model manually; add `en_core_web_sm` to `requirements.txt` or a `packages.txt` if your host requires it.

---

## Acknowledgments

- **spaCy** — NLP and dependency parsing  
- **sentence-transformers** — Semantic embeddings  
- **Streamlit** — Web UI  
- **OpenAI** — Skill and resume suggestion APIs  

Built as an NLP capstone / career-readiness project.
