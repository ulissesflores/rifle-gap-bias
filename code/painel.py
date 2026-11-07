"""Painel de mandatos anonimizado, gerador AR(1) e regras de lacuna usados pelas simulações.

Substitui, no repositório público, as partes do estudo de origem que liam os dados com CPF
(``diagnostico_alinhamento._lideres``, ``diagnostico_alinhamento.lacunas`` e ``rifle_sim.ar1``).
O código de cada prefeito em ``data/mandatos.csv`` é um número por par município-pessoa, na mesma
ordem lexicográfica das chaves originais dentro de cada município: por isso ``np.unique`` sobre
``"município|prefeito"`` devolve os mesmos índices que devolvia com o CPF, e as simulações com
efeito de prefeito reproduzem os números publicados bit a bit.
"""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
RHO = json.loads((DADOS / "parametros.json").read_text(encoding="utf-8"))["rho_gerador"]


def ler(nome):
    """Lê um CSV de ``data/`` como lista de dicionários.

    Parameters
    ----------
    nome : str
        Nome do arquivo em ``data/``.

    Returns
    -------
    list of dict
        Uma linha por registro.
    """
    with (DADOS / nome).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lideres():
    """Sequência de prefeitos nos dez períodos, por município com 2+ prefeitos e sem período vazio.

    Returns
    -------
    dict
        ``{cod_ibge7: [prefeito do período 1, ..., prefeito do período 10]}``, em ordem de código.
    """
    lid = defaultdict(dict)
    for r in ler("mandatos.csv"):
        lid[r["cod_ibge7"]][int(r["periodo"])] = r["prefeito"]
    return {
        m: [d[p] for p in range(1, 11)]
        for m, d in sorted(lid.items())
        if all(p in d for p in range(1, 11)) and len(set(d.values())) >= 2
    }


def lacunas(cond, cal, rng):
    """Períodos observados por município sob a condição de lacuna e se a mesma pessoa atravessa.

    Parameters
    ----------
    cond : str
        ``sem_lacuna``, ``alinhada_p9*``, ``longa_alinhada*``, ``na_troca``, ``meio_da_passagem`` ou
        ``aleatoria`` (período interior sorteado).
    cal : dict
        Saída de :func:`lideres`.
    rng : numpy.random.Generator
        Gerador que sorteia a posição da lacuna.

    Returns
    -------
    tuple
        ``(obs, atravessa)``: períodos observados por município e, por lacuna, se a mesma pessoa
        governa os dois lados.
    """
    obs, atravessa = {}, []
    for m, seq in cal.items():
        if cond == "sem_lacuna":
            fora = []
        elif cond.startswith("alinhada_p9"):
            fora = [9]
        elif cond.startswith("longa_alinhada"):
            fora = [7, 8]
        else:
            cand = list(range(2, 10))
            if cond == "na_troca":
                cand = [p for p in cand if seq[p - 2] != seq[p - 1] or seq[p - 1] != seq[p]]
            elif cond == "meio_da_passagem":
                cand = [p for p in cand if seq[p - 2] == seq[p - 1] == seq[p]]
            if not cand:
                continue
            fora = [int(rng.choice(cand))]
        if fora:
            atravessa.append(seq[min(fora) - 2] == seq[max(fora)])
        obs[m] = [p for p in range(1, 11) if p not in fora]
    return obs, atravessa


def ar1(n, rho, sigma2, rng):
    """Ruído AR(1) gaussiano estacionário de variância ``sigma2`` nos períodos de calendário 1..n.

    Parameters
    ----------
    n : int
        Número de períodos.
    rho : float
        Coeficiente autorregressivo.
    sigma2 : float
        Variância marginal.
    rng : numpy.random.Generator
        Gerador de números aleatórios.

    Returns
    -------
    numpy.ndarray
        Série de comprimento ``n``.
    """
    e = np.empty(n)
    e[0] = rng.normal(0, math.sqrt(sigma2))
    inov = math.sqrt(sigma2 * (1 - rho**2))
    for t in range(1, n):
        e[t] = rho * e[t - 1] + rng.normal(0, inov)
    return e
