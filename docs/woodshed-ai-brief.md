# Woodshed AI — Project Brief

## Project Name
**Woodshed AI**

## Owner
Josh Petersen — Senior Program Manager, musician, Oakland CA

## Last Updated
February 23, 2026

---

## 1. Vision

A locally-hosted, AI-powered songwriting tool — named for the musician's tradition of "woodshedding," the practice of retreating to work intensely on your craft. The user feeds it raw ideas — audio recordings, MIDI files, text descriptions — and it responds with music-theory-grounded suggestions for chords, melodies, arrangements, and song structure. It can analyze what the user gives it, explain *why* its suggestions work, and produce playable MIDI examples and notation/tab output.

The tool runs entirely on local infrastructure (no cloud APIs, no data leaving the machine), leveraging open-source LLMs via Ollama and a curated knowledge base built from open-source music theory, production, and instrumentation resources.

---

## 2. Problem Statement

Songwriters often get stuck between an initial idea (a riff, a chord loop, a melody fragment) and a finished song. The gap requires music theory knowledge, awareness of genre conventions, and the ability to explore "what if" variations quickly. Existing tools either:

- Require deep theory knowledge the user may not have
- Generate music without explanation (black box)
- Are cloud-dependent and/or expensive
- Don't accept mixed input types (audio + text + MIDI)

This tool bridges that gap by combining conversational AI, structured music theory reasoning, and audio analysis into a single local workflow.

---

## 3. User Stories

### Phase 1 — Text-Based Theory Companion
- **As a songwriter**, I want to type a chord progression and get suggestions for what comes next, with music theory explanations, so I can learn while I write.
- **As a songwriter**, I want to describe a mood or style ("jazzy, melancholy, in D minor") and get chord and scale suggestions that match.
- **As a songwriter**, I want to ask "why does this progression feel unresolved?" and get a theory-backed explanation.
- **As a songwriter**, I want to input a verse structure and get chorus/bridge suggestions that complement it.
- **As a songwriter**, I want the tool to know about different genres, instrumentation, and production techniques so its suggestions are contextually informed.

### Phase 2 — Audio/MIDI Analysis
- **As a songwriter**, I want to upload a voice memo of me humming a melody and get it transcribed to notes/chords.
- **As a songwriter**, I want to upload a guitar recording and have the tool identify the key, chords, and suggest where to take it.
- **As a songwriter**, I want to import a MIDI file from my DAW and have the tool analyze it and suggest improvements or variations.

### Phase 3 — Playable Output
- **As a songwriter**, I want the tool to generate MIDI files I can play back in the browser or import into my DAW.
- **As a songwriter**, I want to see suggestions rendered as standard notation and/or guitar tablature.
- **As a songwriter**, I want to hear a suggested chord progression played back with realistic instrument sounds.

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                Browser UI (Gradio)                   │
│  Woodshed AI — your AI practice partner              │
│         Text input, audio upload, MIDI upload        │
│         Notation display, MIDI playback, tabs        │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────┐  ┌──────────────────────────┐
│   Conversation Layer  │  │     Audio/MIDI Pipeline   │
│   (Ollama LLM + RAG) │  │  (Basic Pitch, pretty_midi│
│                       │  │   mido, librosa)          │
└──────────┬───────────┘  └──────────┬───────────────┘
           │                         │
           ▼                         ▼
┌──────────────────────────────────────────────────────┐
│              Music Theory Engine (music21)            │
│   Chord analysis, key detection, voice leading,      │
│   scale suggestions, roman numeral analysis,         │
│   notation rendering, MIDI generation                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│           Knowledge Base (ChromaDB + Embeddings)     │
│   Open-source music theory texts, production guides, │
│   genre conventions, instrumentation references      │
└──────────────────────────────────────────────────────┘
```

### Data Flow — Phase 1 (Text)
1. User types a question or chord progression into the UI
2. System searches ChromaDB for relevant music theory context
3. Context + user input are sent to Ollama LLM
4. LLM can call music21 functions as tools (analyze chords, suggest progressions, detect key)
5. LLM returns a response combining theory explanation + music21 analysis
6. UI displays the response with any formatted notation

### Data Flow — Phase 2 (Audio/MIDI Input)
1. User uploads audio file or MIDI file
2. Audio files → Basic Pitch converts to MIDI
3. MIDI → music21 parses into musical objects (notes, chords, key)
4. Parsed analysis is injected into the conversation as context
5. LLM responds with analysis and suggestions, using music21 tools as needed

### Data Flow — Phase 3 (Playable Output)
1. LLM generates a suggestion (e.g., a chord progression or melody)
2. music21 converts the suggestion into a MIDI file and/or notation
3. UI renders notation via VexFlow (or music21's built-in rendering)
4. UI plays MIDI via FluidSynth (server-side) or Tone.js (client-side)
5. User can download MIDI for import into their DAW

---

## 5. Technology Stack

### Core Runtime
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11+ | Primary application language |
| LLM Runtime | Ollama | Local LLM inference |
| UI Framework | Gradio | Browser-based interface |
| Package Manager | pip + venv | Dependency management |

### LLM & Knowledge Layer
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Primary LLM | **Qwen 2.5:32B** | Best structured output & tool-use from installed models |
| Embedding Model | **nomic-embed-text** (via Ollama) | Vector embeddings for RAG knowledge base |
| Vector Database | ChromaDB | Local vector storage and similarity search |
| RAG Framework | LangChain or LlamaIndex | Orchestration of retrieval + generation pipeline |

#### Model Recommendations & Rationale
- **Qwen 2.5:32B** is recommended as the primary model because it has the strongest structured output and function/tool-calling capabilities among the installed models. This is critical for Phase 1 where the LLM needs to reliably call music21 functions and return structured chord/scale data.
- **Qwen 3:30B** is a viable alternative with newer architecture but may be less tested for tool-use patterns. Worth benchmarking against Qwen 2.5:32B during development.
- **Qwen 3:8B / Qwen 2.5:7B** can serve as fast fallback models for simple queries (e.g., "what notes are in a Dm7?") where speed matters more than depth.
- **Gemma 3:27B** is strong at general reasoning but less proven at structured tool-use. Could be useful for the conversational/creative aspects (lyrical suggestions, mood descriptions).
- **nomic-embed-text** needs to be pulled via Ollama (`ollama pull nomic-embed-text`). It's the standard embedding model for local RAG setups.

### Music Theory & Audio
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Music Theory Engine | music21 | Chord analysis, key detection, scales, notation, MIDI generation |
| Audio-to-MIDI | Basic Pitch (Spotify) | Converts audio recordings to MIDI (Phase 2) |
| MIDI Processing | pretty_midi, mido | Read/write/manipulate MIDI files |
| Audio Analysis | librosa | Audio feature extraction, onset detection (Phase 2) |

### Output & Rendering
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Notation Rendering | music21 + LilyPond (or VexFlow) | Sheet music and tab display |
| MIDI Playback | FluidSynth (server) or Tone.js (browser) | Play generated MIDI examples |
| Soundfont | FluidR3_GM.sf2 (free General MIDI) | Realistic instrument sounds for playback |

---

## 6. Knowledge Base Strategy

The knowledge base is the "brain" behind the RAG system. It should be built from **open-source, freely available** music theory and production resources.

### Source Categories

**Music Theory Foundations**
- Open Music Theory (open textbook — openmusictheory.com)
- Music Theory for the 21st Century Classroom (open textbook)
- Hooktheory's TheoryTab dataset (chord progression database with analysis)
- Wikipedia music theory articles (scales, modes, chord types, cadences, etc.)

**Genre & Style References**
- Genre-specific chord progression databases
- Style guides for jazz, blues, rock, pop, folk, classical, etc.
- Common progressions by genre (e.g., I-IV-V-I in blues, ii-V-I in jazz)

**Production & Instrumentation**
- Open-source production guides and tutorials
- Instrument range and voicing references
- Arrangement and orchestration basics

**Songwriting Craft**
- Song structure conventions (verse-chorus, AABA, etc.)
- Lyric-melody relationship guides
- Rhythmic pattern references by genre

### Ingestion Process
1. Collect source documents (PDFs, web scrapes, markdown)
2. Clean and chunk into ~500-token passages with overlap
3. Generate embeddings using nomic-embed-text via Ollama
4. Store in ChromaDB with metadata (source, category, topic)
5. Build retrieval queries that search by both semantic similarity and category filters

---

## 7. Key Design Decisions

### Local-First
Everything runs on Josh's local machine (AMD-based system with Ollama already configured). No cloud dependencies, no API costs, full data privacy.

### Explanation-First AI
The tool doesn't just suggest — it explains. Every suggestion should include the music theory reasoning behind it. This makes it a learning tool as well as a creative tool.

### Modular Architecture
Each component (LLM, knowledge base, music21, audio pipeline) is a separate module that can be developed and tested independently. This supports the phased rollout and makes it easy to swap components later.

### LLM as Orchestrator
The LLM acts as the "brain" that decides when to search the knowledge base, when to call music21 for analysis, and how to synthesize results into a helpful response. It uses a tool-use pattern where music21 functions are exposed as callable tools.

---

## 8. Success Criteria

### Phase 1 MVP
- [ ] User can type a chord progression and receive theory-backed suggestions
- [ ] User can describe a mood/style and receive relevant chord/scale recommendations
- [ ] LLM responses reference real music theory (not hallucinated rules)
- [ ] music21 is called for actual analysis (key detection, chord quality, roman numeral analysis)
- [ ] Knowledge base contains at least 3 curated music theory sources
- [ ] UI runs in browser on localhost

### Phase 2
- [ ] User can upload a voice memo and see it transcribed to notes
- [ ] User can upload a guitar recording and get key/chord identification
- [ ] User can import MIDI and receive analysis
- [ ] Audio/MIDI analysis feeds into the conversation context

### Phase 3
- [ ] Tool generates downloadable MIDI files from suggestions
- [ ] Notation renders in the browser (standard notation and/or guitar tab)
- [ ] MIDI playback works in the browser
- [ ] User can export suggestions to their DAW

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucinating music theory | Wrong suggestions, broken trust | Use RAG + music21 validation; LLM never suggests without theory engine confirmation |
| Audio-to-MIDI accuracy | Bad transcriptions from noisy recordings | Basic Pitch is best-in-class; add confidence scores; let user correct |
| music21 tool-use reliability | LLM fails to call tools correctly | Use Qwen 2.5:32B (best tool-use); build robust prompts; add fallback parsing |
| Knowledge base gaps | Incomplete genre/style coverage | Start broad, expand iteratively; let user flag gaps |
| Scope creep | Never ships | Strict phased approach; Phase 1 is fully usable alone |

---

## 10. Future Possibilities (Post-MVP)

- **DAW integration** via MIDI over network or plugin architecture
- **Fine-tuned model** trained on curated music theory corpus for faster/better responses
- **Multi-track arrangement** suggestions (drums, bass, keys, etc.)
- **Lyric analysis and suggestion** integrated with melodic content
- **Collaborative mode** where multiple users jam with the AI
- **Mobile companion** for capturing ideas on the go
