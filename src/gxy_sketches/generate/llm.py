"""Anthropic client wrapper with prompt caching on the system prompt.

Prompt caching is mandatory per project convention — the system prompt is
stable across every pipeline, so caching it drops per-pipeline cost ~10x on
large batches. See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic

from ..schema import SketchFrontmatter, WorkflowRecord
from .prompts import build_system_prompt, build_user_prompt


DEFAULT_MODEL = os.environ.get("GXY_SKETCHES_MODEL", "claude-opus-4-6")


@dataclass
class GeneratedSketch:
    frontmatter: SketchFrontmatter
    body: str


class SketchGenerator:
    """Turns a `WorkflowRecord` into a validated `GeneratedSketch`."""

    def __init__(
        self,
        client: Anthropic | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 4096,
    ) -> None:
        self._client = client or Anthropic()
        self._model = model
        self._max_tokens = max_tokens
        self._system_prompt = build_system_prompt()

    def generate(self, record: WorkflowRecord) -> GeneratedSketch:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": self._system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(record.metadata_bundle()),
                }
            ],
        )
        text = _extract_text(response)
        payload = _parse_json_object(text)
        fm_data = payload.get("frontmatter")
        body = payload.get("body")
        if not isinstance(fm_data, dict) or not isinstance(body, str):
            raise ValueError(
                f"LLM response did not match expected shape: {text[:500]}"
            )

        # Back-fill source fields if the model omitted them — they're authoritative
        # from the ingestor, not the LLM.
        fm_data.setdefault("source", {})
        fm_data["source"].setdefault("ecosystem", record.ecosystem)
        fm_data["source"].setdefault("workflow", record.display_name)
        fm_data["source"].setdefault("url", record.source_url)
        if record.version:
            fm_data["source"].setdefault("version", record.version)
        if record.license:
            fm_data["source"].setdefault("license", record.license)

        frontmatter = SketchFrontmatter.model_validate(fm_data)
        return GeneratedSketch(frontmatter=frontmatter, body=body)


def _extract_text(response: Any) -> str:
    parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


def _parse_json_object(text: str) -> dict:
    """Parse the JSON object the model was instructed to emit.

    Falls back to finding the first `{` ... matching `}` window if the model
    wrapped the payload in prose despite instructions.
    """
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in LLM response: {text[:500]}")
    depth = 0
    for i in range(start, len(stripped)):
        ch = stripped[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stripped[start : i + 1])
    raise ValueError(f"Unbalanced JSON in LLM response: {text[:500]}")
