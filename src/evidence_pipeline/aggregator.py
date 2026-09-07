from __future__ import annotations

from collections import Counter, defaultdict
from time import time

from .retriever import RetrievedChunk
from .schemas import AggregationSummary, EvidenceRef, ModelFinding, PipelineFinding, PolicyLever, Stance


def aggregate_findings(query: str, retrieved: list[RetrievedChunk], model_findings: list[ModelFinding]) -> PipelineFinding:
    if not model_findings:
        raise ValueError("At least one model finding is required")

    stance_weights: defaultdict[Stance, float] = defaultdict(float)
    lever_weights: defaultdict[PolicyLever, float] = defaultdict(float)
    entity_weights: Counter[str] = Counter()
    total_weight = sum(item.weight for item in model_findings)

    for finding in model_findings:
        stance_weights[finding.stance] += finding.weight
        for lever in finding.policy_levers:
            lever_weights[lever] += finding.weight
        for entity in finding.entities:
            entity_weights[entity] += finding.weight

    sorted_stances = sorted(stance_weights.items(), key=lambda item: (-item[1], item[0]))
    stance = sorted_stances[0][0]
    agreement = sorted_stances[0][1] / total_weight
    runner_up = sorted_stances[1][1] / total_weight if len(sorted_stances) > 1 else 0.0
    vote_margin = agreement - runner_up

    policy_levers = [
        lever
        for lever, weight in sorted(lever_weights.items(), key=lambda item: (-item[1], item[0]))
        if weight / total_weight >= 0.34 and stance != "insufficient"
    ]
    entities = [entity for entity, _ in entity_weights.most_common(8)]
    weighted_confidence = sum(item.confidence * item.weight for item in model_findings) / total_weight
    disagreement_penalty = 1 - min(0.35, max(0.0, 0.67 - agreement))
    confidence = round(max(0.0, min(1.0, weighted_confidence * disagreement_penalty)), 3)

    evidence = [
        EvidenceRef(
            chunk_id=item.chunk.chunk_id,
            doc_id=item.chunk.doc_id,
            title=item.chunk.title,
            score=item.score,
            snippet=item.chunk.text,
        )
        for item in retrieved
    ]
    needs_review = agreement < 0.67 or stance == "mixed" or not policy_levers

    return PipelineFinding(
        answer_id=f"DEMO-{int(time() * 1000)}",
        query=query,
        stance=stance,
        policy_levers=policy_levers,
        entities=entities,
        confidence=confidence,
        needs_review=needs_review,
        evidence=evidence,
        aggregation=AggregationSummary(
            models=[item.model for item in model_findings],
            agreement=round(agreement, 3),
            vote_margin=round(vote_margin, 3),
        ),
    )
