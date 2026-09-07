# evidence-grounded-llm-pipeline

Public methodological and engineering demo for an evidence-grounded long-document RAG/LLM pipeline.

Long policy and financial documents often contain indirect, ambiguous, or context-dependent signals that cannot be reliably captured by keyword matching or unconstrained LLM generation. This repository illustrates a modular evidence-grounded pipeline that separates retrieval, constrained semantic interpretation, multi-model aggregation, source-linked verification, and human review.

This demo is intentionally separated from the research data and production prompts in the main repository. It uses only synthetic documents, deterministic browser-side scoring, and simulated model outputs. It is suitable for showing the public method without exposing core data, private prompts, API settings, or model credentials.

The browser demo is intentionally deterministic so it can be inspected without credentials. The Python prototype under `src/` shows the replaceable engineering boundaries used in a real RAG system: chunking, retriever interface, optional dense retrieval, LLM adapter interface, structured schema validation, aggregation, and evaluation metrics.

## Scope

Included:

- chunking
- retrieval
- constrained schema
- multi-model aggregation
- evidence traceability
- evaluation interface
- synthetic/demo data

Excluded:

- production prompts
- API keys or base URLs
- original annual reports, government reports, or policy corpora
- private dictionaries, labels, embeddings, and model outputs
- any claim that the synthetic numbers reproduce the paper's empirical estimates

## Run

### Browser Demo

Open `index.html` directly in a browser.

No server, package installation, model download, or external network access is required.

If hosted with GitHub Pages, the same static files can be served from the repository root.

### Python Prototype

The default Python path uses only the standard library and synthetic data:

```bash
python examples/run_synthetic_pipeline.py --json
python -m unittest discover -s tests
```

Optional dense retrieval can be enabled when local dependencies are installed:

```bash
pip install -r requirements-optional.txt
python examples/run_synthetic_pipeline.py --retriever dense --json
```

The dense retriever uses `sentence-transformers` embeddings with a FAISS inner-product index. If these packages are not installed, the default TF-IDF retriever remains fully runnable.

An OpenAI-compatible adapter is included as an interface example only. It reads `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` from environment variables and is not used by the default demo or tests.

## Architecture

```text
synthetic documents
  -> chunking with stable chunk IDs
  -> retriever interface
       -> TF-IDF fallback
       -> optional sentence-transformers + FAISS dense retriever
  -> LLM adapter interface
       -> local mock adapter by default
       -> OpenAI-compatible adapter example
  -> constrained output schema
  -> weighted multi-model aggregation
  -> evidence-linked finding
  -> evaluation metrics and human review log
```

## Files

- `index.html`: standalone demo UI
- `styles.css`: responsive layout and visual styling
- `app.js`: deterministic demo pipeline logic
- `src/evidence_pipeline/`: replaceable Python RAG/LLM pipeline prototype
- `src/evidence_pipeline/adapters/`: mock and OpenAI-compatible model adapters
- `examples/run_synthetic_pipeline.py`: CLI example on synthetic data
- `tests/test_synthetic_pipeline.py`: standard-library smoke tests
- `data/synthetic_documents.json`: inspectable synthetic corpus mirror
- `schema/demo_output_schema.json`: public constrained output schema
- `assets/pipeline-mark.svg`: small local visual asset for the demo header
- `RELEASE_BOUNDARY.md`: public/private boundary checklist
- `LICENSE`: MIT license

## Method Boundary

The demo presents the pipeline architecture and audit surface only. The labels, documents, model behavior, and evaluation cases are artificial examples designed to show how evidence-linked claims can be generated and reviewed.

This repository does not claim to reproduce any private empirical result. It is a public surrogate that exposes the engineering shape of the pipeline while keeping the original corpus, prompts, dictionaries, embeddings, labels, and model outputs private.
