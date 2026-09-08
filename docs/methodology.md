# Methodology

This public note describes the research workflow at a level suitable for inspection without releasing private materials.

## Problem

The project measures how central industrial-policy encouragement and local government industrial narratives are reflected in firm-level digital transformation outcomes. The key measurement problem is that the relevant signals are distributed across long documents, often expressed indirectly, and not reliably captured by raw keyword counts.

## Design Principles

- separate retrieval from interpretation
- force structured outputs rather than free-form summaries
- attach every extracted claim to source evidence
- aggregate across model runs and flag disagreement
- preserve a human review surface for ambiguous cases
- connect text-derived measures to downstream econometric validation

## Policy Text Layer

Central policy documents are parsed into chunks with stable identifiers. Candidate industry mentions are retrieved with high-recall rules and model-assisted interpretation. Outputs are normalized through controlled industry mappings and aggregated into plan-period policy indicators.

## Local Report Layer

Government work reports are filtered through a high-recall neural classifier before structured extraction. The LLM extraction step targets report-level fields such as traditional advantage industries, transition needs, backward/exit sectors, and weak industries. Evidence fallback logic keeps extracted labels traceable to candidate spans.

## Network Layer

Normalized local industry labels are transformed into a PPMI co-occurrence network. Community detection produces interpretable industrial narrative communities. City-year measures include narrative entropy, dominant community, and dominant-community share.

## Evaluation Layer

Text-derived policy and narrative indicators are merged with firm, city, and industry panel variables. Downstream tests include baseline regressions, mechanism checks, heterogeneity analysis, and robustness exercises.
