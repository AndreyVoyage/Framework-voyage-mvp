"""Semantic Memory — векторное хранилище для кода.

Реализация Phase 2 MVP использует numpy-based in-memory store
с hash-based embeddings. Это позволяет работать без torch/onnxruntime.
В будущем можно добавить ChromaDB backend как опциональный.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from numpy.linalg import norm

from voyage_framework.core.models import MemoryEntry, SearchResult
from voyage_framework.core.storage import atomic_write


class SimpleEmbeddingFunction:
    """Лёгкая embedding function на основе хэшей слов.

    Не требует torch, onnxruntime или sentence-transformers.
    Подходит для MVP и тестов.
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def __call__(self, texts: list[str]) -> list[list[float]]:
        """Превратить список текстов в список векторов."""
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        for word in text.lower().split():
            vec[hash(word) % self.dim] += 1.0
        vec_norm = norm(vec)
        if vec_norm > 0:
            vec /= vec_norm
        return vec.tolist()


class SemanticStore:
    """Векторное хранилище документов с semantic search.

    Args:
        collection_name: Имя коллекции.
        embedding_function: Функция эмбеддинга. По умолчанию SimpleEmbeddingFunction.
        persist_directory: Директория для сохранения коллекции.
                           Если None — хранилище только в памяти.
    """

    def __init__(
        self,
        collection_name: str = "codebase",
        embedding_function: Callable[[list[str]], list[list[float]]] | None = None,
        persist_directory: Path | str | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.embedding_function = embedding_function or SimpleEmbeddingFunction()
        self.persist_directory = Path(persist_directory) if persist_directory else None

        self._documents: dict[str, MemoryEntry] = {}
        self._embeddings: dict[str, np.ndarray] = {}

        if self.persist_directory:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._load()

    def add_documents(self, entries: list[MemoryEntry]) -> list[str]:
        """Добавить документы в хранилище.

        Returns:
            Список ID добавленных документов.
        """
        if not entries:
            return []

        texts = [entry.text for entry in entries]
        embeddings = self.embedding_function(texts)

        ids: list[str] = []
        for entry, embedding in zip(entries, embeddings, strict=True):
            self._documents[entry.id] = entry
            self._embeddings[entry.id] = np.array(embedding, dtype=np.float32)
            ids.append(entry.id)

        self._save()
        return ids

    def query(
        self,
        text: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Найти top-K документов, похожих на запрос.

        Args:
            text: Текст запроса.
            top_k: Максимальное количество результатов.
            filters: Опциональный фильтр по metadata (простое равенство).

        Returns:
            Список SearchResult, отсортированных по убыванию score.
        """
        if not self._documents:
            return []

        query_embedding = np.array(
            self.embedding_function([text])[0],
            dtype=np.float32,
        )

        candidates = self._filter_candidates(filters)
        if not candidates:
            return []

        ids = list(candidates.keys())
        matrix = np.stack([self._embeddings[doc_id] for doc_id in ids])
        scores = matrix @ query_embedding

        ranked = sorted(
            zip(ids, scores.tolist(), strict=True),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]

        return [
            SearchResult(
                id=doc_id,
                text=self._documents[doc_id].text,
                score=max(0.0, min(1.0, score)),
                metadata=self._documents[doc_id].metadata,
            )
            for doc_id, score in ranked
        ]

    def delete(self, ids: list[str]) -> None:
        """Удалить документы по ID."""
        for doc_id in ids:
            self._documents.pop(doc_id, None)
            self._embeddings.pop(doc_id, None)
        self._save()

    def count(self) -> int:
        """Количество документов в хранилище."""
        return len(self._documents)

    def _filter_candidates(
        self,
        filters: dict[str, Any] | None,
    ) -> dict[str, MemoryEntry]:
        """Отфильтровать документы по metadata."""
        if not filters:
            return self._documents.copy()

        return {
            doc_id: entry
            for doc_id, entry in self._documents.items()
            if all(entry.metadata.get(k) == v for k, v in filters.items())
        }

    def _save(self) -> None:
        """Сохранить коллекцию на диск, если указана persist_directory."""
        if not self.persist_directory:
            return

        data = {
            "collection_name": self.collection_name,
            "documents": {
                doc_id: {
                    "id": entry.id,
                    "text": entry.text,
                    "metadata": entry.metadata,
                    "embedding": self._embeddings[doc_id].tolist(),
                }
                for doc_id, entry in self._documents.items()
            },
        }
        path = self.persist_directory / f"{self.collection_name}.json"
        atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self) -> None:
        """Загрузить коллекцию с диска."""
        assert self.persist_directory is not None
        path = self.persist_directory / f"{self.collection_name}.json"
        if not path.exists():
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for doc_id, raw in data.get("documents", {}).items():
            entry = MemoryEntry(
                id=raw["id"],
                text=raw["text"],
                metadata=raw.get("metadata", {}),
                embedding=raw.get("embedding"),
            )
            self._documents[doc_id] = entry
            self._embeddings[doc_id] = np.array(
                entry.embedding or self.embedding_function([entry.text])[0],
                dtype=np.float32,
            )
