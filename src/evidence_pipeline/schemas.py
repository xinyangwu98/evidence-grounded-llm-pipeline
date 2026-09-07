from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Stance = Literal["support", "mixed", "insufficient"]
PolicyLever = Literal[
    "finance",
    "talent",
    "infrastructure",
    "market_access",
    "research",
    "green_transition",
    "data_governance",
]

ALLOWED_STANCES = {"support", "mixed", "insufficient"}
ALLOWED_LEVERS = {
    "finance",
    "talent",
    "infrastructure",
    "market_access",
    "research",
    "green_transition",
    "data_governance",
}


@dataclass(frozen=True)
class EvidenceRef:
    chunk_id: str
    doc_id: str
    title: str
    score: float
    snippet: str


@dataclass(frozen=True)
class ModelFinding:
    model: str
    stance: Stance
    policy_levers: list[PolicyLever]
    entities: list[str]
    confidence: float
    evidence_ids: list[str]
    weight: float = 1.0


@dataclass(frozen=True)
class AggregationSummary:
    models: list[str]
    agreement: float
    vote_margin: float


@dataclass(frozen=True)
class PipelineFinding:
    answer_id: str
    query: str
    stance: Stance
    policy_levers: list[PolicyLever]
    entities: list[str]
    confidence: float
    needs_review: bool
    evidence: list[EvidenceRef]
    aggregation: AggregationSummary

    def to_dict(self) -> dict:
        return asdict(self)


def validate_finding(finding: PipelineFinding) -> list[str]:
    errors: list[str] = []
    if finding.stance not in ALLOWED_STANCES:
        errors.append("stance")
    invalid_levers = [lever for lever in finding.policy_levers if lever not in ALLOWED_LEVERS]
    if invalid_levers:
        errors.append(f"policy_levers: {invalid_levers}")
    if not 0 <= finding.confidence <= 1:
        errors.append("confidence")
    if not finding.evidence:
        errors.append("evidence: at least one evidence item is required")
    missing_ids = [item for item in finding.evidence if not item.chunk_id or not item.doc_id]
    if missing_ids:
        errors.append("evidence: chunk_id and doc_id are required")
    return errors
