#!/usr/bin/env python3
"""Recompute the provenance chain from disk and verify it against the latest sealed run.

Exit code == number of mismatches (0 == CHAIN INTACT). Pure stdlib; any third party can
run `python scripts/verify_chain.py` offline with zero knowledge of this tool. See
REPRODUCIBILITY.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import provenance_chain as pc  # noqa: E402


def latest_manifest() -> Path | None:
    """Return the newest `runs/*/manifest.json`, or None when no run was sealed."""
    runs = sorted((ROOT / "runs").glob("*/manifest.json"))
    return runs[-1] if runs else None


def main() -> int:
    """Verify the chain against the latest sealed run; return the number of mismatches."""
    stages_path = ROOT / "configs" / "stages.json"
    mf_path = latest_manifest()
    if mf_path is None:
        print("[FAIL] no runs/*/manifest.json — build one with: python scripts/build_run.py")
        return 1
    manifest = json.loads(mf_path.read_text(encoding="utf-8"))
    prov = manifest.get("provenance", manifest)
    problems = pc.verify(ROOT, stages_path, prov)
    if problems:
        for pr in problems:
            print(f"[FAIL] {pr}")
        print(f"[FAIL] {len(problems)} mismatch(es) — CHAIN VIOLATED ({mf_path.parent.name})")
        return len(problems)
    print(f"[PASS] CHAIN INTACT — chain_head {prov.get('chain_head')} ({mf_path.parent.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
