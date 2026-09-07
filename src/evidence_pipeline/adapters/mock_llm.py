from __future__ import annotations

from collections import Counter

from ..retriever import RetrievedChunk
from ..schemas import ModelFinding, PolicyLever, Stance


LEVER_TERMS: dict[PolicyLever, tuple[str, ...]] = {
    "finance": ("grant", "grants", "funding", "financing", "subsidy", "tax"),
    "talent": ("worker", "retraining", "training", "voucher", "talent", "operator"),
    "infrastructure": ("infrastructure", "broadband", "platform", "lab", "testing", "network"),
    "market_access": ("procurement", "market", "access", "supplier", "matching", "channel"),
    "research": ("research", "university", "lab", "pilot", "collaboration"),
    "green_transition": ("green", "environmental", "recycling", "water", "saving", "compliance"),
    "data_governance": ("data", "standards", "interfaces", "governance", "traceability", "dashboard"),
}

ENTITY_TERMS = (
    "robotics",
    "manufacturing",
    "warehousing",
    "logistics",
    "battery",
    "textile",
    "agricultural",
    "sensor",
    "port",
    "cloud",
)


class MockLLMAdapter:
    """Local deterministic adapter that preserves the LLM boundary without calling a model."""

    def __init__(self, name: str = "mock-llm", weight: float = 1.0, strictness: int = 1) -> None:
        self.name = name
        self.weight = weight
        self.strictness = strictness

    def extract(self, query: str, retrieved: list[RetrievedChunk]) -> ModelFinding:
        evidence_text = " ".join(item.chunk.text for item in retrieved).lower()
        lever_hits: Counter[PolicyLever] = Counter()
        for lever, terms in LEVER_TERMS.items():
            lever_hits[lever] = sum(1 for term in terms if term in evidence_text)
        policy_levers = [
            lever for lever, hits in lever_hits.most_common() if hits >= self.strictness
        ]
        entities = [term for term in ENTITY_TERMS if term in evidence_text]
        stance = self._stance(query=query, evidence_text=evidence_text, retrieved=retrieved)
        confidence = self._confidence(retrieved=retrieved, policy_levers=policy_levers, stance=stance)
        return ModelFinding(
            model=self.name,
            stance=stance,
            policy_levers=policy_levers,
            entities=entities,
            confidence=confidence,
            evidence_ids=[item.chunk.chunk_id for item in retrieved[:3]],
            weight=self.weight,
        )

    def _stance(self, query: str, evidence_text: str, retrieved: list[RetrievedChunk]) -> Stance:
        query_lower = query.lower()
        if "generic" in query_lower or "alone" in query_lower:
            return "insufficient"
        uncertainty = any(signal in evidence_text for signal in ("does not", "uncertain", "not a central"))
        if uncertainty and self.strictness >= 2:
            return "mixed"
        if sum(item.score for item in retrieved[:3]) <= 0:
            return "insufficient"
        return "support"

    def _confidence(self, retrieved: list[RetrievedChunk], policy_levers: list[PolicyLever], stance: Stance) -> float:
        retrieval_signal = sum(item.score for item in retrieved[:3]) / max(1, len(retrieved[:3]))
        base = 0.45 + min(0.3, retrieval_signal) + min(0.2, 0.04 * len(policy_levers))
        if stance == "mixed":
            base -= 0.08
        if stance == "insufficient":
            base = min(base, 0.55)
        return round(max(0.05, min(0.95, base)), 3)
