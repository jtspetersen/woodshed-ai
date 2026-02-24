# Woodshed AI — Document Ingestion
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pipeline for ingesting music theory documents into the knowledge base."""

import argparse
import re
import sys
from pathlib import Path

# Ensure project root is on path when run as module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from app.knowledge.vectorstore import VectorStore


# Chunking parameters
CHUNK_SIZE = 500  # target tokens (approx 4 chars per token)
CHUNK_OVERLAP = 50  # overlap tokens
CHARS_PER_TOKEN = 4  # rough approximation


def _split_into_sections(text: str) -> list[str]:
    """Split markdown text on headings (##, ###) to get logical sections."""
    # Split on markdown headings (keep the heading with its section)
    parts = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks of roughly chunk_size tokens.

    Strategy: split into sections first (by headings), then split large
    sections by paragraphs, then combine small pieces to fill chunks.
    """
    max_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = overlap * CHARS_PER_TOKEN

    sections = _split_into_sections(text)

    # Further split large sections by paragraphs
    pieces = []
    for section in sections:
        if len(section) <= max_chars:
            pieces.append(section)
        else:
            # Split by double newline (paragraphs)
            paragraphs = re.split(r"\n\n+", section)
            for para in paragraphs:
                if para.strip():
                    pieces.append(para.strip())

    # Combine small pieces into chunks of target size with overlap
    chunks = []
    current = ""
    for piece in pieces:
        candidate = (current + "\n\n" + piece).strip() if current else piece
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If this single piece exceeds max, force-split it
            if len(piece) > max_chars:
                words = piece.split()
                current = ""
                for word in words:
                    test = (current + " " + word).strip() if current else word
                    if len(test) <= max_chars:
                        current = test
                    else:
                        if current:
                            chunks.append(current)
                        current = word
            else:
                current = piece

    if current:
        chunks.append(current)

    # Apply overlap: prepend tail of previous chunk to each chunk
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap_chars:]
            overlapped.append(prev_tail + "\n\n" + chunks[i])
        chunks = overlapped

    return chunks


def _detect_category(filepath: Path) -> str:
    """Guess a category from the filename."""
    name = filepath.stem.lower()
    category_map = {
        "genre": "genre",
        "progression": "genre",
        "substitut": "harmony",
        "chord": "harmony",
        "scale": "harmony",
        "mode": "harmony",
        "cadence": "harmony",
        "resolution": "harmony",
        "mood": "harmony",
        "song_structure": "form",
        "structure": "form",
        "form": "form",
        "voicing": "instrumentation",
        "guitar": "instrumentation",
        "instrument": "instrumentation",
        "rhythm": "rhythm",
        "groove": "rhythm",
        "melody": "melody",
        "arrangement": "production",
        "production": "production",
        "mixing": "production",
    }
    for keyword, category in category_map.items():
        if keyword in name:
            return category
    return "general"


def ingest_directory(
    directory: Path,
    source_label: str,
    store: VectorStore,
    verbose: bool = True,
) -> int:
    """Ingest all .md and .txt files from a directory into the vector store.

    Returns the number of new chunks added.
    """
    if not directory.exists():
        if verbose:
            print(f"  Directory not found: {directory}")
        return 0

    files = sorted(list(directory.glob("*.md")) + list(directory.glob("*.txt")))
    if not files:
        if verbose:
            print(f"  No .md or .txt files in {directory}")
        return 0

    total_added = 0
    for filepath in files:
        text = filepath.read_text(encoding="utf-8")
        if not text.strip():
            continue

        chunks = _chunk_text(text)
        category = _detect_category(filepath)

        ids = [f"{source_label}_{filepath.stem}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": filepath.name,
                "source_dir": source_label,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        added = store.add_documents(ids=ids, documents=chunks, metadatas=metadatas)
        total_added += added
        if verbose:
            print(f"  {filepath.name}: {len(chunks)} chunks ({added} new) [{category}]")

    return total_added


def ingest_all(starter_only: bool = False, local_only: bool = False, verbose: bool = True) -> dict:
    """Run the full ingestion pipeline.

    Returns stats dict with counts.
    """
    store = VectorStore()

    starter_count = 0
    local_count = 0

    if not local_only:
        if verbose:
            print("Ingesting starter docs...")
        starter_count = ingest_directory(
            config.STARTER_DATA_DIR, "starter", store, verbose=verbose
        )

    if not starter_only:
        if verbose:
            print("Ingesting local docs...")
        local_count = ingest_directory(
            config.LOCAL_SOURCES_DIR, "local", store, verbose=verbose
        )

    stats = store.get_stats()
    if verbose:
        print(f"\nDone! {starter_count + local_count} new chunks added.")
        print(f"Total in knowledge base: {stats['total_chunks']} chunks")
        print(f"Sources: {stats['sources']}")
        print(f"Categories: {stats['categories']}")

    return {
        "starter_added": starter_count,
        "local_added": local_count,
        "total_chunks": stats["total_chunks"],
        "sources": stats["sources"],
        "categories": stats["categories"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into the Woodshed AI knowledge base.")
    parser.add_argument("--starter-only", action="store_true", help="Only ingest starter docs")
    parser.add_argument("--local-only", action="store_true", help="Only ingest local docs")
    args = parser.parse_args()
    ingest_all(starter_only=args.starter_only, local_only=args.local_only)
