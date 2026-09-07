# evidence-grounded-llm-pipeline

Methodological demo for an evidence-grounded LLM pipeline.

This demo is intentionally separated from the research data and production prompts in the main repository. It uses only synthetic documents, deterministic browser-side scoring, and simulated model outputs. It is suitable for showing the public method without exposing core data, private prompts, API settings, or model credentials.

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

Open `index.html` directly in a browser.

No server, package installation, model download, or external network access is required.

If hosted with GitHub Pages, the same static files can be served from the repository root.

## Files

- `index.html`: standalone demo UI
- `styles.css`: responsive layout and visual styling
- `app.js`: deterministic demo pipeline logic
- `data/synthetic_documents.json`: inspectable synthetic corpus mirror
- `schema/demo_output_schema.json`: public constrained output schema
- `assets/pipeline-mark.svg`: small local visual asset for the demo header
- `RELEASE_BOUNDARY.md`: public/private boundary checklist
- `LICENSE`: MIT license

## Method Boundary

The demo presents the pipeline architecture and audit surface only. The labels, documents, model behavior, and evaluation cases are artificial examples designed to show how evidence-linked claims can be generated and reviewed.
