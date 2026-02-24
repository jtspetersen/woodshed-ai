# Woodshed AI — Vector Store
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""ChromaDB wrapper for the music theory knowledge base."""

import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

import config


def _get_embedding_fn():
    """Create an Ollama embedding function for ChromaDB."""
    return OllamaEmbeddingFunction(
        url=config.OLLAMA_HOST,
        model_name=config.EMBEDDING_MODEL,
    )


class VectorStore:
    """Manages the ChromaDB collection for music theory documents."""

    def __init__(self, persist_dir: str | None = None, collection_name: str | None = None):
        persist_dir = persist_dir or str(config.CHROMA_PERSIST_DIR)
        collection_name = collection_name or config.CHROMA_COLLECTION

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._embedding_fn = _get_embedding_fn()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection(self):
        return self._collection

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ):
        """Add document chunks to the collection.

        Skips any IDs that already exist to allow safe re-ingestion.
        """
        # Filter out already-existing IDs
        existing = set()
        if ids:
            try:
                result = self._collection.get(ids=ids)
                existing = set(result["ids"])
            except Exception:
                pass

        new_ids = []
        new_docs = []
        new_metas = []
        for i, doc_id in enumerate(ids):
            if doc_id not in existing:
                new_ids.append(doc_id)
                new_docs.append(documents[i])
                if metadatas:
                    new_metas.append(metadatas[i])

        if not new_ids:
            return 0

        kwargs = dict(ids=new_ids, documents=new_docs)
        if new_metas:
            kwargs["metadatas"] = new_metas
        self._collection.add(**kwargs)
        return len(new_ids)

    def search(
        self,
        query: str,
        n_results: int = 5,
        category_filter: str | None = None,
    ) -> list[dict]:
        """Search the knowledge base and return matching chunks.

        Returns a list of dicts with keys: id, document, metadata, distance.
        """
        kwargs = dict(query_texts=[query], n_results=n_results)
        if category_filter:
            kwargs["where"] = {"category": category_filter}

        results = self._collection.query(**kwargs)

        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
        return items

    def get_stats(self) -> dict:
        """Return collection statistics."""
        count = self._collection.count()
        # Get unique sources and categories from metadata
        all_data = self._collection.get(include=["metadatas"]) if count > 0 else {"metadatas": []}
        sources = set()
        categories = set()
        for meta in (all_data["metadatas"] or []):
            if meta:
                if "source" in meta:
                    sources.add(meta["source"])
                if "category" in meta:
                    categories.add(meta["category"])

        return {
            "total_chunks": count,
            "sources": sorted(sources),
            "categories": sorted(categories),
        }

    def delete_by_source(self, source: str):
        """Delete all chunks from a specific source file."""
        self._collection.delete(where={"source": source})

    def reset(self):
        """Delete all documents in the collection."""
        # ChromaDB doesn't have a clear() — delete and recreate
        name = self._collection.name
        metadata = self._collection.metadata
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name,
            embedding_function=self._embedding_fn,
            metadata=metadata,
        )
