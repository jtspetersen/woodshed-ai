# Woodshed AI

A locally-hosted, AI-powered songwriting companion — named for the musician's tradition of *woodshedding*, the practice of retreating to work intensely on your craft.

Feed it raw ideas — audio recordings, MIDI files, text descriptions — and it responds with music-theory-grounded suggestions for chords, melodies, arrangements, and song structure. It explains *why* its suggestions work, generates playable MIDI files, renders notation and guitar tabs, and exports to your DAW.

Runs entirely on your machine. No cloud APIs, no data leaving your computer.

## Features

**Conversational Music Theory**
- Ask about chords, progressions, scales, modes, and songwriting concepts
- Get Roman numeral analysis, chord-quality breakdowns, and key detection
- Describe a mood or style and receive matching scale/chord suggestions
- Every suggestion includes the theory reasoning behind it

**Audio & MIDI Analysis**
- Upload MIDI files for automatic analysis (key, tempo, chords, structure)
- Upload audio files (.wav, .mp3, .m4a) for transcription to MIDI via Basic Pitch
- Analysis feeds directly into the conversation as context

**Playable Output**
- Generate MIDI files from suggested chord progressions and scales
- In-browser MIDI playback with piano-roll visualizer
- Render ABC sheet music notation inline (via abcjs)
- Display ASCII guitar tablature with chord diagrams
- Export to MusicXML for DAW import (GarageBand, Logic, Ableton, Reaper, FL Studio)

**Knowledge-Augmented**
- RAG pipeline backed by ChromaDB with curated music theory reference docs
- Covers chord substitution, genre conventions, scales/modes, song structure, arrangement, melody writing, and more

## Quickstart

### Prerequisites

- **Python 3.13** (3.11+ should work; avoid 3.14 due to dependency issues)
- **Node.js 18+** (for the frontend)
- **Ollama** installed and running ([ollama.com](https://ollama.com))

### 1. Clone and set up the backend

```bash
git clone https://github.com/jtspetersen/woodshed-ai.git
cd woodshed-ai
python -m venv venv
source venv/bin/activate        # Linux/macOS
source venv/Scripts/activate    # Windows (Git Bash / MSYS)
pip install -r requirements.txt
```

### 2. Set up the frontend

```bash
cd frontend
npm install
cd ..
```

### 3. Pull Ollama models

```bash
ollama pull qwen2.5:32b         # Primary LLM (or any model you prefer)
ollama pull nomic-embed-text    # Embedding model for the knowledge base
```

### 4. Configure (optional)

Create a `.env` file in the project root to override defaults:

```env
LLM_MODEL=qwen2.5:32b
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_HOST=http://localhost:11434
TEMPERATURE=0.7
```

See [config.py](config.py) for all available settings.

### 5. Build the knowledge base

```bash
python -c "from app.knowledge.ingest import ingest_starter_data; ingest_starter_data()"
```

This indexes the curated reference docs in `data/starter/` into ChromaDB. The vector store is saved to `data/chromadb/` (gitignored, rebuilt locally).

### 6. Run

**Option A — All services at once** (recommended for development):
```bash
python dev.py              # Start all services (backend, frontend, transcription)
python dev.py status       # Show which services are running
python dev.py stop         # Stop all running services (works from any terminal)
```
This starts the FastAPI backend (:8000), Next.js frontend (:3001), and transcription service (:8765) with color-coded output. Press Ctrl+C to stop, or run `python dev.py stop` from another terminal.

**Option B — Separately:**
```bash
# Terminal 1: Backend API
python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

### Audio transcription (optional)

To enable audio-to-MIDI transcription, set up the Basic Pitch microservice:

```bash
cd services/basic-pitch
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install basic-pitch flask
```

The service starts automatically when you run `python main.py` or `python dev.py` (if the venv exists).

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Next.js/React  │────▶│  FastAPI Backend  │────▶│   Ollama    │
│  :3001          │ API │  :8000            │     │   :11434    │
└─────────────────┘     └──────────────────┘     └─────────────┘
                              │
                        ┌─────┴──────┐
                        │            │
                   ┌────▼───┐  ┌────▼────────┐
                   │ChromaDB│  │Basic Pitch  │
                   │(embed) │  │:8765        │
                   └────────┘  └─────────────┘
```

**Frontend** (Next.js 14 + React + Tailwind) handles the UI: chat interface with SSE streaming, file upload, MIDI playback, sheet music rendering, and guitar tab display.

**Backend** (FastAPI) wraps the Python domain code as a thin HTTP/SSE layer. The domain modules (`app/llm/`, `app/theory/`, `app/audio/`, `app/output/`, `app/knowledge/`) are unchanged from earlier phases.

## Project Structure

```
woodshed-ai/
├── main.py                     # Backend entry point (FastAPI + transcription)
├── dev.py                      # Unified dev launcher (all services)
├── config.py                   # Central configuration
├── requirements.txt            # Python dependencies
├── pyproject.toml              # pytest config + coverage thresholds
├── app/
│   ├── api/                    # FastAPI routes, sessions, schemas
│   │   ├── main.py             # App factory with CORS + lifespan
│   │   ├── routes/             # chat, files, status endpoints
│   │   ├── sessions.py         # In-memory session store
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── deps.py             # Dependency injection
│   ├── audio/                  # MIDI analysis + audio transcription
│   ├── knowledge/              # ChromaDB vector store + RAG ingestion
│   ├── llm/                    # Ollama client, conversation pipeline, prompts
│   ├── output/                 # MIDI generation, notation, guitar tab, export
│   └── theory/                 # music21 theory engine + tool schemas
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js app router (layout, page, globals)
│   │   ├── components/         # React components (chat, music, UI)
│   │   ├── hooks/              # useChat, useStatus
│   │   └── lib/                # API client, types, markdown, session
│   ├── e2e/                    # Playwright E2E tests
│   ├── jest.config.ts          # Jest config + coverage thresholds
│   └── playwright.config.ts    # Playwright config
├── services/
│   └── basic-pitch/            # Audio-to-MIDI transcription microservice
├── data/
│   ├── starter/                # Curated reference docs (committed)
│   ├── local/                  # User files — MIDI, exports (gitignored)
│   └── chromadb/               # Vector store (gitignored, rebuilt locally)
├── tests/                      # Backend tests (pytest)
└── docs/                       # Design docs and project brief
```

## LLM Tool Use

The LLM has access to structured tools powered by music21:

| Tool | Description |
|------|-------------|
| `analyze_chord` | Break down a chord symbol (root, quality, notes, intervals) |
| `analyze_progression` | Roman numeral analysis of a chord sequence |
| `suggest_next_chord` | Suggest what chord comes next with theory rationale |
| `get_scale_for_mood` | Match scales to mood/style descriptions |
| `detect_key` | Identify the key from a set of notes or chords |
| `get_chord_voicings` | Guitar fingerings for a chord |
| `get_related_chords` | Substitutions and related chords |
| `generate_progression_midi` | Create a MIDI file from a chord progression |
| `generate_scale_midi` | Create a MIDI file playing a scale |
| `generate_guitar_tab` | ASCII chord diagrams for a progression |
| `generate_notation` | ABC notation for sheet music rendering |
| `export_for_daw` | MIDI + MusicXML export with DAW import instructions |

## Running Tests

```bash
# Backend unit tests (no Ollama required)
python -m pytest tests/ -m "not integration" -q

# Backend with coverage enforcement (≥90%)
python -m pytest tests/ -m "not integration" --cov=app/api --cov-report=term-missing

# Backend integration tests (requires live Ollama)
python -m pytest tests/ -m integration -q

# Frontend unit tests
cd frontend && npm test

# Frontend with coverage enforcement (≥80%)
cd frontend && npm test -- --coverage

# E2E tests (requires backend + frontend running)
cd frontend && npx playwright test
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM inference | [Ollama](https://ollama.com) (local) |
| Primary model | Qwen 2.5:32B (configurable) |
| Music theory | [music21](https://web.mit.edu/music21/) |
| Knowledge base | [ChromaDB](https://www.trychroma.com/) + nomic-embed-text |
| Audio-to-MIDI | [Basic Pitch](https://github.com/spotify/basic-pitch) (Spotify) |
| MIDI processing | mido, pretty_midi |
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + SSE streaming |
| Frontend | [Next.js](https://nextjs.org/) 14 + React + TypeScript |
| Styling | [Tailwind CSS](https://tailwindcss.com/) |
| MIDI playback | [html-midi-player](https://cifkao.github.io/html-midi-player/) |
| Notation rendering | [abcjs](https://www.abcjs.net/) (client-side) |
| Testing | pytest, Jest, Playwright |

## License

[GPL-3.0-or-later](LICENSE)
