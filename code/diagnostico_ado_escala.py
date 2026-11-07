#!/usr/bin/env python3

"""Números de capa do artigo com a tradução fiel do ``rifle.ado``: costura padrão por N.

No repositório público: cópia do módulo do estudo de origem
(``piloto/diagnostico_ado_escala.py``), com o painel lido de ``data/`` por
``painel.py`` (código anônimo de prefeito, sem CPF) e a saída em ``output/rerun/``; o resto
é idêntico, e a rodada completa reproduz bit a bit a saída congelada em ``data/congelado/``.

Os 64%/98% anteriores vêm do nosso motor (rótulo por passagem). O artigo critica o PACOTE, então
os números de capa vêm de ``rifle_ado``. Só SINTÉTICO, AR(1) ρ 0,217, Prop 0, costura padrão.
Células: lacuna p9, lacuna interior sorteada (2 a 9) e lacuna vizinha de troca, em subamostras
de N ∈ {50, 200, 1000} e no painel inteiro (5.468). 500 bases, 1.000 permutações. Registra
também a fração de lacunas vizinhas de troca e a fração em que a mesma pessoa está dos dois lados.

Sementes: ``SeedSequence([15112026, k])``. Saída: ``output/rerun/diagnostico_ado_escala.json``.
"""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import painel as D
import rifle_ado as R
from scipy.stats import binomtest

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "output" / "rerun" / "diagnostico_ado_escala.json"
SEMENTE, BASES, PERM = 15112026, 500, 1000
CELULAS = [(c, n) for c in ("p9", "aleatoria", "na_troca") for n in (50, 200, 1000, None)]


def rodar(k):
    """Roda a célula ``k`` de ``CELULAS``: simula as bases e conta as rejeições.

    Parameters
    ----------
    k : int
        Índice da célula em ``CELULAS`` (condição de lacuna e tamanho do painel).

    Returns
    -------
    tuple
        Nome da célula e o dicionário com desenho, rejeições, taxa e intervalo de 95%.
    """
    cond, n = CELULAS[k]
    rng = np.random.default_rng(np.random.SeedSequence([SEMENTE, k]))
    cal = D.lideres()
    nomes = sorted(cal)
    if n:
        cal = {
            nomes[i]: cal[nomes[i]] for i in sorted(rng.choice(len(nomes), size=n, replace=False))
        }
    obs, atravessa = D.lacunas("alinhada_p9" if cond == "p9" else cond, cal, rng)
    ms = sorted(obs)
    u = np.repeat(np.arange(len(ms)), 10)
    t = np.tile(np.arange(1, 11), len(ms))
    pessoa = np.array([f"{m}|{p}" for m in ms for p in cal[m]])
    falta = np.array([p not in obs[m] for m in ms for p in range(1, 11)])
    vizinha = [
        any(cal[m][q - 1] != cal[m][q] for q in (p - 1, p) if 1 <= q < 10)
        for m in ms
        for p in range(2, 10)
        if p not in obs[m]
    ]
    rej = 0
    for _ in range(BASES):
        y = np.concatenate([D.ar1(10, D.RHO, 1.0, rng) for _ in ms])
        y[falta] = np.nan
        _, p = R.teste(R.preparar(u, t, pessoa, y), PERM, rng)
        rej += p <= 0.05
    ci = binomtest(rej, BASES).proportion_ci(confidence_level=0.95, method="exact")
    return f"{cond}_N{n or len(ms)}", {
        "condicao": cond,
        "N": len(ms),
        "rejeicoes": rej,
        "bases": BASES,
        "taxa": rej / BASES,
        "ic95": [round(ci.low, 4), round(ci.high, 4)],
        "fracao_lacuna_vizinha_de_troca": float(np.mean(vizinha)),
        "fracao_mesma_pessoa_dos_dois_lados": float(np.mean(atravessa)),
    }


def main():
    """Roda as células em paralelo, imprime cada resultado e grava ``SAIDA``."""
    with ProcessPoolExecutor(6) as ex:
        res = dict(ex.map(rodar, range(len(CELULAS))))
    out = {
        "semente": SEMENTE,
        "rho": D.RHO,
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
