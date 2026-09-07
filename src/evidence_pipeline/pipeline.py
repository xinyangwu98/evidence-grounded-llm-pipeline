from __future__ import annotations

from .adapters.mock_llm import MockLLMAdapter
from .aggregator import aggregate_findings
from .chunking import Document, chunk_documents
from .retriever import build_retriever
from .schemas import PipelineFinding, validate_finding


def run_pipeline(
    query: str,
    documents: list[Document],
    retriever_kind: str = "tfidf",
    top_k: int = 5,
    chunk_tokens: int = 80,
    overlap_tokens: int = 12,
) -> tuple[PipelineFinding, list[str]]:
    chunks = chunk_documents(documents, max_tokens=chunk_tokens, overlap_tokens=overlap_tokens)
    retriever = build_retriever(retriever_kind)
    retriever.index(chunks)
    retrieved = retriever.search(query, top_k=top_k)
    adapters = [
        MockLLMAdapter(name="mock-extractive", weight=0.38, strictness=1),
        MockLLMAdapter(name="mock-semantic", weight=0.34, strictness=1),
        MockLLMAdapter(name="mock-skeptical", weight=0.28, strictness=2),
    ]
    model_findings = [adapter.extract(query=query, retrieved=retrieved) for adapter in adapters]
    finding = aggregate_findings(query=query, retrieved=retrieved, model_findings=model_findings)
    return finding, validate_finding(finding)
