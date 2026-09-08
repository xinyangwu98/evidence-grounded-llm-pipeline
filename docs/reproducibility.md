# Reproducibility

This public repository provides a sanitized reproducibility map and runnable interface examples.

## Publicly Runnable

The following commands use only synthetic data and require no credentials:

```bash
python examples/run_synthetic_pipeline.py --json
python -m unittest discover -s tests
```

The browser example can be opened directly:

```text
index.html
```

## Optional Dense Retrieval

Dense retrieval can be tested with optional local dependencies:

```bash
pip install -r requirements-optional.txt
python examples/run_synthetic_pipeline.py --retriever dense --json
```

This uses sentence-transformer embeddings and a FAISS inner-product index on the synthetic corpus.

## Private Full Reproduction

Full reproduction of the working paper requires resources not released here:

- original policy and government-report corpora
- licensed firm, city, and industry panel datasets
- full production prompts and extraction guidelines
- private dictionaries, whitelists, and normalization tables
- case-level validation records
- selected thresholds and tuning parameters

The public version preserves the workflow structure, module boundaries, audit logic, and selected aggregate outputs while omitting these materials.
