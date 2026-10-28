<h1 align="center">Coursera Markdown Notes</h1>

<p align="center"><b>A Playwright-powered automation that turns Coursera lecture transcripts into clean, organized Markdown study notes.</b></p>

<p align="center"><i>Watch the lecture once. Keep the notes forever.</i></p>

<p align="center">
A small FastAPI service drives a logged-in Chromium browser through Coursera and reads lecture transcripts, either a whole module at a time or one lecture at a time. An n8n workflow calls that service, hands each transcript to a local Ollama model that writes the study notes, and uploads the Markdown files to Google Drive.
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
  <img src="docs/n8n-workflow.png" alt="The n8n workflow: Set Mode and a Switch route each run to the multiple modules branch or the single module branch" width="900" />
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
- **Under your control.** You choose the Ollama model, edit the prompt in the Markdown Notes Generator nodes, and can point the upload step somewhere else, such as a local folder, if you'd rather not use Drive.

Keep `auth.json` and `coursera_profile/` out of version control. They're already listed in `.gitignore`, because anyone holding `auth.json` can sign in as you.

## Two modes

| Mode | What it scrapes | Link to copy | Output |
| --- | --- | --- | --- |
| `multiple` | Every lecture in one module of a course | The **course page** | A new Drive folder with one note per lecture |
| `single` | One lecture (topic) | The **lecture video page** | One note in your notes folder |

Use `multiple` to take notes on a whole week of a course at once. Use `single` when you only need one topic, or to redo a single lecture's notes.

## Architecture

```
n8n: Manual trigger → Set Mode → Switch
   │
   ├── mode = "multiple"
   │     Configurations
   │       ├── Multiple Modules Scraper (POST /scrape_multiple/{module}) ──► FastAPI + Playwright
   │       │     → Transcription Compiler (Code)
   │       └── Google Drive: Create folder → Set Folder
   │     → Merge → Loop Over Items → Title and Transcription
   │     → Markdown Notes Generator (Ollama) → Convert to Text → Multiple Upload
   │
   └── mode = "single"
         Single Configuration
         → Single Module Scraper (POST /scraper_single) ──► FastAPI + Playwright
         → Markdown Notes Generator (Ollama) → Convert to File → Single Upload
```

The scraper opens Coursera in a headless Chromium that's logged in with your saved `auth.json`.

| Layer | Tech |
| --- | --- |
| Scraper | Python 3.12+, Playwright (Chromium) |
| API | FastAPI, served with Uvicorn |
| Workflow | n8n |
| Notes generator | Ollama chat model, running locally (`qwen3:8b` by default) |
| Storage | Google Drive |

## Features

- Two modes: a whole module in one run, or a single lecture
- Paste the Coursera link exactly as it appears in your browser, with no config files to edit
- Works with personal accounts and with organization or university accounts
- Reuses a saved Coursera login, so the scraper never types your password
- Notes are written by a local model, so transcripts never leave your machine before they reach Drive

## Project structure

```
coursera_scraper/
├── main.py                   # FastAPI app and the Playwright scrapers
├── login.py                  # One-time manual login that saves auth.json
├── automation_workflow.json  # n8n workflow export, ready to import
├── docs/                     # README images
├── auth.json                 # Saved Coursera session (git-ignored)
├── coursera_profile/         # Chrome profile used by login.py (git-ignored)
└── LICENSE
```

## Setup

You need Python 3.12 or newer, Google Chrome, n8n and Ollama.

1. Create a virtual environment and install the dependencies:

   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install fastapi uvicorn playwright
   playwright install chromium
   ```

2. **Log in to Coursera before you use the workflow.** The scraper can only open lectures with a saved login, so do this first:

   ```powershell
   python login.py
   ```

   A Chrome window opens. Sign in to your Coursera account (or your organization's login page), then go back to the terminal and press Enter. Your session is saved to `auth.json`. Run it again whenever Coursera logs you out or the scraper ends up on the login page.

3. Start the API from this folder, so it can find `auth.json`:

   ```powershell
   python -m uvicorn main:app --port 8000
   ```

   Leave off `--reload`. On Windows it switches the event loop and Playwright fails to launch the browser.

4. Open `http://localhost:8000/test`. You should see `"Successfull Test"`.

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

3. Pull a model. **You can use any model you like.** The workflow ships with `qwen3:8b`, but any chat model from the [Ollama library](https://ollama.com/library) works:

   ```powershell
   ollama pull qwen3:8b
   ```

   | Model | Size | Good for |
   | --- | --- | --- |
   | `qwen3:8b` | ~5 GB | Default. Well-structured notes, handles code identifiers well |
   | `gemma3:4b` | ~3 GB | Faster on most laptops |
   | `llama3.2:3b` | ~2 GB | Low-memory machines |
   | `llama3.1:8b` | ~5 GB | An alternative 8B model |

   Bigger models write better notes but need more RAM or VRAM and take longer per lecture.

4. Select your model in n8n. Open the **Ollama Chat Model** and **Ollama Chat Model1** nodes (one for each mode) and choose it from the **Model** dropdown, which lists every model you've pulled. Run `ollama list` to see them in the terminal.

   `qwen3` is a thinking model. Its reasoning would end up in your notes, so the workflow turns thinking off: the **Think** option is off in the Ollama node, and the single mode prompt ends with `/no_think`. Keep those if you switch to another qwen3 size.

## API

Both scrape routes take a JSON body with the full Coursera link:

```json
{ "link": "https://www.coursera.org/..." }
```

| Method | Route | Description |
| --- | --- | --- |
| POST | `/scrape_multiple/{module_num}` | Scrape every lecture in module `module_num` (counting from 1). `link` is the **course page** |
| POST | `/scraper_single` | Scrape one lecture. `link` is the **lecture video page** |
| GET | `/test` | Health check |

`/scrape_multiple` returns a list with one object per lecture, mapping its title to the transcript lines:

```json
[
  { "<lecture title>": ["<transcript line>", "<transcript line>", "..."] }
]
```

`/scraper_single` returns the lecture's whole transcript as one string.

## Importing the n8n workflow

The whole workflow is exported in `automation_workflow.json`.

1. In n8n, create a new workflow, open the **⋯** menu, choose **Import from File…** and pick `automation_workflow.json`. You can also paste the file's contents straight onto the canvas.
2. Connect your own credentials. They aren't included in the export, so each node below shows a warning until you set one:
   - **Ollama Chat Model** and **Ollama Chat Model1**: an Ollama credential pointing at your Ollama server (`http://localhost:11434`, or `http://host.docker.internal:11434` if n8n runs in Docker)
   - **Create folder**, **Multiple Upload** and **Single Upload**: a Google Drive OAuth2 credential
3. Choose your own Drive folder in **Create folder** (multiple mode makes its folders inside it) and in **Single Upload** (single mode notes go straight into it). The export still points at the author's "Generated Markdown Notes" folder, which you can't access.
4. In both Ollama nodes, pick the model you pulled. It's set to `qwen3:8b`, but any model works (see [Installing Ollama](#installing-ollama)).
5. Check the **Multiple Modules Scraper** and **Single Module Scraper** URLs. They're set to `http://host.docker.internal:8000/...` for n8n in Docker. If you run n8n with npm, change them to `http://localhost:8000/...`.

## Using the automation

Before every run, make sure you've logged in with `python login.py` at least once and the API is running with `python -m uvicorn main:app --port 8000`.

The workflow starts with a **manual trigger**, so nothing runs on a schedule.

### 1. Choose a mode in Set Mode

Open the **Set Mode** node and set `mode` to `multiple` or `single`. The **Switch** node reads it and sends the run down the matching branch, so you don't need to touch the other one.

| `mode` | Branch that runs | Node to fill in next |
| --- | --- | --- |
| `multiple` | Top branch | **Configurations** |
| `single` | Bottom branch | **Single Configuration** |

Type the value in lowercase. The Switch compares it exactly, so `Single` or `multi` won't match either branch.

### 2a. Multiple modules: copy the course page link

1. Open the course on Coursera and go to its main page, the one that lists the modules.
2. Copy the link from the address bar. It looks like:

   ```
   https://www.coursera.org/learn/<course-name>
   https://www.coursera.org/organizations/<your-organization>/learn/<course-name>
   ```

3. Fill in **Configurations**:

   | Field | Example | Meaning |
   | --- | --- | --- |
   | `link` | `https://www.coursera.org/learn/<course-name>` | The course page link |
   | `module_number` | `1` | Module to scrape, counting from 1 |
   | `title` | `Machine Learning` | Name of the Drive folder created for this run |

4. Click **Execute workflow**. It creates a folder named after `title` and uploads one `.md` note for every lecture in that module.

To take notes on several modules, run it once per module and change `module_number` each time. A module with many lectures can take a few minutes, so raise the scraper node's timeout if the request gets cut off.

### 2b. Single module: copy the lecture video page link

1. Open the lecture you want on Coursera, on the page where the video plays.
2. Copy the link from the address bar. It has `/lecture/` in it:

   ```
   https://www.coursera.org/learn/<course-name>/lecture/<id>/<lecture-name>
   ```

3. Fill in **Single Configuration**:

   | Field | Example | Meaning |
   | --- | --- | --- |
   | `module_link` | `https://www.coursera.org/learn/<course-name>/lecture/<id>/<lecture-name>` | The lecture video page link |
   | `title` | `Recap - Programming Fundamentals` | File name of the note (`.md` is added for you) |

4. Click **Execute workflow**. It uploads one note named `title.md` to the folder set in **Single Upload**.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `uvicorn` is not recognized | Activate the venv, or run `python -m uvicorn main:app` |
| `NotImplementedError` when the browser starts | Start Uvicorn without `--reload` |
| Nothing runs after Set Mode | `mode` must be exactly `multiple` or `single`, in lowercase |
| Requests hang for 30 seconds, then fail | Check you pasted the right kind of link for the mode. If it's right, Coursera changed its page layout and a selector in `main.py` no longer matches |
| Redirected to the login page | Run `python login.py` again to refresh `auth.json` |
| `IndexError` | The module number is higher than the number of modules in the course |
| The note starts with the model's reasoning | Turn off **Think** in the Ollama node, or keep `/no_think` at the end of the prompt |

## Disclaimer

This project is for **personal, educational use only**.

- **Follow Coursera's rules.** Coursera's [Terms of Use](https://www.coursera.org/about/terms) restrict automated access and scraping. You're responsible for making sure your use complies with them.
- **Use your own account.** Only scrape courses you're enrolled in, with your own login. Don't share `auth.json` or use someone else's account.
- **Don't redistribute course material.** Lecture transcripts and the notes generated from them are copyrighted by Coursera and its partner institutions. Keep them for your own study, and don't publish, share or sell them.
- **Not affiliated with Coursera.** This project isn't endorsed by, sponsored by or connected to Coursera, Inc.
- **Use at your own risk.** The software is provided as is, without warranty. The authors aren't responsible for account restrictions or any other consequences of using it.

## License

MIT. See [LICENSE](LICENSE).
