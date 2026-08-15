#!/usr/bin/env python3
"""Backend for the /pm slash command.

Detects the current session's model (transcript-based detection is not
available here, so settings-based detection is used) and prints the
rewrite as JSON for the command template to consume.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prompt_tailor.detect import detect_model  # noqa: E402
from prompt_tailor.engine import rewrite  # noqa: E402


def main() -> int:
    raw = " ".join(sys.argv[1:]).strip()
    if not raw:
        print(json.dumps({"error": "빈 프롬프트"}, ensure_ascii=False))
        return 0
    log_path = REPO_ROOT / "runs" / "pm_command.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["PROMPT_TAILOR_ACTIVE"] = "1"  # recursion guard for the hook
    try:
        target = detect_model({"cwd": os.getcwd()}) or "fable-5"
        # Interactive path — the user waits inline. Condensed meta measured
        # 14.5-21.9s vs full meta avg 41.4s (LOOP_LOG R7); cap each attempt at 60s.
        r = rewrite(raw, target, retries=1, timeout=60, concise=True)
        print(json.dumps({
            "target_model": r.target_model,
            "rewritten_prompt": r.rewritten_prompt,
            "changes": r.changes,
        }, ensure_ascii=False, indent=2))
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} ok target={target} raw={raw[:60]!r}\n")
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} ERROR {type(e).__name__}: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
