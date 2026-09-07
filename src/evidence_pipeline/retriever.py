from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from typing import Protocol

from .chunking import Chunk, normalized_tokens


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
    rank: int


class Retriever(Protocol):
    def index(self, chunks: list[Chunk]) -> None:
        ...

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        ...


class TfidfRetriever:
    """Dependency-light retriever used as the deterministic fallback."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        doc_freq: dict[str, int] = {}
        tokenized = [normalized_tokens(f"{chunk.title} {chunk.title} {chunk.text}") for chunk in chunks]
        for tokens in tokenized:
            for token in set(tokens):
                doc_freq[token] = doc_freq.get(token, 0) + 1
        n_docs = max(1, len(chunks))
        self.idf = {token: log((1 + n_docs) / (1 + freq)) + 1 for token, freq in doc_freq.items()}
        self.vectors = [self._vectorize_tokens(tokens) for tokens in tokenized]

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_vector = self._vectorize_tokens(normalized_tokens(query))
        scored = [
            RetrievedChunk(chunk=chunk, score=round(_cosine(query_vector, vector), 6), rank=0)
            for chunk, vector in zip(self.chunks, self.vectors)
        ]
        positive = [item for item in scored if item.score > 0]
        ranked = sorted(positive, key=lambda item: (-item.score, item.chunk.chunk_id))[:top_k]
        return [RetrievedChunk(chunk=item.chunk, score=item.score, rank=i + 1) for i, item in enumerate(ranked)]

    def _vectorize_tokens(self, tokens: list[str]) -> dict[str, float]:
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = max(1, len(tokens))
        return {token: (count / total) * self.idf.get(token, 1.0) for token, count in counts.items()}


class DenseRetriever:
    """Optional dense retriever using sentence-transformers and FAISS when installed."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        try:
            import faiss  # type: ignore
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "DenseRetriever requires optional dependencies: sentence-transformers and faiss-cpu"
            ) from exc

        self._faiss = faiss
        self._model = SentenceTransformer(model_name)
        self.chunks: list[Chunk] = []
        self.index_obj = None

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        embeddings = self._model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
        dimension = embeddings.shape[1]
        self.index_obj = self._faiss.IndexFlatIP(dimension)
        self.index_obj.add(embeddings)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        if self.index_obj is None:
            raise RuntimeError("index() must be called before search()")
        query_embedding = self._model.encode([query], normalize_embeddings=True)
        scores, indices = self.index_obj.search(query_embedding, top_k)
        results: list[RetrievedChunk] = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx < 0:
                continue
            results.append(RetrievedChunk(chunk=self.chunks[int(idx)], score=round(float(score), 6), rank=rank))
        return results


def build_retriever(kind: str = "tfidf") -> Retriever:
    if kind == "tfidf":
        return TfidfRetriever()
    if kind == "dense":
        return DenseRetriever()
    raise ValueError(f"Unsupported retriever kind: {kind}")


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(value * right.get(token, 0.0) for token, value in left.items())
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
