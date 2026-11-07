#!/usr/bin/env python3

"""Células pedidas pela 1ª rodada de revisão externa (2026-11-01), na tradução fiel do ado.

No repositório público: cópia do módulo do estudo de origem
(``piloto/diagnostico_ado_juizes.py``), com o painel lido de ``data/`` por
``painel.py`` (código anônimo de prefeito, sem CPF) e a saída em ``output/rerun/``; o resto
é idêntico, e a rodada completa reproduz bit a bit a saída congelada em ``data/congelado/``.

Não há afirmação nova: cada célula sustenta, ou derruba, uma frase que o artigo de método já faz.

- ``nostitch`` no painel inteiro (5.468): a frase "o ``nostitch`` restaura o tamanho" estava
  medida só em 1.000 municípios, ao lado de 76,6% e 89,4% em 5.468.
- Sem lacuna no painel inteiro: a linha de base do pacote (2,2% em 1.000) pode mudar com N.
- Sem lacuna, com e sem efeito, nos MESMOS 867 municípios da célula ``meio`` de ``diagnostico_ado``:
  a comparação "muda só onde a lacuna cai" misturava 1.000 e 867 municípios.
- Poder sob ``nostitch`` (Prop 10% e 5%) e o controle sem lacuna com Prop 5%: a recomendação de
  preferir o ``nostitch`` não media o custo em poder.

Painéis: "todo" = os 5.468 municípios; "mil" = a subamostra fixa de ``diagnostico_ado.painel()``;
"meio867" = os municípios de "mil" com candidato a lacuna no meio da passagem (mesmo critério de
``diagnostico_ado.lacuna("meio")``). Identidade do líder = par município-pessoa. Só resultado
SINTÉTICO.

Sementes: ``SeedSequence([17112026, k])``. Fumaça: ``--fumaca`` (semente descartável 999980,
3 bases, 50 permutações, saída só no stdout). Saída: ``output/rerun/diagnostico_ado_juizes.json``.
"""

import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import diagnostico_ado as A
import numpy as np
import painel as D
import rifle_ado as R
from scipy.stats import binomtest

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "output" / "rerun" / "diagnostico_ado_juizes.json"
FUMACA = "--fumaca" in sys.argv
SEMENTE, BASES, PERM = (999980, 3, 50) if FUMACA else (17112026, 500, 1000)

# (nome, painel, lacuna, costura, prop)
CELULAS = [
    ("sem_lacuna_N5468", "todo", "nenhuma", True, 0.0),
    ("p9_nostitch_N5468", "todo", "p9", False, 0.0),
    ("na_troca_nostitch_N5468", "todo", "na_troca", False, 0.0),
    ("aleatoria_nostitch_N5468", "todo", "aleatoria", False, 0.0),
    ("sem_lacuna_meio867", "meio867", "nenhuma", True, 0.0),
    ("sem_lacuna_poder10_meio867", "meio867", "nenhuma", True, 0.10),
    ("p9_nostitch_poder10", "mil", "p9", False, 0.10),
    ("p9_nostitch_poder05", "mil", "p9", False, 0.05),
    ("sem_lacuna_poder05", "mil", "nenhuma", True, 0.05),
    ("aleatoria2_nostitch_poder10", "mil", "aleatoria2", False, 0.10),
]


def painel(nome):
    """Devolve o painel de líderes da célula pedida.

    Parameters
    ----------
    nome : str
        ``"todo"`` (5.468 municípios), ``"mil"`` (subamostra fixa) ou ``"meio867"``.

    Returns
    -------
    dict
        Município -> sequência de líderes nos 10 períodos.
    """
    if nome == "todo":
        return D.lideres()
    cal = A.painel()
    if nome == "meio867":
        cal = {
            m: s for m, s in cal.items() if any(s[p - 2] == s[p - 1] == s[p] for p in range(2, 10))
        }
    return cal


def fora_de(tipo, seq, rng):
    """Período a tirar (None = nenhum) ou False se o município não serve à condição."""
    if tipo in ("nenhuma", "p9", "meio", "aleatoria2"):
        return A.lacuna(tipo, seq, rng)
    cand = list(range(2, 10))  # mesmos critérios de diagnostico_alinhamento.lacunas
    if tipo == "na_troca":
        cand = [p for p in cand if seq[p - 2] != seq[p - 1] or seq[p - 1] != seq[p]]
    return int(rng.choice(cand)) if cand else False


def rodar(k):
    """Roda a célula ``k`` de ``CELULAS``: simula as bases e conta as rejeições.

    Parameters
    ----------
    k : int
        Índice da célula em ``CELULAS`` (também entra na semente).

    Returns
    -------
    tuple
        Nome da célula e o dicionário com desenho, rejeições, taxa e intervalo de 95%.
    """
    nome, pnl, tipo, costura, prop = CELULAS[k]
    rng = np.random.default_rng(np.random.SeedSequence([SEMENTE, k]))
    cal = painel(pnl)
    fora = {m: fora_de(tipo, s, rng) for m, s in cal.items()}
    ms = [m for m in cal if fora[m] is not False]
    u = np.repeat(np.arange(len(ms)), 10)
    t = np.tile(np.arange(1, 11), len(ms))
    pessoa = np.array([f"{m}|{p}" for m in ms for p in cal[m]])
    falta = np.array([fora[m] == p for m in ms for p in range(1, 11)])
    _, pid = np.unique(pessoa, return_inverse=True)
    s2l = prop / (1 - prop)
    rej, e0 = 0, None
    for _ in range(BASES):
        y = np.concatenate([D.ar1(10, D.RHO, 1.0, rng) for _ in ms])
        if s2l:
            y = y + rng.normal(0, math.sqrt(s2l), pid.max() + 1)[pid]
        y[falta] = np.nan
        e = R.preparar(u, t, pessoa, y, stitch=costura)
        e0 = e0 or {
            "celulas": len(e["y"]),
            "unidades": int(e["unid"].max()) + 1,
            "stints": len(e["st_lid"]),
        }
        _, p = R.teste(e, PERM, rng)
        rej += p <= 0.05
    ci = binomtest(rej, BASES).proportion_ci(confidence_level=0.95, method="exact")
    return nome, {
        "painel": pnl,
        "lacuna": tipo,
        "modo": "costura" if costura else "nostitch",
        "rho": D.RHO,
        "prop": prop,
        "municipios": len(ms),
        **e0,
        "rejeicoes": rej,
        "bases": BASES,
        "taxa": rej / BASES,
        "ic95": [round(ci.low, 4), round(ci.high, 4)],
    }


def main():
    """Roda as células em paralelo, imprime cada resultado e grava ``SAIDA`` (menos na fumaça)."""
    with ProcessPoolExecutor(len(CELULAS)) as ex:
        res = dict(ex.map(rodar, range(len(CELULAS))))
    out = {
        "semente": SEMENTE,
        "bases": BASES,
        "permutacoes": PERM,
        "motor": "rifle_ado",
        "celulas": res,
    }
    for c, r in res.items():
        print(c, json.dumps(r), flush=True)
    if not FUMACA:
        SAIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
