from __future__ import annotations

from dataclasses import dataclass

from .schemas import PipelineFinding


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    query: str
    expected_stance: str
    expected_levers: list[str]


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    stance_match: bool
    lever_precision: float
    lever_recall: float
    lever_f1: float
    evidence_coverage: float


def evaluate_finding(case: EvaluationCase, finding: PipelineFinding) -> EvaluationResult:
    predicted = set(finding.policy_levers)
    expected = set(case.expected_levers)
    true_positive = len(predicted & expected)
    precision = true_positive / len(predicted) if predicted else float(not expected)
    recall = true_positive / len(expected) if expected else float(not predicted)
    f1 = 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)
    evidence_coverage = sum(1 for item in finding.evidence if item.chunk_id and item.snippet) / max(1, len(finding.evidence))
    return EvaluationResult(
        case_id=case.case_id,
        stance_match=finding.stance == case.expected_stance,
        lever_precision=round(precision, 3),
        lever_recall=round(recall, 3),
        lever_f1=round(f1, 3),
        evidence_coverage=round(evidence_coverage, 3),
    )
