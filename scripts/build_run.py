#!/usr/bin/env python3
"""Sela uma rodada: ``runs/<UTC>/manifest.json`` (cadeia de proveniência) e ``checksums.sha256``.

A rodada é a unidade de evidência: a cadeia de Merkle por etapas (``provenance_chain.py``,
configurada em ``configs/stages.json``) amarra ambiente, pré-registro, dados, código, saídas
congeladas, resultados, tabelas e paper num único ``chain_head``.
``scripts/verify_chain.py`` recomputa tudo do disco.

    python scripts/build_run.py --nota "<por que esta rodada>"
"""

import argparse
import datetime as dt
import importlib.metadata as md
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import provenance_chain as pc  # noqa: E402


def main(argv=None):
    """Monta a cadeia, grava o manifesto e as somas de verificação e devolve 0.

    Parameters
    ----------
    argv : list of str, optional
        Argumentos de linha de comando.

    Returns
    -------
    int
        Código de saída.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nota", required=True)
    a = ap.parse_args(argv)
    anteriores = sorted((ROOT / "runs").glob("*/manifest.json"))
    prev = (
        json.loads(anteriores[-1].read_text(encoding="utf-8"))["provenance"]["chain_head"]
        if anteriores
        else ""
    )
    stages = json.loads((ROOT / "configs" / "stages.json").read_text(encoding="utf-8"))
    prov = pc.build_chain(ROOT, stages, prev)
    run_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    d = ROOT / "runs" / run_id
    d.mkdir(parents=True, exist_ok=False)
    manifest = {
        "run_id": run_id,
        "nota": a.nota,
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        # ambiente exato desta rodada, lido do interpretador que a selou
        "pip_freeze": sorted(f"{d.metadata['Name']}=={d.version}" for d in md.distributions()),
        "provenance": prov,
    }
    (d / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    n = pc.write_sha256sums(prov, d / "checksums.sha256")
    print(f"[OK] runs/{run_id}: chain_head {prov['chain_head']} ({n} arquivos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
