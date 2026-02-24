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
- Render ABC sheet music notation in the chat (via abcjs)
- Display ASCII guitar tablature with chord diagrams
- Export to MusicXML for DAW import (GarageBand, Logic, Ableton, Reaper, FL Studio)

**Knowledge-Augmented**
- RAG pipeline backed by ChromaDB with curated music theory reference docs
- Covers chord substitution, genre conventions, scales/modes, song structure, arrangement, melody writing, and more

## Quickstart

### Prerequisites

- **Python 3.13** (3.11+ should work; avoid 3.14 due to dependency issues)
- **Ollama** installed and running ([ollama.com](https://ollama.com))

### 1. Clone and set up

```bash
git clone https://github.com/jtspetersen/woodshed-ai.git
cd woodshed-ai
python -m venv venv
source venv/bin/activate        # Linux/macOS
source venv/Scripts/activate    # Windows (Git Bash / MSYS)
pip install -r requirements.txt
```

### 2. Pull Ollama models

```bash
ollama pull qwen2.5:32b         # Primary LLM (or any model you prefer)
ollama pull nomic-embed-text    # Embedding model for the knowledge base
```

### 3. Configure (optional)

Create a `.env` file in the project root to override defaults:

```env
LLM_MODEL=qwen2.5:32b
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_HOST=http://localhost:11434
TEMPERATURE=0.7
```

See [config.py](config.py) for all available settings.

### 4. Build the knowledge base

```bash
python -c "from app.knowledge.ingest import ingest_starter_data; ingest_starter_data()"
```

This indexes the curated reference docs in `data/starter/` into ChromaDB. The vector store is saved to `data/chromadb/` (gitignored, rebuilt locally).

### 5. Run

```bash
python main.py
```

Open [http://localhost:7860](http://localhost:7860) in your browser.

### Audio transcription (optional)

To enable audio-to-MIDI transcription, set up the Basic Pitch microservice:

```bash
cd services/basic-pitch
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install basic-pitch flask
```

The service starts automatically when you run `main.py` (if the venv exists).

## Project Structure

```
woodshed-ai/
├── main.py                     # Application entry point
├── config.py                   # Central configuration
├── requirements.txt            # Python dependencies
├── app/
│   ├── audio/                  # MIDI analysis + audio transcription
│   ├── knowledge/              # ChromaDB vector store + RAG ingestion
│   ├── llm/                    # Ollama client, conversation pipeline, prompts
│   ├── output/                 # MIDI generation, notation, guitar tab, export
│   ├── theory/                 # music21 theory engine + tool schemas
│   └── ui/                     # Gradio web interface
├── services/
│   └── basic-pitch/            # Audio-to-MIDI transcription microservice
├── data/
│   ├── starter/                # Curated reference docs (committed)
│   ├── local/                  # User files — MIDI, exports (gitignored)
│   └── chromadb/               # Vector store (gitignored, rebuilt locally)
├── tests/                      # 107 tests across all modules
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
python -m pytest tests/ -q
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
| Web UI | [Gradio](https://gradio.app/) |
| Notation rendering | [abcjs](https://www.abcjs.net/) (client-side) |

## License

[GPL-3.0-or-later](LICENSE)
