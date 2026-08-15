"""Measure the real token/cost overhead of prompt-tailor.

Three numbers a user actually pays:
  1. Rewrite call (hook path, lean meta): tokens + USD + wall time
  2. Rewrite call (/pm & MCP path, intent-routed meta): tokens + USD + wall time
  3. Injected-context overhead in the main conversation: measured as the
     input-token DELTA between a probe call with and without the injected
     context appended (isolates the context's true token count).

Uses `claude -p --output-format json`, which reports usage and total_cost_usd.

Usage: python3 eval/measure_cost.py
Writes runs/cost_measurement.json (raw outputs preserved).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from prompt_tailor.engine import build_meta_prompt, parse_json_output  # noqa: E402

SAMPLE = "주문 내역 페이지가 가끔 빈 화면으로 나와요 고쳐주세요"
REWRITER = "claude-haiku-4-5"


def call_json(prompt: str, model: str, timeout: int = 120) -> dict:
    t0 = time.time()
    proc = subprocess.run(
        ["claude", "-p", "--model", model, "--output-format", "json",
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}'],
        input=prompt, capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr[:300]}")
    data = json.loads(proc.stdout)
    usage = data.get("usage", {})
    return {
        "wall_s": round(time.time() - t0, 1),
        "input_tokens": usage.get("input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cost_usd": data.get("total_cost_usd"),
        "result": data.get("result", ""),
    }


def total_in(u: dict) -> int:
    return sum(u.get(k) or 0 for k in
               ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def main() -> int:
    out: dict = {"sample": SAMPLE, "rewriter": REWRITER}

    # 1+2: rewrite call cost, both meta variants, 2 runs each
    for tag, kwargs in (("hook_lean", {"concise": True, "intent_routing": False}),
                        ("pm_routed", {"concise": True, "intent_routing": True})):
        meta = build_meta_prompt(SAMPLE, "fable-5", **kwargs)
        runs = []
        for _ in range(2):
            r = call_json(meta, REWRITER)
            r["rewritten_chars"] = len(parse_json_output(r["result"])["rewritten_prompt"])
            runs.append(r)
        out[tag] = {"meta_chars": len(meta), "runs": runs}
        avg_in = sum(total_in(r) for r in runs) / len(runs)
        avg_out = sum(r["output_tokens"] for r in runs) / len(runs)
        avg_cost = sum(r["cost_usd"] for r in runs) / len(runs)
        avg_wall = sum(r["wall_s"] for r in runs) / len(runs)
        out[tag]["avg"] = {"in_tokens": round(avg_in), "out_tokens": round(avg_out),
                           "cost_usd": round(avg_cost, 4), "wall_s": round(avg_wall, 1)}
        print(f"{tag}: in≈{avg_in:.0f} out≈{avg_out:.0f} tokens, "
              f"${avg_cost:.4f}, {avg_wall:.1f}s (n=2)")

    # 3: injected-context overhead — token delta of a probe with/without context
    rewritten = parse_json_output(out["hook_lean"]["runs"][0]["result"])["rewritten_prompt"]
    context = (
        "[PromptTailor] 사용자의 요청을 대상 모델에 맞게 재해석했다. "
        "원문 의도를 유지하되 아래 재작성을 작업 지침으로 삼아라. "
        "[가정]으로 표시된 부분은 단정하지 말고 작업 중 확인하라.\n"
        f"<재작성 대상모델=fable-5>\n{rewritten}\n</재작성>"
    )
    probe = "답변은 'ok' 한 단어로만 하라."
    base = call_json(probe, REWRITER)
    with_ctx = call_json(probe + "\n\n" + context, REWRITER)
    delta = total_in(with_ctx) - total_in(base)
    out["injected_context"] = {"chars": len(context), "token_delta": delta,
                               "base": base, "with_ctx": with_ctx}
    print(f"injected context: {len(context)} chars ≈ {delta} input tokens in the main conversation")

    (ROOT / "runs" / "cost_measurement.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written to runs/cost_measurement.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
