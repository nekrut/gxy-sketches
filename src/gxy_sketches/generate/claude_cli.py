"""Backend that shells out to the `claude` CLI in non-interactive mode.

Used when there is no `ANTHROPIC_API_KEY` in the environment — relies on the
existing Claude Code login instead. Mirrors `SketchGenerator.generate()` so
the CLI can pick a backend at runtime with no other code changes.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from ..schema import WorkflowRecord
from .llm import DEFAULT_MODEL, GeneratedSketch, finalize_llm_payload
from .prompts import build_system_prompt, build_user_prompt


class ClaudeCliError(RuntimeError):
    pass


class ClaudeCliGenerator:
    """Same interface as `SketchGenerator`, but uses `claude -p` for auth."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        claude_path: str | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        self._model = model
        self._claude = claude_path or shutil.which("claude") or "claude"
        self._timeout = timeout_seconds
        self._system_prompt = build_system_prompt()

    def generate(self, record: WorkflowRecord) -> GeneratedSketch:
        user_prompt = build_user_prompt(record.metadata_bundle())
        cmd = [
            self._claude,
            "-p",
            "--model",
            self._model,
            "--disallowedTools",
            "*",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--system-prompt",
            self._system_prompt,
        ]
        try:
            proc = subprocess.run(
                cmd,
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise ClaudeCliError(f"claude CLI timed out after {self._timeout}s") from e

        if proc.returncode != 0:
            raise ClaudeCliError(
                f"claude CLI exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
            )

        envelope = _parse_envelope(proc.stdout)
        if envelope.get("is_error"):
            raise ClaudeCliError(f"claude CLI reported error: {envelope}")
        result_text = envelope.get("result")
        if not isinstance(result_text, str):
            raise ClaudeCliError(f"claude CLI envelope missing .result string: {envelope}")

        try:
            return finalize_llm_payload(result_text, record)
        except ValueError as e:
            raise ClaudeCliError(str(e)) from e


def _parse_envelope(stdout: str) -> dict:
    """The `claude -p --output-format json` envelope is a single JSON object on stdout.

    We still walk line-by-line in case the harness prepends noise.
    """
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("type") == "result":
            return data
    try:
        return json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        raise ClaudeCliError(f"could not parse claude CLI envelope: {stdout[:500]}") from e
