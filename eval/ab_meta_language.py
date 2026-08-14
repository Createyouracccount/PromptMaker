"""A/B experiment: Korean vs English meta-prompt (condensed path).

Question: does an English-language meta-prompt produce equal-or-better rewrites
(while preserving the RAW's language in output) with lower latency?

Same-window interleaved calls (K then E on even items, E then K on odd) to
control for time-of-day API variance. Blind pairwise judging: the judge sees
rewrites as A/B without knowing which meta produced them; assignment alternates
by item parity and is recorded for de-blinding.

Usage: python3 eval/ab_meta_language.py
Writes eval/ab_meta_language_results.json (raw judge outputs preserved).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from promptmaker.engine import build_meta_prompt, call_claude, parse_json_output  # noqa: E402

ITEMS = ["g01", "g05", "g09", "g13", "g18", "g19"]  # diverse intents
REWRITER = "claude-haiku-4-5"
JUDGE = "claude-sonnet-5"
TARGET = "fable-5"

EN_CONDENSED_FABLE = (
    "No numbered step lists — describe goal, intent, constraints, and completion "
    "criteria in prose. State what must NOT be done (no scope creep beyond the "
    "request). No heavy emphasis words (MUST/CRITICAL). If information needs "
    "checking, fold it into prose like 'first identify X, then proceed'."
)

EN_TEMPLATE = """You are a prompt rewriter. Rewrite RAW into a prompt optimized for Claude {target_model}.
{target_model} rules: {profile}
Common rules: never invent facts absent from RAW — turn unknowns into investigation directives; any added specifics must carry a bracketed assumption tag written in the RAW's language (Korean RAW -> [가정: 이유]). Write rewritten_prompt in the RAW's language. Keep it under 700 characters.
<RAW>
{raw}
</RAW>
Output JSON only: {{"intent": "fix|build|research|debug|refactor|docs|general", "rewritten_prompt": "...", "changes": ["1-3 items, one sentence each"]}}
"""

PAIR_JUDGE = """당신은 프롬프트 품질 심판이다. 같은 원본(RAW)을 두 가지 방식으로 재작성했다.
어느 쪽이 Claude Code(코딩 에이전트)에 입력될 프롬프트로 더 나은지 평가하라.

<RAW>
{raw}
</RAW>

<A>
{a}
</A>

<B>
{b}
</B>

각각 1~5점: clarity(목표·범위·완료기준), fidelity(왜곡·무단 추가 없음 — [가정] 표시나 조사 지시는 감점 아님), actionability(바로 착수 가능).
lang_a / lang_b: 재작성이 RAW와 같은 언어인가 (true/false).
verdict: "A" | "B" | "tie"

JSON만 출력:
{{"a": {{"clarity": n, "fidelity": n, "actionability": n}}, "b": {{"clarity": n, "fidelity": n, "actionability": n}}, "lang_a": bool, "lang_b": bool, "verdict": "A|B|tie", "reason": "한 문장"}}
"""


def timed_rewrite(meta: str) -> tuple[dict, float]:
    t0 = time.time()
    out = call_claude(meta, REWRITER, timeout=120)
    dt = time.time() - t0
    return parse_json_output(out), dt


def main() -> int:
    golden = {json.loads(l)["id"]: json.loads(l)["raw"]
              for l in (ROOT / "golden" / "golden.jsonl").open(encoding="utf-8")}
    results = []
    for i, gid in enumerate(ITEMS):
        raw = golden[gid]
        meta_k = build_meta_prompt(raw, TARGET, concise=True)
        meta_e = EN_TEMPLATE.format(target_model=TARGET, profile=EN_CONDENSED_FABLE, raw=raw.strip())
        rec = {"id": gid, "raw": raw,
               "meta_chars": {"K": len(meta_k), "E": len(meta_e)}}
        try:
            order = ["K", "E"] if i % 2 == 0 else ["E", "K"]  # interleave for fairness
            for cond in order:
                data, dt = timed_rewrite(meta_k if cond == "K" else meta_e)
                rec[cond] = {"rewritten": data["rewritten_prompt"], "latency_s": round(dt, 1)}
            # blind assignment: even items A=K, odd items A=E
            a_cond, b_cond = ("K", "E") if i % 2 == 0 else ("E", "K")
            rec["assignment"] = {"A": a_cond, "B": b_cond}
            judge_out = call_claude(
                PAIR_JUDGE.format(raw=raw, a=rec[a_cond]["rewritten"], b=rec[b_cond]["rewritten"]),
                JUDGE, timeout=120)
            rec["judge_raw"] = judge_out
            rec["judge"] = parse_json_output(judge_out)
            v = rec["judge"]["verdict"]
            rec["winner"] = "tie" if v == "tie" else rec["assignment"].get(v, "?")
            print(f"{gid}: K={rec['K']['latency_s']}s E={rec['E']['latency_s']}s "
                  f"winner={rec['winner']} lang_ok(A/B)={rec['judge']['lang_a']}/{rec['judge']['lang_b']}")
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            print(f"{gid}: ERROR {rec['error']}")
        results.append(rec)

    out = ROOT / "eval" / "ab_meta_language_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = [r for r in results if "winner" in r]
    wins = {"K": 0, "E": 0, "tie": 0}
    for r in ok:
        wins[r["winner"]] += 1
    lat_k = [r["K"]["latency_s"] for r in ok]
    lat_e = [r["E"]["latency_s"] for r in ok]
    print(f"\nwins: {wins} (n={len(ok)})")
    if ok:
        print(f"latency K: avg {sum(lat_k)/len(lat_k):.1f}s {sorted(lat_k)}")
        print(f"latency E: avg {sum(lat_e)/len(lat_e):.1f}s {sorted(lat_e)}")
        print(f"meta chars K/E: {ok[0]['meta_chars']}")
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
