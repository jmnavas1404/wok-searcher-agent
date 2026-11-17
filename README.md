# 🤖 LUH Job Search Agent

An automated weekly job-search agent for students at **Leibniz Universität Hannover (LUH)**. It scrapes multiple job portals, filters relevant postings using the **Gemini AI** API, generates a styled HTML report with English draft application messages, and sends it directly to your Gmail inbox.

---

## ✨ Features

- Scrapes job listings from:
  - **LUH Jobbörse** (general university job board)
  - **LUH Institutes** (IMES, IRT, IFW, IDS, IAL and more)
  - **Stellenwerk Hannover** (student job portal)
  - **German Federal Employment Agency**
  - **Stud.IP Schwarzes Brett** (requires LUH credentials — SSO via Shibboleth)
- Filters positions relevant to mechanical engineering, mechatronics, robotics, CAD, simulation, and IT support
- Uses Gemini to generate polished English application drafts for each matching position
- Colour-codes results by LUH institute
- Sends a beautiful HTML report to your Gmail via the Gmail API
- Runs automatically every Friday at 10:00 UTC via GitHub Actions

---

## 🛠 Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Tested on 3.10 and 3.12 |
| Gemini API key | [Get one at Google AI Studio](https://aistudio.google.com/app/apikey) |
| Google Cloud project | For Gmail API OAuth2 credentials |
| LUH account | Optional — only needed for Schwarzes Brett |

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/searching-work-agent.git
cd searching-work-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
# venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and set:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key from Google AI Studio |
| `REPORT_RECIPIENT_EMAIL` | The Gmail address that will receive the weekly report |
| `LUH_USERNAME` | Your LUH username (optional, for Schwarzes Brett) |
| `LUH_PASSWORD` | Your LUH password (optional, for Schwarzes Brett) |
| `RAPID_API_KEY` | RapidAPI key (optional, for LinkedIn jobs) |

> [!CAUTION]
> Never commit your `.env` file. It is listed in `.gitignore`. Keep all secrets out of version control.

### 5. Set up Gmail API credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or reuse an existing one).
3. Enable the **Gmail API**.
4. Under **APIs & Services → Credentials**, create an **OAuth 2.0 Client ID** (Application type: *Desktop app*).
5. Download the JSON file and save it as `credentials.json` in the project root.

> [!NOTE]
> `credentials.json` and `token.json` are listed in `.gitignore` and must never be committed.

### 6. Authenticate with Gmail (first run only)

On the first run the agent will open a browser window asking you to authorise access to your Gmail account. After you approve, a `token.json` file is saved locally for future runs.

```bash
python agent.py --no-email   # test run — saves the HTML report to tests/ without sending email
```

### 7. Create your candidate profile

Create a file named `profile.md` in the project root with your own professional profile. The agent injects this text into every Gemini prompt to personalise the application drafts.

> [!IMPORTANT]
> `profile.md` is **not** tracked by git because it contains personal contact information. Each user must create their own copy.

```bash
cp profile.example.md profile.md   # if an example is provided, or create your own
```

The file should contain your name, education, work experience, skills, and languages in Markdown format. Example structure:

```markdown
# Professional Profile: Your Name
**Contact:** your@email.com | LinkedIn: linkedin.com/in/yourprofile

## Summary
...

## Education
...

## Work Experience
...

## Skills & Languages
...
```

---

## ▶️ Running the agent

### Manual run — send email

```bash
python agent.py
```

### Manual run — save HTML report locally (no email sent)

```bash
python agent.py --no-email
```

The report is saved to `tests/report_test_<timestamp>.html`.

---

## ⚙️ GitHub Actions — Automated weekly run

The workflow in [`.github/workflows/weekly_report.yml`](.github/workflows/weekly_report.yml) runs every Friday at 10:00 UTC.

You need to add the following **repository secrets** in GitHub (**Settings → Secrets and variables → Actions**):

| Secret name | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GMAIL_TOKEN` | The full contents of your local `token.json` |

> [!TIP]
> You can trigger the workflow manually at any time via **Actions → Weekly Job Scraper → Run workflow**.

---

## 📁 Project structure

```
searching-work-agent/
├── agent.py              # Main agent script
├── config.py             # Job sources, API config (reads from .env)
├── report.html           # Jinja2 HTML template for the email report
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template (safe to commit)
├── .github/
│   └── workflows/
│       └── weekly_report.yml   # GitHub Actions CI workflow
└── README.md
```

> [!NOTE]
> The following files are **not tracked** (`.gitignore`):
> - `.env` — your real environment variables
> - `credentials.json` — Google OAuth client secret
> - `token.json` — Gmail OAuth access token
> - `hoja_de_vida.md` — your personal candidate profile (English)
> - `venv/` — virtual environment
> - `tests/` — locally generated HTML reports

---

## 🔧 Customising job sources

Edit the `JOB_SOURCES` dictionary in `config.py` to add or remove job portals. Each key is a category label displayed in the HTML report; each value is a list of URLs to scrape.

---

## 📄 License

MIT
