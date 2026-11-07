#!/usr/bin/env python3

"""Verificações pequenas do port ``rifle_ado`` e do exemplo de dois municípios, para o artigo.

No repositório público: cópia do módulo do estudo de origem (``piloto/verificacoes_port.py``), com o
painel lido de ``data/`` por ``painel.py`` (código anônimo de prefeito, sem CPF) e a saída em
``output/rerun/``; o resto é idêntico, e a rodada completa reproduz bit a bit a saída
congelada em ``data/congelado/``.

Pedidas pela quarta rodada de revisão (2026-11-03): os números de validação do port e o
"cerca de 47%" da Seção 3.2 estavam no texto sem saída com hash. Quatro blocos, todos sintéticos:

1. ``ponta``: painel de 2 unidades com líder que volta (A A B A A; C D D E E); as 36 ordens de
   passagens enumeradas dão o valor-p exato e a Diferença populacional; ``R.teste`` com
   200.000 permutações tem de ficar a menos de 0,01 do valor-p exato.
2. ``media_inclui_real``: com 3 permutações, refaz por fora as ordens sorteadas (mesma sequência
   de números aleatórios) e calcula o R² de cada uma com uma fórmula independente (dicionário
   de grupos); a Diferença de ``R.teste`` tem de ser igual a real − (soma das permutações +
   real)/4 até 1e-12 e diferente de real − média só das permutações.
3. ``nostitch``: painel com lacuna, trecho de um só líder descartado, trecho de uma linha
   mantido e a mesma pessoa nos dois trechos; valor-p exato por enumeração contra ``R.teste``.
4. ``dois_municipios``: o segundo exemplo da Seção 3.2 (A em 1-2, B em 3-6, falta o período 4)
   em dois municípios independentes, ruído gaussiano AR(1) estacionário (variância 1, inovação
   1 − ρ²), ρ = 0,217, desconto da média do período; mede P(Q_real > Q_invertida) em 400.000
   bases e a taxa de rejeição a 5% de ``R.teste`` (200 permutações) em 4.000 bases.

Sementes: ``SeedSequence([19112026, k])``. Saída: ``output/rerun/verificacoes_port.json``.
"""

import itertools
import json
import math
from pathlib import Path

import numpy as np
import rifle_ado as R

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "output" / "rerun" / "verificacoes_port.json"
SEMENTE, RHO = 19112026, 0.21696453979704527


def rng(k):
    """Cria o gerador de números aleatórios da verificação ``k``.

    Parameters
    ----------
    k : int
        Índice do bloco (entra na semente).

    Returns
    -------
    numpy.random.Generator
        Gerador semeado com ``SeedSequence([SEMENTE, k])``.
    """
    return np.random.default_rng(np.random.SeedSequence([SEMENTE, k]))


def r2_independente(y, grupos):
    """R² de efeitos fixos de grupo, sem passar por ``R.r2``."""
    g = {}
    for v, k in zip(y, grupos, strict=False):
        g.setdefault(int(k), []).append(v)
    ssw = sum(((np.array(v) - np.mean(v)) ** 2).sum() for v in g.values())
    return 1 - ssw / ((np.asarray(y) - np.mean(y)) ** 2).sum()


def enumerar(e):
    """Valor-p exato (fração das ordens com R² estritamente maior) e média exata das ordens."""
    real = r2_independente(e["y"], e["lid"])
    por_unid = [np.flatnonzero(e["st_unid"] == k) for k in np.unique(e["st_unid"])]
    r2s = []
    for ordens in itertools.product(*(itertools.permutations(ix) for ix in por_unid)):
        ordem = np.concatenate(ordens)
        r2s.append(r2_independente(e["y"], np.repeat(e["st_lid"][ordem], e["st_tam"][ordem])))
    r2s = np.array(r2s)
    return real, float((r2s > real).mean()), float(r2s.mean()), len(r2s)


def bloco_ponta():
    """Confere ``R.teste`` contra a enumeração exata das 36 ordens de passagens.

    Returns
    -------
    dict
        Número de ordens, valor-p e Diferença exatos e de ``R.teste``, e o veredito ``passa``.
    """
    u, t = [1] * 5 + [2] * 5, list(range(1, 6)) * 2
    lid = ["A", "A", "B", "A", "A", "C", "D", "D", "E", "E"]
    y = [0.3, 1.9, -0.7, 2.4, 1.1, -1.2, 0.8, 1.5, -0.4, 0.2]
    e = R.preparar(u, t, lid, y)
    real, p_exato, media, n = enumerar(e)
    diff, p = R.teste(e, 200_000, rng(1))
    return {
        "ordens": n,
        "p_exato": p_exato,
        "p_teste": p,
        "diff_exata": real - media,
        "diff_teste": diff,
        "passa": bool(abs(p - p_exato) < 0.01 and abs(diff - (real - media)) < 0.005),
    }


def bloco_media():
    """Confere que a Diferença de ``R.teste`` inclui a linha real na média.

    Returns
    -------
    dict
        Diferença de ``R.teste``, com e sem a linha real, e o veredito ``passa``.
    """
    u, t = [1] * 5 + [2] * 5, list(range(1, 6)) * 2
    lid = ["A", "A", "B", "A", "A", "C", "D", "D", "E", "E"]
    y = [0.3, 1.9, -0.7, 2.4, 1.1, -1.2, 0.8, 1.5, -0.4, 0.2]
    e = R.preparar(u, t, lid, y)
    diff, _ = R.teste(e, 3, rng(2))
    g = rng(2)  # mesma sequência: refaz por fora as três ordens sorteadas
    perm = []
    for _ in range(3):
        ordem = np.lexsort((g.random(len(e["st_lid"])), e["st_unid"]))
        perm.append(r2_independente(e["y"], np.repeat(e["st_lid"][ordem], e["st_tam"][ordem])))
    real = r2_independente(e["y"], e["lid"])
    com_real = real - (sum(perm) + real) / 4
    sem_real = real - sum(perm) / 3
    return {
        "diff_teste": diff,
        "diff_com_linha_real": com_real,
        "diff_sem_linha_real": sem_real,
        "passa": bool(abs(diff - com_real) < 1e-12 and abs(diff - sem_real) > 1e-6),
    }


def bloco_nostitch():
    """Confere ``R.teste`` com ``stitch=False`` contra a enumeração exata.

    Returns
    -------
    dict
        Células, trechos, ordens, valor-p e Diferença exatos e de ``R.teste``, e ``passa``.
    """
    # unidade 1: A Z | falta | B B A (o A está nos dois trechos);
    # unidade 2: C C | falta | D (trecho de 1 linha)
    # unidade 3: E E E | falta | F G   ; o trecho "C C" tem um só líder e 2 linhas -> descartado
    u = [1] * 6 + [2] * 4 + [3] * 6
    t = [1, 2, 3, 4, 5, 6] + [1, 2, 3, 4] + [1, 2, 3, 4, 5, 6]
    lid = ["A", "Z", "x", "B", "B", "A", "C", "C", "x", "D", "E", "E", "E", "x", "F", "G"]
    y = [
        0.5,
        1.2,
        np.nan,
        -0.3,
        0.9,
        2.1,
        1.0,
        -0.6,
        np.nan,
        0.4,
        0.1,
        1.7,
        -0.8,
        np.nan,
        0.6,
        -1.1,
    ]
    e = R.preparar(u, t, lid, y, stitch=False)
    real, p_exato, media, n = enumerar(e)
    diff, p = R.teste(e, 200_000, rng(3))
    return {
        "celulas": len(e["y"]),
        "trechos": int(e["unid"].max()) + 1,
        "ordens": n,
        "p_exato": p_exato,
        "p_teste": p,
        "diff_exata": real - media,
        "diff_teste": diff,
        "passa": bool(abs(p - p_exato) < 0.01 and abs(diff - (real - media)) < 0.005),
    }


def ar1(n, T, g):
    """Gera ``n`` séries gaussianas AR(1) estacionárias de ``T`` períodos (variância 1).

    Parameters
    ----------
    n : int
        Número de séries.
    T : int
        Número de períodos por série.
    g : numpy.random.Generator
        Gerador de números aleatórios.

    Returns
    -------
    numpy.ndarray
        Matriz ``(n, T)``.
    """
    e = np.empty((n, T))
    e[:, 0] = g.normal(size=n)
    for k in range(1, T):
        e[:, k] = RHO * e[:, k - 1] + math.sqrt(1 - RHO**2) * g.normal(size=n)
    return e


def bloco_dois_municipios():
    """Mede P(Q_real > Q_invertida) e a rejeição de ``R.teste`` no exemplo de dois municípios.

    Returns
    -------
    dict
        Proporção ``p_q_real_maior`` e taxa de rejeição, com o número de bases de cada uma.
    """
    obs = [0, 1, 2, 4, 5]  # períodos 1, 2, 3, 5 e 6 (falta o 4)
    real, inv = [[0, 1], [2, 3, 4]], [[0, 1, 2], [3, 4]]
    g = rng(4)
    y = np.stack([ar1(400_000, 6, g), ar1(400_000, 6, g)], axis=1)[:, :, obs]
    r = y - y.mean(axis=1, keepdims=True)[:, :, :]

    def q(v, grupos):
        """Soma, sobre os grupos, do quadrado da soma de ``v`` dividido pelo tamanho do grupo."""
        return sum(v[:, k].sum(axis=1) ** 2 / len(k) for k in grupos)

    p_q = float((q(r[:, 0], real) > q(r[:, 0], inv)).mean())
    g = rng(5)
    u, t = [1] * 6 + [2] * 6, list(range(1, 7)) * 2
    lid = ["A", "A", "B", "B", "B", "B", "C", "C", "D", "D", "D", "D"]
    rej = 0
    for _ in range(4_000):
        yy = np.concatenate([ar1(1, 6, g)[0], ar1(1, 6, g)[0]])
        yy[[3, 9]] = np.nan
        _, p = R.teste(R.preparar(u, t, lid, yy), 200, g)
        rej += p <= 0.05
    return {
        "p_q_real_maior": p_q,
        "bases_q": 400_000,
        "rejeicao_teste": rej / 4_000,
        "bases_teste": 4_000,
    }


def main():
    """Roda os quatro blocos, imprime e grava o JSON; falha se algum bloco não passar."""
    out = {
        "semente": SEMENTE,
        "rho": RHO,
        "ponta": bloco_ponta(),
        "media_inclui_real": bloco_media(),
        "nostitch": bloco_nostitch(),
        "dois_municipios": bloco_dois_municipios(),
    }
    print(json.dumps(out, indent=1, ensure_ascii=False))
    SAIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    assert all(out[k]["passa"] for k in ("ponta", "media_inclui_real", "nostitch")), (
        "verificação falhou"
    )


if __name__ == "__main__":
    main()
