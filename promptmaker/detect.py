"""Target-model auto-detection.

Priority (measured 2026-08-11, see LOOP_LOG.md R1):
  1. explicit argument (CLI --model)
  2. transcript JSONL last assistant record's message.model
     (hook input itself carries NO model field — measured)
  3. project .claude/settings.local.json / settings.json "model"
  4. user ~/.claude/settings.json "model"  (may carry suffix like "[1m]")
  5. None (caller falls back to default)
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def normalize_model(model_id: str | None) -> str | None:
    """Map any model id/alias spelling to a profile stem."""
    if not model_id:
        return None
    m = re.sub(r"\[.*?\]", "", model_id).strip().lower()  # strip "[1m]" etc.
    if "fable" in m or "mythos" in m:
        return "fable-5"
    if "opus" in m:
        return "opus-5"
    if "sonnet" in m:
        return "sonnet-5"
    if "haiku" in m:
        return "haiku-4-5"
    return None


def _model_from_transcript(transcript_path: str | None) -> str | None:
    if not transcript_path:
        return None
    p = Path(transcript_path)
    if not p.exists():
        return None
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "assistant":
            model = (d.get("message") or {}).get("model")
            if model:
                return model
    return None


def _model_from_settings(cwd: str | None) -> str | None:
    candidates: list[Path] = []
    if cwd:
        candidates += [
            Path(cwd) / ".claude" / "settings.local.json",
            Path(cwd) / ".claude" / "settings.json",
        ]
    candidates.append(Path.home() / ".claude" / "settings.json")
    for p in candidates:
        try:
            model = json.loads(p.read_text(encoding="utf-8")).get("model")
        except (OSError, json.JSONDecodeError):
            continue
        if model:
            return model
    return None


def detect_model(hook_input: dict | None = None) -> str | None:
    """Return a profile stem (e.g. 'fable-5') or None if undetectable."""
    hook_input = hook_input or {}
    for raw in (
        _model_from_transcript(hook_input.get("transcript_path")),
        _model_from_settings(hook_input.get("cwd")),
    ):
        stem = normalize_model(raw)
        if stem:
            return stem
    return None
