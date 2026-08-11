"""promptmaker CLI.

Usage:
    promptmaker "대충 쓴 요청" --model fable-5
    echo "요청" | promptmaker --model opus-5
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .engine import DEFAULT_REWRITER_MODEL, MODEL_ALIASES, rewrite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="promptmaker",
        description="대충 쓴 요청을 대상 Claude 모델에 맞는 프롬프트로 재작성합니다.",
    )
    parser.add_argument("raw", nargs="?", help="원본 프롬프트 (생략 시 stdin에서 읽음)")
    parser.add_argument(
        "-m", "--model", default="fable-5",
        help=f"대상 모델 (기본: fable-5; 허용: {sorted(set(MODEL_ALIASES.values()))})",
    )
    parser.add_argument(
        "--rewriter-model", default=DEFAULT_REWRITER_MODEL,
        help=f"재작성에 사용할 모델 (기본: {DEFAULT_REWRITER_MODEL})",
    )
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    raw = args.raw if args.raw is not None else sys.stdin.read()
    if not raw.strip():
        parser.error("빈 프롬프트입니다.")

    result = rewrite(raw, args.model, rewriter_model=args.rewriter_model)

    if args.json:
        print(json.dumps({
            "intent": result.intent,
            "target_model": result.target_model,
            "rewritten_prompt": result.rewritten_prompt,
            "changes": result.changes,
        }, ensure_ascii=False, indent=2))
    else:
        print(result.rewritten_prompt)
        print("\n--- 변경 요약 ---", file=sys.stderr)
        for c in result.changes:
            print(f"• {c}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
