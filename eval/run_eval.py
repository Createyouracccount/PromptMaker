"""Golden-set evaluation for promptmaker.

For each golden item:
  1. rewrite raw -> fable-5-targeted prompt
  2. judge: is the rewrite clearly better than raw? (rubric, JSON verdict)
For a subset (diff check):
  3. rewrite same raw with haiku-4-5 profile, judge whether the two rewrites
     differ in ways consistent with their profiles.

Writes results to eval/results.json and prints a summary.

Usage: python3 eval/run_eval.py [--limit N] [--workers K]
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from promptmaker.engine import call_claude, parse_json_output, rewrite  # noqa: E402

JUDGE_MODEL = "claude-sonnet-5"
DIFF_ITEMS = {"g01", "g05", "g09", "g18", "g19"}  # profile-difference check subset

JUDGE_PROMPT = """\
당신은 프롬프트 품질 심판이다. Claude Code(코딩 에이전트)에 입력될 프롬프트로서
원본(RAW)과 재작성본(REWRITTEN)을 비교 평가하라.

<RAW>
{raw}
</RAW>

<REWRITTEN>
{rewritten}
</REWRITTEN>

평가 기준 (각 1~5점):
- clarity: 목표·범위·완료기준이 명확한가
- fidelity: 원문 의도를 왜곡하거나 없는 사실을 지어내지 않았는가 (가정은 [가정] 표시 시 감점 없음)
- actionability: 에이전트가 되묻지 않고 바로 착수할 수 있는가

verdict: 재작성본이 원본보다 "명확히 낫다"(better) / "비슷하다"(same) / "더 나쁘다"(worse)

아래 JSON만 출력하라:
{{"clarity": n, "fidelity": n, "actionability": n, "verdict": "better|same|worse", "reason": "한 문장"}}
"""

DIFF_JUDGE_PROMPT = """\
같은 원본 요청을 두 가지 모델 프로필로 재작성했다.
프로필 A(fable-5): 단계 나열 금지, 목표·제약·의도 중심, 자율성 부여.
프로필 B(haiku-4-5): 작업을 작게 분해, 번호 매긴 단계, 출력 형식 지정, 판단 여지 축소.

<원본>
{raw}
</원본>

<재작성_A_fable5>
{a}
</재작성_A_fable5>

<재작성_B_haiku45>
{b}
</재작성_B_haiku45>

질문: 두 재작성본이 각자의 프로필 특성을 실제로 반영하며 유의미하게 다른가?
- a_matches_profile: A가 fable-5 프로필 특성(목표 중심, 단계 나열 없음)을 보이는가 (true/false)
- b_matches_profile: B가 haiku-4-5 프로필 특성(명시적 단계/형식)을 보이는가 (true/false)
- meaningfully_different: 표면 어휘 차이가 아니라 구조적으로 다른가 (true/false)

아래 JSON만 출력하라:
{{"a_matches_profile": bool, "b_matches_profile": bool, "meaningfully_different": bool, "reason": "한 문장"}}
"""


def _call_judge(prompt: str, required_keys: tuple[str, ...], retries: int = 2) -> dict:
    """Judge call with retry on truncated/invalid output or missing fields
    (both failure modes observed in Phase 1: g19 truncation, g02 missing verdict)."""
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            data = parse_json_output(call_claude(prompt, JUDGE_MODEL))
            missing = [k for k in required_keys if k not in data]
            if missing:
                raise ValueError(f"judge output missing keys: {missing}")
            return data
        except (ValueError, RuntimeError) as e:
            last_err = e
    raise RuntimeError(f"judge failed after {retries + 1} attempts: {last_err}")


def judge(raw: str, rewritten: str) -> dict:
    return _call_judge(
        JUDGE_PROMPT.format(raw=raw, rewritten=rewritten),
        required_keys=("clarity", "fidelity", "actionability", "verdict"),
    )


def judge_diff(raw: str, a: str, b: str) -> dict:
    return _call_judge(
        DIFF_JUDGE_PROMPT.format(raw=raw, a=a, b=b),
        required_keys=("a_matches_profile", "b_matches_profile", "meaningfully_different"),
    )


def process_item(item: dict) -> dict:
    rec: dict = {"id": item["id"], "raw": item["raw"]}
    try:
        r_fable = rewrite(item["raw"], "fable-5")
        rec["rewritten_fable5"] = r_fable.rewritten_prompt
        rec["intent"] = r_fable.intent
        rec["changes"] = r_fable.changes
        rec["judge"] = judge(item["raw"], r_fable.rewritten_prompt)

        if item["id"] in DIFF_ITEMS:
            r_haiku = rewrite(item["raw"], "haiku-4-5")
            rec["rewritten_haiku45"] = r_haiku.rewritten_prompt
            rec["diff_judge"] = judge_diff(
                item["raw"], r_fable.rewritten_prompt, r_haiku.rewritten_prompt
            )
    except Exception:
        rec["error"] = traceback.format_exc(limit=3)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    items = [json.loads(line) for line in (ROOT / "golden" / "golden.jsonl").open(encoding="utf-8")]
    if args.limit:
        items = items[: args.limit]

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(process_item, items))

    out_path = ROOT / "eval" / "results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = [r for r in results if "judge" in r]
    errors = [r for r in results if "error" in r]
    better = [r for r in ok if r["judge"].get("verdict") == "better"]
    same = [r for r in ok if r["judge"].get("verdict") == "same"]
    worse = [r for r in ok if r["judge"].get("verdict") == "worse"]
    diffs = [r for r in ok if "diff_judge" in r]
    diff_pass = [
        r for r in diffs
        if r["diff_judge"].get("a_matches_profile")
        and r["diff_judge"].get("b_matches_profile")
        and r["diff_judge"].get("meaningfully_different")
    ]

    print(f"total={len(results)} ok={len(ok)} errors={len(errors)}")
    print(f"verdict: better={len(better)} same={len(same)} worse={len(worse)}")
    if ok:
        avg = {k: sum(r["judge"].get(k, 0) for r in ok) / len(ok)
               for k in ("clarity", "fidelity", "actionability")}
        print(f"avg scores: {avg}")
    print(f"profile-diff check: {len(diff_pass)}/{len(diffs)} pass")
    for r in errors:
        print(f"ERROR {r['id']}: {r['error'].splitlines()[-1]}")
    print(f"results written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
