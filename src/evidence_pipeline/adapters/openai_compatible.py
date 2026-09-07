from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..retriever import RetrievedChunk
from ..schemas import ALLOWED_LEVERS, ALLOWED_STANCES, ModelFinding, PolicyLever, Stance


class OpenAICompatibleAdapter:
    """Minimal OpenAI-compatible chat completions adapter.

    The adapter reads configuration from environment variables and is not used by
    the default demo. It exists to show how a real model backend can be swapped in
    without committing credentials or private prompts.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        weight: float = 1.0,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = os.getenv(api_key_env)
        self.weight = weight

    def extract(self, query: str, retrieved: list[RetrievedChunk]) -> ModelFinding:
        if not self.api_key:
            raise RuntimeError("Missing API key. Set OPENAI_API_KEY or use MockLLMAdapter.")

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return compact JSON only. Use the provided synthetic evidence IDs. "
                        "Allowed stance values: support, mixed, insufficient."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "query": query,
                            "allowed_policy_levers": sorted(ALLOWED_LEVERS),
                            "evidence": [
                                {
                                    "chunk_id": item.chunk.chunk_id,
                                    "doc_id": item.chunk.doc_id,
                                    "title": item.chunk.title,
                                    "score": item.score,
                                    "text": item.chunk.text,
                                }
                                for item in retrieved
                            ],
                            "required_json_fields": [
                                "stance",
                                "policy_levers",
                                "entities",
                                "confidence",
                                "evidence_ids",
                            ],
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc

        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return self._coerce(parsed=parsed, retrieved=retrieved)

    def _coerce(self, parsed: dict, retrieved: list[RetrievedChunk]) -> ModelFinding:
        stance = parsed.get("stance", "insufficient")
        if stance not in ALLOWED_STANCES:
            stance = "insufficient"
        policy_levers = [
            lever for lever in parsed.get("policy_levers", []) if lever in ALLOWED_LEVERS
        ]
        evidence_ids = [
            item for item in parsed.get("evidence_ids", []) if item in {hit.chunk.chunk_id for hit in retrieved}
        ] or [item.chunk.chunk_id for item in retrieved[:1]]
        confidence = float(parsed.get("confidence", 0.5))
        return ModelFinding(
            model=self.model,
            stance=stance,  # type: ignore[arg-type]
            policy_levers=policy_levers,  # type: ignore[list-item]
            entities=[str(item) for item in parsed.get("entities", [])],
            confidence=max(0.0, min(1.0, confidence)),
            evidence_ids=evidence_ids,
            weight=self.weight,
        )
