#!/usr/bin/env python3

"""A máscara REAL de lacunas, com resultado SINTÉTICO, na tradução fiel do ``rifle.ado``.

No repositório público: cópia do módulo do estudo de origem
(``piloto/diagnostico_ado_mascara_real.py``), com o painel lido de ``data/`` por
``painel.py`` (código anônimo de prefeito, sem CPF) e a saída em ``output/rerun/``; o resto
é idêntico, e a rodada completa reproduz bit a bit a saída congelada em ``data/congelado/``.

Pedido pela revisão independente (2026-10-31): os 64% (lacuna interior) e os 5% (só borda) da
máscara real vieram do nosso motor (rótulo por passagem). Aqui, com ``rifle_ado``: municípios da
amostra v2 cujas células observadas têm lacuna interior, ou só lacuna de borda, conforme o
índice real (``indice_secundaria.csv``, só QUAIS células existem; nenhum valor do índice é
usado). Resultado sintético AR(1) ρ 0,217 no calendário, sem efeito de prefeito; costura padrão e
nostitch. 500 bases, 1.000 permutações. Sementes ``SeedSequence([16112026, k])``.
Saída: ``output/rerun/diagnostico_ado_mascara_real.json``.
"""

import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import painel as P
import rifle_ado as R
from scipy.stats import binomtest

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "output" / "rerun" / "diagnostico_ado_mascara_real.json"
SEMENTE, BASES, PERM = 16112026, 500, 1000
RHO = P.RHO
CELULAS = [("interior", True), ("interior", False), ("so_borda", True)]


def rodar(k):
    """Roda a célula ``k`` de ``CELULAS``: simula as bases sobre a máscara real e conta rejeições.

    Parameters
    ----------
    k : int
        Índice da célula em ``CELULAS`` (grupo de municípios e modo de costura).

    Returns
    -------
    tuple
        Nome da célula e o dicionário com municípios, rejeições, taxa e intervalo de 95%.
    """
    grupo, costura = CELULAS[k]
    lid = defaultdict(dict)
    for r in P.ler("mandatos.csv"):
        lid[r["cod_ibge7"]][int(r["periodo"])] = r["prefeito"]
    obs = defaultdict(list)
    for r in P.ler("mascara_indice.csv"):
        obs[r["cod_ibge7"]].append(int(r["periodo"]))
    lac = [m for m in sorted(obs) if len(obs[m]) < 10]
    borda = [m for m in lac if obs[m][-1] - obs[m][0] + 1 == len(obs[m])]
    ms = borda if grupo == "so_borda" else [m for m in lac if m not in set(borda)]
    u = np.concatenate([[i] * len(obs[m]) for i, m in enumerate(ms)])
    t = np.concatenate([obs[m] for m in ms])
    pessoa = np.array([f"{m}|{lid[m][p]}" for m in ms for p in obs[m]])
    rng = np.random.default_rng(np.random.SeedSequence([SEMENTE, k]))
    rej = 0
    for _ in range(BASES):
        y = np.concatenate([P.ar1(10, RHO, 1.0, rng)[np.asarray(obs[m]) - 1] for m in ms])
        _, p = R.teste(R.preparar(u, t, pessoa, y, stitch=costura), PERM, rng)
        rej += p <= 0.05
    ci = binomtest(rej, BASES).proportion_ci(confidence_level=0.95, method="exact")
    return f"{grupo}_{'costura' if costura else 'nostitch'}", {
        "municipios": len(ms),
        "rejeicoes": rej,
        "bases": BASES,
        "taxa": rej / BASES,
        "ic95": [round(ci.low, 4), round(ci.high, 4)],
    }


def main():
    """Roda as células em paralelo, imprime cada resultado e grava ``SAIDA``."""
    with ProcessPoolExecutor(len(CELULAS)) as ex:
        res = dict(ex.map(rodar, range(len(CELULAS))))
    out = {
        "semente": SEMENTE,
        "rho": RHO,
        "bases": BASES,
        "permutacoes": PERM,
        "motor": "rifle_ado",
        "celulas": res,
    }
    for c, r in res.items():
        print(c, json.dumps(r), flush=True)
    SAIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
