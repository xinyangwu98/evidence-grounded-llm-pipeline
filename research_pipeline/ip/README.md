# Industrial Policy Extraction

This module documents the public structure of the industrial-policy text pipeline.

## Inputs

- central plan documents and policy catalogs
- industry whitelist and synonym resources
- policy-action vocabulary

The public repository does not release the raw corpus, full dictionaries, private prompts, or case-level labels.

## Workflow

1. Parse long policy documents and split them into traceable chunks.
2. Retrieve high-recall candidate chunks for each industry and policy-action category.
3. Run constrained multi-model semantic labeling.
4. Normalize extracted industry labels to controlled categories.
5. Aggregate across model runs and flag disagreement.
6. Construct plan-period policy-action intensity and policy-by-industry matrices.

## Public Outputs

The public README includes selected aggregate policy-by-industry and policy-lever-by-industry heatmaps. They demonstrate the final measurement layer without exposing source chunks or prompt text.

The policy-lever intensity figure can be rebuilt from a sanitized public matrix:

```bash
python research_pipeline/ip/plot_policy_lever_heatmap.py
```
