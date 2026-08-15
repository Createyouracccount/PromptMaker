"""Pilot: does the rewritten prompt produce a BETTER TASK RESULT, not just a
better-looking prompt?

Design (addresses the R23 methodology obligations):
  - Self-contained generation tasks executable headless (no repo context).
  - Executor = haiku (the model the rewrite targets).
  - Generation order alternates by item parity; presentation position (A/B)
    alternates on the OPPOSITE parity, so position and generation order are
    not confounded. Assignment recorded for de-blinding.
  - Judge (sonnet) sees only the task request and the two RESULTS.
  - Judge raw outputs preserved.

This is a pilot (n=3): it produces the first outcome evidence, not proof.

Usage: python3 eval/ab_task_outcome.py
Writes eval/ab_task_outcome_results.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from prompt_tailor.engine import call_claude, parse_json_output, rewrite  # noqa: E402

TASKS = [
    "파이썬으로 퀵정렬 함수 하나 짜줘 간단 설명도",
    "CSV 파일에서 중복 행 제거하는 스크립트 만들어줘",
    "이메일 형식 검증하는 함수 자바스크립트로 만들어줘",
]
EXECUTOR = "claude-haiku-4-5"
JUDGE = "claude-sonnet-5"

RESULT_JUDGE = """당신은 결과물 품질 심판이다. 사용자가 아래 요청을 했고, 두 결과물 A와 B를 받았다.
어느 결과물이 사용자의 실제 필요를 더 잘 충족하는지 평가하라.

<사용자_요청>
{task}
</사용자_요청>

<결과물_A>
{a}
</결과물_A>

<결과물_B>
{b}
</결과물_B>

기준: 정확성(코드가 실제로 동작하고 엣지케이스를 다루는가), 완결성(바로 쓸 수 있는가),
적합성(요청 범위를 벗어난 과잉이나 미달이 없는가).
verdict: "A" | "B" | "tie"

JSON만 출력:
{{"a_score": n, "b_score": n, "verdict": "A|B|tie", "reason": "한 문장"}}
"""


def execute(prompt: str) -> tuple[str, float]:
    t0 = time.time()
    out = call_claude(prompt, EXECUTOR, timeout=180)
    return out, round(time.time() - t0, 1)


def main() -> int:
    results = []
    for i, task in enumerate(TASKS):
        rec: dict = {"task": task}
        try:
            r = rewrite(task, "haiku-4-5", concise=True, retries=1, timeout=90)
            rec["rewritten_prompt"] = r.rewritten_prompt

            # generation order alternates by parity
            gen_order = ["raw", "rewritten"] if i % 2 == 0 else ["rewritten", "raw"]
            for arm in gen_order:
                prompt = task if arm == "raw" else r.rewritten_prompt
                out, dt = execute(prompt)
                rec[arm] = {"output": out, "wall_s": dt}

            # presentation position alternates on the OPPOSITE parity
            a_arm, b_arm = ("rewritten", "raw") if i % 2 == 0 else ("raw", "rewritten")
            rec["assignment"] = {"A": a_arm, "B": b_arm}
            judge_out = call_claude(
                RESULT_JUDGE.format(task=task, a=rec[a_arm]["output"], b=rec[b_arm]["output"]),
                JUDGE, timeout=120)
            rec["judge_raw"] = judge_out
            rec["judge"] = parse_json_output(judge_out)
            v = rec["judge"]["verdict"]
            rec["winner"] = "tie" if v == "tie" else rec["assignment"].get(v, "?")
            print(f"[{i}] winner={rec['winner']} | {rec['judge'].get('reason', '')[:110]}")
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            print(f"[{i}] ERROR {rec['error']}")
        results.append(rec)

    out_path = ROOT / "eval" / "ab_task_outcome_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    wins = {"raw": 0, "rewritten": 0, "tie": 0}
    for rec in results:
        if "winner" in rec:
            wins[rec["winner"]] += 1
    print(f"\ntask-outcome wins: {wins}")
    print(f"written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
