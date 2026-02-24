# Woodshed AI — Project Plan

## Purpose of This Document
This project plan is designed to be used with **Claude Code** as the primary engineering tool and **Claude Opus** as the design/strategy advisor. Each task is written as a self-contained instruction that Claude Code can execute. Tasks are small, testable, and sequential.

**Project:** Woodshed AI — a locally-hosted, AI-powered songwriting companion.

## How to Use This Plan

### With Claude Code (Engineer)
Copy a task's description and acceptance criteria into Claude Code. It will write the code, create files, and run tests. Review output before moving to the next task.

**Example prompt to Claude Code:**
> "I'm building a Songwriting Companion app. Here's the project brief: [paste brief or point to file]. I'm on Task 1.1 — set up the project skeleton. Here are the requirements: [paste task]. Please implement this step."

### With Claude Opus (Designer / Advisor)
Use for architecture decisions, prompt engineering for the LLM, knowledge base curation strategy, UI/UX design, and troubleshooting when things don't work as expected.

---

## Environment Prerequisites
- **OS**: Linux (Ubuntu-based, AMD system)
- **Python**: 3.11+
- **Ollama**: Installed and running with Qwen 2.5:32B available
- **Disk space**: ~5GB free for knowledge base, models, and soundfonts
- **Browser**: For Gradio UI

---

## PHASE 1: Text-Based Music Theory Companion

### Milestone: User can have a text conversation with an AI that gives music-theory-grounded chord and songwriting suggestions, backed by a curated knowledge base and the music21 analysis engine.

---

### Task 1.1 — Project Skeleton & Environment Setup

**What to do:**
Create the project directory structure and Python virtual environment. Install core dependencies and verify each one works.

**Directory structure:**
```
songwriting-companion/ → woodshed-ai/
├── .env                        # Environment variables (model names, paths)
├── .gitignore
├── README.md
├── requirements.txt
├── config.py                   # Central configuration (reads from .env)
├── main.py                     # Application entry point
├── app/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── gradio_app.py       # Gradio UI definition
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── ollama_client.py    # Ollama API wrapper
│   │   └── prompts.py          # System prompts and prompt templates
│   ├── theory/
│   │   ├── __init__.py
│   │   ├── engine.py           # music21 wrapper functions exposed as tools
│   │   └── tools.py            # Tool definitions for LLM tool-use
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Embedding generation via Ollama
│   │   ├── vectorstore.py      # ChromaDB wrapper
│   │   └── ingest.py           # Document ingestion pipeline
│   └── audio/                  # Phase 2 — placeholder for now
│       ├── __init__.py
│       └── transcribe.py
├── data/
│   ├── sources/                # Raw source documents for knowledge base
│   ├── chromadb/               # ChromaDB persistent storage
│   └── midi/                   # Generated MIDI output files
└── tests/
    ├── test_ollama.py
    ├── test_music21.py
    ├── test_knowledge.py
    └── test_theory_tools.py
```

**Dependencies (requirements.txt):**
```
music21>=9.1
chromadb>=0.4
gradio>=4.0
ollama>=0.3
python-dotenv>=1.0
requests>=2.31
```

**Acceptance criteria:**
- [ ] Virtual environment created and activated
- [ ] All packages install without errors
- [ ] `python -c "import music21; print(music21.VERSION_STR)"` prints version
- [ ] `python -c "import chromadb; print(chromadb.__version__)"` prints version
- [ ] `python -c "import gradio; print(gradio.__version__)"` prints version
- [ ] `python -c "import ollama; print('ok')"` prints ok
- [ ] `ollama list` shows Qwen 2.5:32B available
- [ ] Directory structure created as specified
- [ ] .env file created with placeholder values
- [ ] .gitignore includes venv/, data/chromadb/, __pycache__/, .env

---

### Task 1.2 — Ollama Client Wrapper

**What to do:**
Create a Python wrapper around the Ollama API that handles chat completions with tool-use support. This is the central interface between the app and the LLM.

**File:** `app/llm/ollama_client.py`

**Requirements:**
- Use the `ollama` Python package
- Support basic chat (messages in, text out)
- Support tool-use / function-calling pattern (messages in, tool calls or text out)
- Handle streaming responses for the UI
- Read model name from config (default: `qwen2.5:32b`)
- Include error handling for connection failures (Ollama not running, model not loaded)
- Include a simple test function that sends "What key is C-E-G?" and prints the response

**Key function signatures:**
```python
def chat(messages: list[dict], tools: list[dict] = None, stream: bool = False) -> dict
def chat_stream(messages: list[dict], tools: list[dict] = None) -> Generator
def get_embedding(text: str, model: str = "nomic-embed-text") -> list[float]
```

**Acceptance criteria:**
- [ ] Can send a basic chat message to Qwen 2.5:32B and get a response
- [ ] Can send a message with tool definitions and get a tool_call response back
- [ ] Streaming works (yields chunks)
- [ ] Embedding generation works with nomic-embed-text
- [ ] Connection errors are caught and return a useful error message
- [ ] Test script passes: `python -m tests.test_ollama`

---

### Task 1.3 — Music21 Theory Engine (Tool Functions)

**What to do:**
Create a set of music theory functions using music21 that will be exposed as tools the LLM can call. Each function takes simple string inputs and returns structured data.

**File:** `app/theory/engine.py`

**Functions to implement:**

```python
def analyze_chord(chord_symbol: str) -> dict
    # Input: "Dm7" → Output: {root: "D", quality: "minor seventh", notes: ["D","F","A","C"], intervals: [...]}

def analyze_progression(chords: list[str], key: str = None) -> dict
    # Input: ["Dm7", "G7", "Cmaj7"] → Output: {key: "C major", roman_numerals: ["ii7","V7","Imaj7"], analysis: "..."}

def suggest_next_chord(chords: list[str], style: str = "general") -> dict
    # Input: ["Dm7", "G7"] → Output: {suggestions: [{chord: "Cmaj7", reason: "Resolves V7→I"}, ...]}

def get_scale_for_mood(mood: str, root: str = None) -> dict
    # Input: mood="melancholy", root="D" → Output: {scales: [{name: "D natural minor", notes: [...], why: "..."}]}

def detect_key(notes: list[str]) -> dict
    # Input: ["D", "F", "A", "C", "G", "B"] → Output: {key: "C major", confidence: 0.85, alternatives: [...]}

def get_chord_voicings(chord_symbol: str, instrument: str = "guitar") -> dict
    # Input: "Dm7", "guitar" → Output: {voicings: [{name: "standard", frets: "xx0211", fingering: "..."}]}

def get_related_chords(chord_symbol: str) -> dict
    # Input: "Dm7" → Output: {substitutions: [...], borrowed_chords: [...], extensions: [...]}
```

**File:** `app/theory/tools.py`

Define each function above as a tool schema compatible with Ollama's tool-use format:
```python
MUSIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_progression",
            "description": "Analyze a chord progression...",
            "parameters": { ... }
        }
    },
    ...
]
```

**Acceptance criteria:**
- [ ] Each function works independently with simple test inputs
- [ ] Functions return structured dicts (not raw music21 objects)
- [ ] Tool schemas are valid and match function signatures
- [ ] Error handling for invalid chord symbols (e.g., "Xzz9") returns a clear message
- [ ] Test script passes: `python -m tests.test_music21`

---

### Task 1.4 — Knowledge Base: Document Ingestion Pipeline

**What to do:**
Build the pipeline that takes music theory source documents, chunks them, generates embeddings, and stores them in ChromaDB.

**File:** `app/knowledge/ingest.py`
**File:** `app/knowledge/embeddings.py`
**File:** `app/knowledge/vectorstore.py`

**Ingestion pipeline steps:**
1. Read source files from `data/sources/` (supports .txt, .md, .pdf, .html)
2. Clean and normalize text (remove headers/footers, fix encoding)
3. Chunk into ~500-token passages with ~50-token overlap
4. Generate embeddings for each chunk using Ollama + nomic-embed-text
5. Store chunks + embeddings + metadata in ChromaDB (persistent, saved to `data/chromadb/`)

**Metadata per chunk:**
```python
{
    "source": "open_music_theory",
    "category": "harmony",       # harmony, melody, rhythm, form, production, genre, instrumentation
    "chapter": "Secondary Dominants",
    "url": "https://..."          # if applicable
}
```

**ChromaDB wrapper should support:**
```python
def add_documents(chunks: list[str], metadatas: list[dict], ids: list[str])
def search(query: str, n_results: int = 5, category_filter: str = None) -> list[dict]
def get_collection_stats() -> dict   # count of docs, categories breakdown
```

**Acceptance criteria:**
- [ ] Can ingest a sample .txt file and store it in ChromaDB
- [ ] Embeddings are generated via Ollama nomic-embed-text
- [ ] Search returns relevant chunks for a query like "secondary dominant chords"
- [ ] Category filtering works
- [ ] Collection persists between runs (data saved to disk)
- [ ] Stats function shows document count and category breakdown
- [ ] Test script passes: `python -m tests.test_knowledge`

---

### Task 1.5 — Seed the Knowledge Base

**What to do:**
Curate and ingest the initial set of music theory sources. This is a content task — focus on getting high-quality, diverse content into the knowledge base.

**Sources to ingest (all open-source or freely available):**

1. **Open Music Theory** — https://openmusictheory.com
   - Scrape or download key chapters: fundamentals, harmony, form, pop/rock analysis
   - Category tags: harmony, melody, rhythm, form

2. **Music Theory for the 21st Century Classroom** — https://musictheory.pugetsound.edu
   - Download relevant chapters
   - Category tags: harmony, melody, rhythm

3. **Create curated reference documents** for topics not well-covered by textbooks:
   - `genre_progressions.md` — Common chord progressions by genre (blues, jazz, pop, rock, folk, R&B, country) with roman numeral analysis and examples
   - `chord_substitution_guide.md` — Tritone subs, modal interchange, secondary dominants, diminished passing chords
   - `song_structure_guide.md` — Verse-chorus, AABA, through-composed, bridge conventions by genre
   - `guitar_voicings_reference.md` — Common voicings, open vs barre, jazz voicings, drop voicings
   - `mood_to_theory_mapping.md` — Mapping emotional descriptors to scales, modes, chord qualities, tempos

4. **Wikipedia music theory articles** (curated selection):
   - Diatonic and chromatic scales, modes, chord types, cadences
   - Circle of fifths, voice leading, counterpoint basics
   - Category tags: as appropriate per article

**Acceptance criteria:**
- [ ] At least 500 chunks ingested across all sources
- [ ] All 7 categories represented (harmony, melody, rhythm, form, production, genre, instrumentation)
- [ ] Custom reference documents created and ingested
- [ ] Search quality spot-check: 10 sample queries return relevant results
  - "What chords work in a blues progression?"
  - "How do secondary dominants work?"
  - "What scale sounds melancholy?"
  - "Common jazz chord substitutions"
  - "Verse-chorus song structure"
  - "Guitar voicings for jazz"
  - "What is modal interchange?"
  - "How to write a bridge"
  - "Difference between Dorian and Aeolian"
  - "What makes a cadence feel resolved?"

---

### Task 1.6 — RAG Pipeline: Connect Knowledge Base to LLM

**What to do:**
Wire together the Ollama client, ChromaDB knowledge base, and music21 tools into a single conversation pipeline. When the user sends a message:

1. Search ChromaDB for relevant theory context
2. Build a prompt that includes: system instructions, retrieved context, music21 tool definitions, and the user's message
3. Send to Ollama
4. If LLM returns a tool call → execute the music21 function → feed result back to LLM
5. Return final response to user

**File:** `app/llm/prompts.py`

**System prompt should instruct the LLM to:**
- Act as **Woodshed AI**, a knowledgeable music theory advisor and songwriting collaborator
- Always explain the theory behind suggestions
- Use the provided music21 tools for analysis rather than guessing
- Reference retrieved knowledge base context when relevant
- Format chord symbols consistently (e.g., Dm7, Cmaj7, G7, F#m)
- When suggesting progressions, include roman numeral analysis
- Adapt language to be accessible (avoid overly academic jargon unless the user signals advanced knowledge)
- Ask clarifying questions when the user's request is ambiguous

**File:** `app/llm/pipeline.py` (new file)

```python
class MusicConversation:
    def __init__(self):
        self.messages = []          # Conversation history
        self.ollama = OllamaClient()
        self.knowledge = VectorStore()
        self.theory = TheoryEngine()

    def send(self, user_message: str) -> str:
        # 1. Search knowledge base
        context = self.knowledge.search(user_message, n_results=5)

        # 2. Build augmented prompt
        augmented_messages = self._build_messages(user_message, context)

        # 3. Call LLM with tools
        response = self.ollama.chat(augmented_messages, tools=MUSIC_TOOLS)

        # 4. Handle tool calls (may loop multiple times)
        while response.has_tool_calls:
            tool_results = self._execute_tools(response.tool_calls)
            augmented_messages.append(response)
            augmented_messages.append(tool_results)
            response = self.ollama.chat(augmented_messages, tools=MUSIC_TOOLS)

        # 5. Store in history and return
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": response.text})
        return response.text
```

**Acceptance criteria:**
- [ ] Full pipeline works end-to-end: user message → context retrieval → LLM → response
- [ ] LLM successfully calls music21 tools when appropriate
- [ ] Tool results are fed back to LLM and incorporated into response
- [ ] Conversation history is maintained across messages
- [ ] System prompt produces helpful, theory-grounded responses
- [ ] Test conversation passes:
  - "What key is this progression in: Am, F, C, G?" → Should identify key and provide roman numerals
  - "Suggest a jazzy chord to follow Dm7 → G7" → Should suggest Cmaj7 or similar with explanation
  - "I want something melancholy in E minor" → Should suggest appropriate chords/scales

---

### Task 1.7 — Gradio UI (Phase 1)

**What to do:**
Build a browser-based chat interface using Gradio that connects to the conversation pipeline.

**File:** `app/ui/gradio_app.py`
**File:** `main.py` (update to launch the app)

**UI Requirements:**
- Chat interface (text input, message history)
- System status indicator (Ollama connected, knowledge base loaded, doc count)
- Conversation controls: "New conversation" button, "Clear history"
- Display area for any formatted output (chord diagrams, roman numeral analysis)
- Settings panel:
  - Model selector (dropdown of available Ollama models)
  - Temperature slider (0.1 to 1.0, default 0.7)
  - Knowledge base category filter (checkboxes for categories)
- Runs on localhost:7860 (Gradio default)

**Launch command:** `python main.py`

**Acceptance criteria:**
- [ ] App launches in browser at localhost:7860
- [ ] User can type a message and receive a response
- [ ] Conversation history displays correctly
- [ ] New conversation button works
- [ ] Model selector shows available models
- [ ] Temperature slider affects response variety
- [ ] Status indicator shows system health
- [ ] App handles errors gracefully (e.g., Ollama not running)

---

### Task 1.8 — Testing & Quality Pass

**What to do:**
Run a thorough test of the complete Phase 1 system. Test with real songwriting scenarios and fix issues.

**Test scenarios:**

1. **Basic theory questions:**
   - "What notes are in a C major scale?"
   - "What's the difference between major and minor?"
   - "Explain the circle of fifths"

2. **Chord analysis:**
   - "Analyze this progression: Em, C, G, D"
   - "What key is Am, Dm, E7, Am in?"
   - "Why does this sound unresolved: C, F, G?"

3. **Creative suggestions:**
   - "I have a verse in D minor with Dm, Bb, F, C. Suggest a chorus."
   - "Give me a jazzy chord progression in Eb"
   - "I want something that sounds like a rainy day — what chords and scale should I use?"

4. **Genre-specific:**
   - "What makes a blues progression different from a rock progression?"
   - "Give me a bossa nova chord progression"
   - "How would I make this more R&B: Cm, Ab, Eb, Bb?"

5. **Edge cases:**
   - Very long messages
   - Misspelled chord names
   - Ambiguous requests ("make it sound cooler")
   - Requests outside scope ("write me lyrics" — should handle gracefully)

**Acceptance criteria:**
- [ ] All 5 scenario categories produce reasonable responses
- [ ] No crashes or unhandled exceptions
- [ ] Tool calls succeed at least 80% of the time
- [ ] Knowledge base context visibly improves response quality vs. no RAG
- [ ] Response time under 30 seconds for typical queries
- [ ] Document any bugs or limitations found for future fixes

---

## PHASE 2: Audio/MIDI Analysis (Tasks 2.1–2.5)

> Phase 2 tasks are outlined at a high level. Detailed task specs should be written after Phase 1 is complete and stable.

### Task 2.1 — Install Audio Pipeline Dependencies
Install Basic Pitch, librosa, pretty_midi, mido. Verify each with test inputs.

### Task 2.2 — Audio-to-MIDI Transcription
Build wrapper around Basic Pitch that takes an audio file (wav, mp3, m4a) and returns a MIDI representation. Handle voice memos, guitar recordings, and humming.

### Task 2.3 — MIDI Analysis Integration
Parse MIDI files (uploaded or transcribed) using music21. Extract key, tempo, chord progression, melody notes, time signature. Return structured analysis.

### Task 2.4 — Feed Audio Analysis into Conversation
When user uploads audio/MIDI, automatically analyze it and inject the analysis into the conversation context. LLM can then discuss and suggest based on what it "heard."

### Task 2.5 — UI Updates for Audio/MIDI Upload
Add file upload to Gradio UI. Show transcription results, waveform visualization, detected chords/key. Audio playback of uploaded file.

---

## PHASE 3: Playable Output (Tasks 3.1–3.5)

> Phase 3 tasks are outlined at a high level. Detailed task specs should be written after Phase 2 is complete and stable.

### Task 3.1 — MIDI Generation from Suggestions
When LLM suggests a progression or melody, generate a MIDI file using music21. Save to data/midi/.

### Task 3.2 — Notation Rendering
Render music21 output as standard notation (PNG/SVG via LilyPond or VexFlow). Display in Gradio UI.

### Task 3.3 — Guitar Tab Generation
Convert notation to guitar tablature using music21's tab capabilities. Display alongside standard notation.

### Task 3.4 — In-Browser MIDI Playback
Integrate Tone.js or FluidSynth for playing generated MIDI in the browser. Play/pause/tempo controls.

### Task 3.5 — Export & DAW Integration
Download buttons for MIDI files, notation PDFs, and tab PDFs. Document how to import into common DAWs (GarageBand, Logic, Ableton, Reaper).

---

## Task Dependency Map

```
1.1 Project Setup
 └── 1.2 Ollama Client
      ├── 1.3 Music21 Theory Engine
      │    └── 1.6 RAG Pipeline ──── 1.7 Gradio UI ──── 1.8 Testing
      └── 1.4 Knowledge Ingestion
           └── 1.5 Seed Knowledge Base
                └── 1.6 RAG Pipeline

Phase 2 depends on Phase 1 completion:
1.8 ──── 2.1 ──── 2.2 ──── 2.3 ──── 2.4 ──── 2.5

Phase 3 depends on Phase 2 completion:
2.5 ──── 3.1 ──── 3.2 ──── 3.3 ──── 3.4 ──── 3.5
```

---

## Working with Claude Code — Tips

1. **Start each session** by pointing Claude Code to this plan and the project brief. Example: "Read the project brief at `./woodshed-ai-brief.md` and the project plan at `./woodshed-ai-plan.md`. I'm starting Task 1.3."

2. **One task at a time.** Don't ask Claude Code to do multiple tasks at once. Complete and verify each task before moving on.

3. **Test after every task.** Each task has acceptance criteria — run through them before proceeding.

4. **Keep a log.** After each task, note what worked, what needed adjustment, and any decisions made. This helps maintain context across sessions.

5. **Use Claude Opus for decisions.** If you're unsure about an architecture choice, prompt engineering, or debugging strategy, bring it to Claude Opus for discussion before having Claude Code implement.

6. **The plan is a living document.** Update it as you learn. If a task needs to be split, revised, or reordered, do it.
