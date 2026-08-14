#!/usr/bin/env python3
"""PromptMaker UserPromptSubmit hook (auto mode, opt-in).

Reads hook input JSON on stdin. If the prompt looks like a rough request,
rewrites it for the detected target model and injects the rewrite as
additionalContext (the hook API cannot replace the prompt itself).

Skip conditions (no intervention, exit 0 with no output):
  - prompt starts with "/" (slash command)
  - prompt contains "#raw" (explicit opt-out tag)
  - prompt too short (< 6 estimated tokens) — greetings, short commands
    (was < 10; lowered per user-approved gate amendment, GATES.md 2026-08-12)
  - prompt already detailed (> 800 chars) — user wrote a real prompt
Fail-open: any internal error -> no output, logged to runs/hook.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # PromptMaker/
sys.path.insert(0, str(REPO_ROOT))

LOG_PATH = REPO_ROOT / "runs" / "hook.log"
DEFAULT_TARGET = "fable-5"


def log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def estimate_tokens(text: str) -> int:
    """Rough token estimate good enough for a skip threshold.
    Korean ~2 chars/token, English ~4 chars/token — use chars/2 when the
    text is mostly non-ASCII (Korean), chars/4 otherwise; floor at word count."""
    non_ascii = sum(1 for c in text if ord(c) > 127)
    divisor = 2 if non_ascii > len(text) / 2 else 4
    return max(len(text.split()), len(text) // divisor)


def should_skip(prompt: str) -> str | None:
    p = prompt.strip()
    if p.startswith("/"):
        return "slash-command"
    if re.search(r"(?:^|\s)#raw\b", p):
        return "raw-tag"
    if estimate_tokens(p) < 6:
        return "too-short"
    if len(p) > 800:
        return "already-detailed"
    return None


def main() -> int:
    t0 = time.time()
    # Recursion guard: the rewrite itself spawns `claude -p`, which inherits
    # this project's settings and would re-trigger this hook (measured, P3).
    if os.environ.get("PROMPTMAKER_ACTIVE"):
        log("skip (recursion-guard)")
        return 0
    os.environ["PROMPTMAKER_ACTIVE"] = "1"

    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        log("ERROR: invalid hook input JSON")
        return 0

    prompt = hook_input.get("prompt", "")
    reason = should_skip(prompt)
    if reason:
        log(f"skip ({reason}): {prompt[:60]!r}")
        return 0

    try:
        from promptmaker.detect import detect_model
        from promptmaker.engine import rewrite

        target = detect_model(hook_input) or DEFAULT_TARGET
        # gate: 30s. intent_routing=False — the intent block pushed 2/6 calls
        # past the 28s cap in A/B; the hook keeps the lean meta (LOOP_LOG R22).
        result = rewrite(prompt, target, retries=0, timeout=28, concise=True, intent_routing=False)
        context = (
            "[PromptMaker] 사용자의 요청을 대상 모델에 맞게 재해석했다. "
            "원문 의도를 유지하되 아래 재작성을 작업 지침으로 삼아라. "
            "[가정]으로 표시된 부분은 단정하지 말고 작업 중 확인하라.\n"
            f"<재작성 대상모델={target}>\n{result.rewritten_prompt}\n</재작성>"
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            },
            "suppressOutput": True,
        }, ensure_ascii=False))
        log(f"rewrote ({target}, {time.time() - t0:.1f}s): {prompt[:60]!r}")
    except Exception as e:  # fail-open: never block the user's prompt
        log(f"ERROR ({time.time() - t0:.1f}s): {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
