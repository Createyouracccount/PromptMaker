"""Re-run specific golden items and merge into eval/results.json.

Usage: python3 eval/rerun_items.py g02 g05 g19
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from run_eval import process_item  # noqa: E402


def main() -> int:
    ids = set(sys.argv[1:])
    if not ids:
        print("usage: rerun_items.py <id> [<id> ...]")
        return 1
    items = [json.loads(line) for line in (ROOT / "golden" / "golden.jsonl").open(encoding="utf-8")]
    targets = [i for i in items if i["id"] in ids]

    with ThreadPoolExecutor(max_workers=3) as pool:
        new = {r["id"]: r for r in pool.map(process_item, targets)}

    path = ROOT / "eval" / "results.json"
    results = json.load(path.open(encoding="utf-8"))
    results = [new.get(r["id"], r) for r in results]
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    for rid, r in new.items():
        if "error" in r:
            print(f"{rid}: ERROR {r['error'].splitlines()[-1]}")
        else:
            print(f"{rid}: verdict={r['judge'].get('verdict')} judge={json.dumps(r['judge'], ensure_ascii=False)}")
            if "diff_judge" in r:
                print(f"{rid}: diff={json.dumps(r['diff_judge'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
