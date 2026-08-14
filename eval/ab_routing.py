"""A/B experiment: model-profile-only meta (v1) vs intent-routed meta (v2).

Same design as ab_meta_language.py: interleaved same-window calls, blind
pairwise judging with recorded assignment, judge raw outputs preserved.

Usage: python3 eval/ab_routing.py
Writes eval/ab_routing_results.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from promptmaker.engine import (  # noqa: E402
    CONDENSED_TEMPLATE,
    PROFILES_DIR,
    build_meta_prompt,
    call_claude,
    parse_json_output,
)

# one item per intent family
ITEMS = ["g01", "g05", "g09", "g13", "g16", "g19"]
REWRITER = "claude-haiku-4-5"
JUDGE = "claude-sonnet-5"
TARGET = "fable-5"

# v1 = the pre-R22 condensed template (no intent rules), reconstructed
V1_TEMPLATE = """\
당신은 프롬프트 재작성기다. RAW를 Claude {target_model}에 맞게 재작성하라.
{target_model} 규칙: {condensed_profile}
공통: RAW에 없는 사실을 지어내지 말 것 — 모르면 조사 지시로 바꾸고, 추가 세부에는 [가정: 이유] 필수. RAW 언어 유지. rewritten_prompt는 700자 이내.
<RAW>
{raw_prompt}
</RAW>
JSON만 출력: {{"intent": "fix|build|research|debug|refactor|docs|general", "rewritten_prompt": "...", "changes": ["1~3개, 각 한 문장"]}}
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
verdict: "A" | "B" | "tie"

JSON만 출력:
{{"a": {{"clarity": n, "fidelity": n, "actionability": n}}, "b": {{"clarity": n, "fidelity": n, "actionability": n}}, "verdict": "A|B|tie", "reason": "한 문장"}}
"""


def timed(meta: str) -> tuple[dict, float]:
    t0 = time.time()
    out = call_claude(meta, REWRITER, timeout=120)
    return parse_json_output(out), time.time() - t0


def main() -> int:
    golden = {json.loads(l)["id"]: json.loads(l)["raw"]
              for l in (ROOT / "golden" / "golden.jsonl").open(encoding="utf-8")}
    condensed_profile = (PROFILES_DIR / "condensed" / f"{TARGET}.md").read_text(encoding="utf-8").strip()
    results = []
    for i, gid in enumerate(ITEMS):
        raw = golden[gid]
        meta_v1 = V1_TEMPLATE.format(target_model=TARGET, condensed_profile=condensed_profile,
                                     raw_prompt=raw.strip())
        meta_v2 = build_meta_prompt(raw, TARGET, concise=True)
        rec = {"id": gid, "raw": raw}
        try:
            order = ["v1", "v2"] if i % 2 == 0 else ["v2", "v1"]
            for cond in order:
                data, dt = timed(meta_v1 if cond == "v1" else meta_v2)
                rec[cond] = {"rewritten": data["rewritten_prompt"],
                             "intent": data.get("intent"), "latency_s": round(dt, 1)}
            a_cond, b_cond = ("v1", "v2") if i % 2 == 0 else ("v2", "v1")
            rec["assignment"] = {"A": a_cond, "B": b_cond}
            judge_out = call_claude(
                PAIR_JUDGE.format(raw=raw, a=rec[a_cond]["rewritten"], b=rec[b_cond]["rewritten"]),
                JUDGE, timeout=120)
            rec["judge_raw"] = judge_out
            rec["judge"] = parse_json_output(judge_out)
            v = rec["judge"]["verdict"]
            rec["winner"] = "tie" if v == "tie" else rec["assignment"].get(v, "?")
            print(f"{gid}: v1={rec['v1']['latency_s']}s v2={rec['v2']['latency_s']}s "
                  f"intent(v2)={rec['v2']['intent']} winner={rec['winner']}")
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            print(f"{gid}: ERROR {rec['error']}")
        results.append(rec)

    out = ROOT / "eval" / "ab_routing_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = [r for r in results if "winner" in r]
    wins = {"v1": 0, "v2": 0, "tie": 0}
    for r in ok:
        wins[r["winner"]] += 1
    for tag in ("v1", "v2"):
        lat = [r[tag]["latency_s"] for r in ok]
        if lat:
            print(f"latency {tag}: avg {sum(lat)/len(lat):.1f}s {sorted(lat)}")
    print(f"wins: {wins} (n={len(ok)})")
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
