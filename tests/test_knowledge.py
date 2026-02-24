# Woodshed AI — Knowledge Base Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the ChromaDB vector store and ingestion pipeline."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.knowledge.vectorstore import VectorStore
from app.knowledge.ingest import _chunk_text, _detect_category, ingest_directory


def _make_temp_store():
    """Create a VectorStore backed by a temp directory."""
    tmp = tempfile.mkdtemp(prefix="woodshed_test_")
    return VectorStore(persist_dir=tmp, collection_name="test_collection")


def test_add_and_search():
    """Add documents and search for them."""
    store = _make_temp_store()
    store.add_documents(
        ids=["doc1", "doc2", "doc3"],
        documents=[
            "The ii-V-I progression is the backbone of jazz harmony.",
            "A pentatonic scale has five notes and is common in blues and rock.",
            "Song form AABA is also known as 32-bar form.",
        ],
        metadatas=[
            {"source": "test.md", "category": "harmony"},
            {"source": "test.md", "category": "harmony"},
            {"source": "test.md", "category": "form"},
        ],
    )
    results = store.search("jazz chord progression", n_results=2)
    print(f"  Search returned {len(results)} results")
    assert len(results) == 2
    assert results[0]["document"]  # has content
    assert results[0]["metadata"]["category"]  # has metadata
    print(f"  Top result: {results[0]['document'][:80]}...")


def test_category_filter():
    """Search with category filter returns only matching category."""
    store = _make_temp_store()
    store.add_documents(
        ids=["h1", "f1"],
        documents=[
            "Dominant seventh chords resolve down a fifth.",
            "Verse-chorus form is the most common pop structure.",
        ],
        metadatas=[
            {"source": "test.md", "category": "harmony"},
            {"source": "test.md", "category": "form"},
        ],
    )
    results = store.search("common structure", n_results=5, category_filter="form")
    print(f"  Filtered results: {len(results)}")
    assert len(results) >= 1
    for r in results:
        assert r["metadata"]["category"] == "form"


def test_get_stats():
    """Stats reflect the correct count and metadata."""
    store = _make_temp_store()
    store.add_documents(
        ids=["a", "b"],
        documents=["Chord analysis.", "Scale modes."],
        metadatas=[
            {"source": "chords.md", "category": "harmony"},
            {"source": "scales.md", "category": "harmony"},
        ],
    )
    stats = store.get_stats()
    print(f"  Stats: {stats}")
    assert stats["total_chunks"] == 2
    assert "harmony" in stats["categories"]
    assert "chords.md" in stats["sources"]


def test_duplicate_ids_skipped():
    """Re-adding the same IDs should not create duplicates."""
    store = _make_temp_store()
    store.add_documents(ids=["x1"], documents=["First version."])
    added = store.add_documents(ids=["x1"], documents=["Second version."])
    assert added == 0
    assert store.get_stats()["total_chunks"] == 1
    print("  Duplicate correctly skipped")


def test_reset():
    """Reset clears all documents."""
    store = _make_temp_store()
    store.add_documents(ids=["r1", "r2"], documents=["A", "B"])
    assert store.get_stats()["total_chunks"] == 2
    store.reset()
    assert store.get_stats()["total_chunks"] == 0
    print("  Reset cleared collection")


def test_chunk_text():
    """Chunking splits text into reasonable pieces."""
    text = "# Heading\n\nParagraph one about chords.\n\n## Section Two\n\nParagraph two about scales.\n\n## Section Three\n\nParagraph three about rhythm."
    chunks = _chunk_text(text, chunk_size=20, overlap=0)
    print(f"  Chunks: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"    [{i}] {c[:60]}...")
    assert len(chunks) >= 2


def test_detect_category():
    """Category detection works for known filenames."""
    assert _detect_category(Path("genre_progressions.md")) == "genre"
    assert _detect_category(Path("chord_substitution_guide.md")) == "harmony"
    assert _detect_category(Path("song_structure_guide.md")) == "form"
    assert _detect_category(Path("guitar_voicings_reference.md")) == "instrumentation"
    assert _detect_category(Path("rhythm_and_groove_guide.md")) == "rhythm"
    assert _detect_category(Path("melody_writing_guide.md")) == "melody"
    assert _detect_category(Path("arrangement_basics.md")) == "production"
    assert _detect_category(Path("random_file.md")) == "general"
    print("  All categories detected correctly")


def test_ingest_directory():
    """Ingest a temp directory with test files."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="woodshed_ingest_"))
    store_dir = tempfile.mkdtemp(prefix="woodshed_store_")

    # Create test files
    (tmp_dir / "chord_basics.md").write_text(
        "# Chord Basics\n\nA chord is three or more notes played together.\n\n"
        "## Triads\n\nMajor triads have a root, major third, and perfect fifth.\n\n"
        "## Seventh Chords\n\nAdding a seventh creates richer harmony.\n",
        encoding="utf-8",
    )
    (tmp_dir / "scale_modes.md").write_text(
        "# Scales and Modes\n\nThe seven diatonic modes each have a unique character.\n\n"
        "## Ionian\n\nThe major scale. Bright and happy.\n\n"
        "## Dorian\n\nMinor with a raised sixth. Smooth and jazzy.\n",
        encoding="utf-8",
    )

    store = VectorStore(persist_dir=store_dir, collection_name="test_ingest")
    added = ingest_directory(tmp_dir, "test", store, verbose=True)
    print(f"  Ingested {added} chunks")
    assert added > 0

    stats = store.get_stats()
    assert stats["total_chunks"] == added
    assert "harmony" in stats["categories"]

    # Search should find relevant content
    results = store.search("seventh chords", n_results=3)
    assert len(results) > 0
    print(f"  Search 'seventh chords' -> {results[0]['document'][:80]}...")


if __name__ == "__main__":
    tests = [
        ("Add and search", test_add_and_search),
        ("Category filter", test_category_filter),
        ("Get stats", test_get_stats),
        ("Duplicate IDs skipped", test_duplicate_ids_skipped),
        ("Reset", test_reset),
        ("Chunk text", test_chunk_text),
        ("Detect category", test_detect_category),
        ("Ingest directory", test_ingest_directory),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
