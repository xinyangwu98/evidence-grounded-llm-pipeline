from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import re


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    year: int
    source_type: str
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    year: int
    source_type: str
    text: str
    token_count: int


def tokenize(text: str) -> list[str]:
    return [token for token in re.sub(r"[^A-Za-z0-9_ ]+", " ", text.lower()).split() if len(token) > 2]


def normalize_token(token: str) -> str:
    """Small public-demo normalizer, not a substitute for a production tokenizer."""
    for suffix in ("ers", "ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            return token[: -len(suffix)]
    return token


def normalized_tokens(text: str) -> list[str]:
    return [normalize_token(token) for token in tokenize(text)]


def chunk_documents(
    documents: Iterable[Document],
    max_tokens: int = 80,
    overlap_tokens: int = 12,
) -> list[Chunk]:
    """Split documents into overlapping word chunks with stable evidence IDs."""
    if max_tokens < 8:
        raise ValueError("max_tokens must be at least 8")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be non-negative and smaller than max_tokens")

    chunks: list[Chunk] = []
    for doc in documents:
        words = tokenize(doc.text)
        if not words:
            continue
        start = 0
        chunk_no = 1
        while start < len(words):
            window = words[start : start + max_tokens]
            chunk_text = " ".join(window)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}-C{chunk_no:03d}",
                    doc_id=doc.doc_id,
                    title=doc.title,
                    year=doc.year,
                    source_type=doc.source_type,
                    text=chunk_text,
                    token_count=len(window),
                )
            )
            if start + max_tokens >= len(words):
                break
            start += max_tokens - overlap_tokens
            chunk_no += 1
    return chunks
