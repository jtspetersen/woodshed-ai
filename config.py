# Woodshed AI — Central Configuration
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
ROOT_DIR = Path(__file__).parent

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:32b")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen2.5:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Generation
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Performance
RAG_RESULTS = int(os.getenv("RAG_RESULTS", "3"))

# Data paths
CHROMA_PERSIST_DIR = ROOT_DIR / os.getenv("CHROMA_PERSIST_DIR", "data/chromadb")
STARTER_DATA_DIR = ROOT_DIR / os.getenv("STARTER_DATA_DIR", "data/starter")
LOCAL_DATA_DIR = ROOT_DIR / os.getenv("LOCAL_DATA_DIR", "data/local")
LOCAL_SOURCES_DIR = LOCAL_DATA_DIR / "sources"
LOCAL_MIDI_DIR = LOCAL_DATA_DIR / "midi"

# ChromaDB
CHROMA_COLLECTION = "music_theory"
