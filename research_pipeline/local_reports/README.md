# Local Government Report Pipeline

This module documents the public structure of the local government work report extraction pipeline.

## Inputs

- prefecture-level government work reports
- human-labeled training examples
- structured extraction guidelines
- report-level recall outputs

The public repository does not release raw reports, full guidelines, production prompts, or case-level validation records.

## Workflow

1. Build human-labeled training data for high-recall filtering.
2. Train and apply a MacBERT-style recall model to find candidate report spans.
3. Construct a report-level recall corpus.
4. Run structured LLM extraction with constrained output fields.
5. Apply evidence fallback and label normalization.
6. Export audit tables for missingness, recall quality, disagreement, and noisy labels.

## Output Fields

The private workflow extracts structured fields related to local industrial narratives, including traditional advantage industries, transition needs, backward/exit sectors, and weak industries.
