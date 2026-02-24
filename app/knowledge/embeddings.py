# Woodshed AI — Embedding Generation
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Embedding generation via Ollama for the knowledge base.

ChromaDB handles embeddings internally via OllamaEmbeddingFunction,
but this module exposes the standalone embedding API for use outside
the vector store (e.g., for similarity comparisons in the RAG pipeline).
"""

from app.llm.ollama_client import get_embedding

__all__ = ["get_embedding"]
