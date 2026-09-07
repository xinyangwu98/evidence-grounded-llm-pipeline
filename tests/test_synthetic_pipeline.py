from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evidence_pipeline import run_pipeline
from evidence_pipeline.chunking import Document, chunk_documents
from evidence_pipeline.evaluator import EvaluationCase, evaluate_finding


class SyntheticPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        rows = json.loads((ROOT / "data" / "synthetic_documents.json").read_text(encoding="utf-8"))
        self.documents = [Document(**row) for row in rows]

    def test_chunking_produces_stable_evidence_ids(self) -> None:
        chunks = chunk_documents(self.documents, max_tokens=32, overlap_tokens=6)
        self.assertGreater(len(chunks), len(self.documents))
        self.assertRegex(chunks[0].chunk_id, r"^SYN-[A-Z]+-\d{3}-C\d{3}$")

    def test_pipeline_returns_schema_valid_evidence_grounded_finding(self) -> None:
        finding, errors = run_pipeline(
            query="Which policy levers support digital upgrading in manufacturing?",
            documents=self.documents,
            top_k=4,
            chunk_tokens=48,
        )
        self.assertEqual(errors, [])
        self.assertGreater(len(finding.evidence), 0)
        self.assertIn(finding.stance, {"support", "mixed", "insufficient"})
        self.assertGreaterEqual(finding.aggregation.agreement, 0)

    def test_evaluator_reports_metrics(self) -> None:
        finding, _ = run_pipeline(
            query="Which policy levers support digital upgrading in manufacturing?",
            documents=self.documents,
            top_k=4,
            chunk_tokens=48,
        )
        case = EvaluationCase(
            case_id="manufacturing",
            query=finding.query,
            expected_stance="support",
            expected_levers=["finance", "talent", "infrastructure", "data_governance"],
        )
        result = evaluate_finding(case, finding)
        self.assertGreaterEqual(result.lever_f1, 0)
        self.assertLessEqual(result.lever_f1, 1)
        self.assertEqual(result.evidence_coverage, 1.0)


if __name__ == "__main__":
    unittest.main()
