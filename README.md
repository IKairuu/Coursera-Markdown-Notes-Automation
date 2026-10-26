<h1 align="center">Coursera Markdown Notes</h1>

<p align="center"><b>A Playwright-powered automation that turns Coursera lecture transcripts into clean, organized Markdown study notes.</b></p>

<p align="center"><i>Watch the lecture once. Keep the notes forever.</i></p>

<p align="center">
A small FastAPI service drives a logged-in Chromium browser through a Coursera course, opens every lecture in a module and reads its transcript. An n8n workflow calls that service, hands each transcript to a local Ollama model that writes the study notes, and uploads one Markdown file per lecture into a Google Drive folder.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Scraper-Playwright-2EAD33?logo=playwright&logoColor=white" alt="Scraper: Playwright" />
  <img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white" alt="API: FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/Workflow-n8n-EA4B71?logo=n8n&logoColor=white" alt="Workflow: n8n" />
  <img src="https://img.shields.io/badge/AI-Ollama-000000?logo=ollama&logoColor=white" alt="AI: Ollama" />
  <img src="https://img.shields.io/badge/Storage-Google%20Drive-4285F4?logo=googledrive&logoColor=white" alt="Storage: Google Drive" />
  <img src="https://img.shields.io/badge/Runs-Locally-6E40C9" alt="Runs locally" />
  <img src="https://img.shields.io/badge/License-MIT-555555" alt="License: MIT" />
</p>

## Preview

<p align="center">
  <img src="docs/n8n-workflow.png" alt="The n8n workflow, from the manual trigger to the Google Drive upload" width="900" />
</p>

## Runs locally

Everything except the final upload runs on your own computer. There's no hosted server, no paid AI API and no third-party account besides Coursera and Google Drive.

| Part | Where it runs |
| --- | --- |
| Scraper API (FastAPI + Playwright) | Your machine, on `localhost:8000` |
| Browser session | A headless Chromium on your machine, using the login saved in `auth.json` |
| Workflow | Your own n8n instance, installed with npm or Docker |
| Notes generator | Ollama, running a model on your own CPU or GPU |
| Storage | Google Drive, the only step that leaves your machine |

What this means:

- **Private.** Your Coursera session cookies and lecture transcripts stay on your computer. The model writes notes offline, and only the finished Markdown files are uploaded.
- **Free to run.** There are no per-request API costs, so you can generate notes for a whole course as often as you like.
- **Under your control.** You choose the Ollama model, edit the prompt in the Markdown Notes Generator node, and can point the upload step somewhere else, such as a local folder, if you'd rather not use Drive.

Keep `auth.json`, `coursera_profile/` and `.env` out of version control. They're already listed in `.gitignore`, because anyone holding `auth.json` can sign in as you.

## Architecture

```
n8n (Manual trigger → Configurations)
   │
   ├── Scraper (HTTP GET) ──► FastAPI + Playwright (this folder)
   │        │                     └── Chromium, logged in with auth.json
   │        ▼
   │   Transcription Compiler (Code)
   │
   └── Google Drive: Create folder → Set Folder
   │
   ▼
Merge → Loop Over Items → Title and Transcription
   → Markdown Notes Generator (Ollama chat model)
   → Convert to Text → Upload file to Google Drive
```

| Layer | Tech |
| --- | --- |
| Scraper | Python 3.12+, Playwright (Chromium) |
| API | FastAPI, served with Uvicorn |
| Workflow | n8n |
| Notes generator | Ollama chat model, running locally |
| Storage | Google Drive |

## Features

- Scrapes every lecture transcript in a chosen module with one request
- Reuses a saved Coursera login, so the scraper never types your password
- Works with personal accounts and with organization or university accounts through `COURSERA_LINK`
- Returns transcripts grouped by lecture title, ready for n8n to loop over
- Notes are written by a local model, so transcripts never leave your machine before they reach Drive

## Project structure

```
coursera_scraper/
├── main.py           # FastAPI app and the Playwright scraper
├── login.py          # One-time manual login that saves auth.json
├── automation_workflow.json  # n8n workflow export, ready to import
├── docs/             # README images
├── .env.example      # Template for COURSERA_LINK
├── .env              # Your settings (git-ignored)
├── auth.json         # Saved Coursera session (git-ignored)
├── coursera_profile/ # Chrome profile used by login.py (git-ignored)
└── LICENSE
```

## Setup

You need Python 3.12 or newer, Google Chrome, n8n and Ollama.

1. Create a virtual environment and install the dependencies:

   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install fastapi uvicorn playwright python-dotenv
   playwright install chromium
   ```

2. Copy `.env.example` to `.env` and set `COURSERA_LINK`:

   ```env
   # Personal account
   COURSERA_LINK=https://www.coursera.org

   # Organization or university account
   COURSERA_LINK=https://www.coursera.org/organizations/your-organization-slug
   ```

3. **Log in to Coursera before you use the workflow.** The scraper can only open lectures with a saved login, so do this first:

   ```powershell
   python login.py
   ```

   A Chrome window opens. Sign in to your Coursera account (or your organization's login page), then go back to the terminal and press Enter. Your session is saved to `auth.json`. Run it again whenever Coursera logs you out or the scraper ends up on the login page.

4. Start the API from this folder, so it can find `auth.json` and `.env`:

   ```powershell
   python -m uvicorn main:app --port 8000
   ```

   Leave off `--reload`. On Windows it switches the event loop and Playwright fails to launch the browser.

5. Open `http://localhost:8000/test`. You should see `"Successfull Test"`.

## Installing Ollama

Ollama runs the AI model that writes the notes, right on your computer.

1. Download and install Ollama from [ollama.com/download](https://ollama.com/download). It's available for Windows, macOS and Linux. On Linux you can run:

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Check that it's running. Ollama starts in the background after you install it:

   ```powershell
   ollama --version
   ```

   The server listens on `http://localhost:11434`. If it isn't running, start it with `ollama serve`.

3. Pull a model. **You can use any model you like.** The workflow ships with `gemma3:4b`, but any chat model from the [Ollama library](https://ollama.com/library) works:

   ```powershell
   ollama pull gemma3:4b
   ```

   | Model | Size | Good for |
   | --- | --- | --- |
   | `gemma3:4b` | ~3 GB | Default. Fast on most laptops |
   | `llama3.2:3b` | ~2 GB | Low-memory machines |
   | `qwen2.5:7b` | ~5 GB | Longer, more detailed notes |
   | `llama3.1:8b` | ~5 GB | Better structure on technical lectures |

   Bigger models write better notes but need more RAM or VRAM and take longer per lecture.

4. Select your model in n8n. Open the **Ollama Chat Model** node and choose it from the **Model** dropdown, which lists every model you've pulled. Run `ollama list` to see them in the terminal.

## API

| Method | Route | Description |
| --- | --- | --- |
| GET | `/scrape/{module_num}/{coursera_link}` | Scrape every lecture transcript in module `module_num` (counting from 1) of the course at `COURSERA_LINK/{coursera_link}` |
| GET | `/test` | Health check |
| GET | `/test/{module}/{coursera_path}` | Echoes the parameters back, to check what n8n is sending |

`coursera_link` is the course path after `COURSERA_LINK`, for example `learn/ai-machine-learning-apply-build-solve`.

The response is a list with one object per lecture, mapping its title to the transcript lines:

```json
[
  { "<lecture title>": ["<transcript line>", "<transcript line>", "..."] }
]
```

## Importing the n8n workflow

The whole workflow is exported in `automation_workflow.json`.

1. In n8n, create a new workflow, open the **⋯** menu, choose **Import from File…** and pick `automation_workflow.json`. You can also paste the file's contents straight onto the canvas.
2. Connect your own credentials. They aren't included in the export, so each node below shows a warning until you set one:
   - **Ollama Chat Model**: an Ollama credential pointing at your Ollama server (`http://localhost:11434`, or `http://host.docker.internal:11434` if n8n runs in Docker)
   - **Create folder** and **Upload file**: a Google Drive OAuth2 credential
3. In **Create folder**, choose the Drive folder the notes should go into. The export still points at the author's "Generated Markdown Notes" folder, which you can't access.
4. In **Ollama Chat Model**, pick the model you pulled. It's set to `gemma3:4b`, but any model works (see [Installing Ollama](#installing-ollama)).

5. Check the **Scraper** URL. It's set to `http://host.docker.internal:8000/...` for n8n in Docker. If you run n8n with npm, change it to `http://localhost:8000/...`.

### Running it

Before every run, make sure you've logged in with `python login.py` at least once and the API is running with `python -m uvicorn main:app --port 8000`.

The workflow starts with a **manual trigger**, so nothing runs on a schedule. Set the course in the **Configurations** node, then click **Execute workflow**:

| Field | Example | Meaning |
| --- | --- | --- |
| `link` | `learn/ai-machine-learning-apply-build-solve` | Course path after `COURSERA_LINK` |
| `module_number` | `1` | Module to scrape, counting from 1 |
| `title` | `Machine Learning` | Name of the Drive folder created for this run |

Each run creates a folder named after `title` and uploads one `.md` note for every lecture in that module. A module with many lectures can take a few minutes, so raise the Scraper node's timeout if the request gets cut off.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `uvicorn` is not recognized | Activate the venv, or run `python -m uvicorn main:app` |
| `NotImplementedError` when the browser starts | Start Uvicorn without `--reload` |
| Requests hang for 30 seconds, then fail | Coursera changed its page layout and a selector in `main.py` no longer matches |
| Redirected to the login page | Run `python login.py` again to refresh `auth.json` |
| `IndexError` | The module number is higher than the number of modules in the course |

## Disclaimer

This project is for **personal, educational use only**.

- **Follow Coursera's rules.** Coursera's [Terms of Use](https://www.coursera.org/about/terms) restrict automated access and scraping. You're responsible for making sure your use complies with them.
- **Use your own account.** Only scrape courses you're enrolled in, with your own login. Don't share `auth.json` or use someone else's account.
- **Don't redistribute course material.** Lecture transcripts and the notes generated from them are copyrighted by Coursera and its partner institutions. Keep them for your own study, and don't publish, share or sell them.
- **Not affiliated with Coursera.** This project isn't endorsed by, sponsored by or connected to Coursera, Inc.
- **Use at your own risk.** The software is provided as is, without warranty. The authors aren't responsible for account restrictions or any other consequences of using it.

## License

MIT. See [LICENSE](LICENSE).
