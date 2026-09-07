from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evidence_pipeline import run_pipeline
from evidence_pipeline.chunking import Document
from evidence_pipeline.evaluator import EvaluationCase, evaluate_finding


DEFAULT_QUERY = "Which policy levers support digital upgrading in manufacturing?"


def load_documents(path: Path) -> list[Document]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Document(**row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the public synthetic evidence-grounded RAG prototype.")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--retriever", choices=["tfidf", "dense"], default="tfidf")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--json", action="store_true", help="Print only the structured finding JSON.")
    args = parser.parse_args()

    documents = load_documents(ROOT / "data" / "synthetic_documents.json")
    finding, validation_errors = run_pipeline(
        query=args.query,
        documents=documents,
        retriever_kind=args.retriever,
        top_k=args.top_k,
    )
    case = EvaluationCase(
        case_id="synthetic-manufacturing",
        query=args.query,
        expected_stance="support",
        expected_levers=["finance", "talent", "infrastructure", "data_governance"],
    )
    evaluation = evaluate_finding(case=case, finding=finding)
    payload = {
        "finding": finding.to_dict(),
        "validation_errors": validation_errors,
        "evaluation": evaluation.__dict__,
        "runtime_boundary": {
            "corpus": "synthetic demo documents only",
            "llm_backend": "mock local adapter by default",
            "secrets_required": False,
        },
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
