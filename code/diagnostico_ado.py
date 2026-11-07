#!/usr/bin/env python3

"""Os achados da costura valem para o pacote oficial? Teste com a tradução fiel do ``rifle.ado``.

No repositório público: cópia do módulo do estudo de origem (``piloto/diagnostico_ado.py``), com o
painel lido de ``data/`` por ``painel.py`` (código anônimo de prefeito, sem CPF) e a saída em
``output/rerun/``; o resto é idêntico, e a rodada completa reproduz bit a bit a saída
congelada em ``data/congelado/``.

Pedido pela revisão independente (2026-10-31): o nosso motor rotula por passagem e transforma
cada trecho em unidade; o ado agrupa pela IDENTIDADE do líder (inclusive entre blocos no
``nostitch``) e mantém bloco de uma linha. Aqui tudo roda em ``rifle_ado`` (testado contra contas
à mão em ``teste_rifle_ado.py``). Só resultado SINTÉTICO.

Painel: subamostra aleatória fixa de N = 1.000 municípios com prefeito nos 10 períodos e 2+
prefeitos. Ruído AR(1) por município no calendário; efeito por PESSOA no município (a mesma pessoa
dos dois lados da lacuna tem o mesmo efeito), variância Prop/(1-Prop). Células, 500 bases,
1.000 permutações:

| célula | lacuna | modo | ρ | Prop |
|---|---|---|---|---|
| sem_lacuna | nenhuma | costura | 0,217 | 0 |
| p9 | período 9 | costura | 0,217 | 0 |
| meio | um período no meio da passagem | costura | 0,217 | 0 |
| p9_nostitch | período 9 | nostitch | 0,217 | 0 |
| aleatoria_nostitch | período interior sorteado (2+ prefeitos por bloco) | nostitch | 0,217 | 0 |
| p9_rho0 | período 9 | costura | 0 | 0 |
| sem_lacuna_poder | nenhuma | costura | 0,217 | 0,10 |
| meio_poder | um período no meio da passagem | costura | 0,217 | 0,10 |

Sementes: ``SeedSequence([14112026, k])``; a subamostra usa ``SeedSequence([14112026, 99])``.
Saída: ``output/rerun/diagnostico_ado.json``.
"""

import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import painel as D
import rifle_ado as R
from scipy.stats import binomtest

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "output" / "rerun" / "diagnostico_ado.json"
SEMENTE, BASES, PERM, N = 14112026, 500, 1000, 1000
CELULAS = [
    ("sem_lacuna", "nenhuma", True, D.RHO, 0.0),
    ("p9", "p9", True, D.RHO, 0.0),
    ("meio", "meio", True, D.RHO, 0.0),
    ("p9_nostitch", "p9", False, D.RHO, 0.0),
    ("aleatoria_nostitch", "aleatoria2", False, D.RHO, 0.0),
    ("p9_rho0", "p9", True, 0.0, 0.0),
    ("sem_lacuna_poder", "nenhuma", True, D.RHO, 0.10),
    ("meio_poder", "meio", True, D.RHO, 0.10),
]


def painel():
    """Sorteia a subamostra fixa de ``N`` municípios do painel de líderes.

    Returns
    -------
    dict
        Município -> sequência de líderes nos 10 períodos, na ordem dos códigos.
    """
    cal = D.lideres()
    nomes = sorted(cal)
    rng = np.random.default_rng(np.random.SeedSequence([SEMENTE, 99]))
    return {nomes[i]: cal[nomes[i]] for i in sorted(rng.choice(len(nomes), size=N, replace=False))}


def lacuna(tipo, seq, rng):
    """Período a tirar (ou None), ou False se o município não serve à condição."""
    if tipo == "nenhuma":
        return None
    if tipo == "p9":
        return 9
    if tipo == "meio":
        cand = [p for p in range(2, 10) if seq[p - 2] == seq[p - 1] == seq[p]]
    else:  # aleatoria2: os dois blocos contíguos com 2+ prefeitos distintos
        cand = [p for p in range(2, 10) if len(set(seq[: p - 1])) >= 2 and len(set(seq[p:])) >= 2]
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
    nome, tipo, costura, rho, prop = CELULAS[k]
    rng = np.random.default_rng(np.random.SeedSequence([SEMENTE, k]))
    cal = painel()
    fora = {m: lacuna(tipo, s, rng) for m, s in cal.items()}
    ms = [m for m in cal if fora[m] is not False]
    u = np.repeat(np.arange(len(ms)), 10)
    t = np.tile(np.arange(1, 11), len(ms))
    pessoa = np.array([f"{m}|{p}" for m in ms for p in cal[m]])  # identidade dentro do município
    falta = np.array([fora[m] == p for m in ms for p in range(1, 11)])
    _, pid = np.unique(pessoa, return_inverse=True)
    s2l = prop / (1 - prop)
    rej = 0
    e0 = None
    for _ in range(BASES):
        y = np.concatenate([D.ar1(10, rho, 1.0, rng) for _ in ms])
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
        "lacuna": tipo,
        "modo": "costura" if costura else "nostitch",
        "rho": rho,
        "prop": prop,
        "municipios": len(ms),
        **e0,
        "rejeicoes": rej,
        "bases": BASES,
        "taxa": rej / BASES,
        "ic95": [round(ci.low, 4), round(ci.high, 4)],
    }


def main():
    """Roda as células em paralelo, imprime cada resultado e grava ``SAIDA``."""
    with ProcessPoolExecutor(len(CELULAS)) as ex:
        res = dict(ex.map(rodar, range(len(CELULAS))))
    out = {"semente": SEMENTE, "bases": BASES, "permutacoes": PERM, "N": N, "celulas": res}
    for c, r in res.items():
        print(c, json.dumps(r), flush=True)
    SAIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
