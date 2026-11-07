#!/usr/bin/env python3
"""Tradução fiel do ``rifle.ado`` oficial (Berry e Fowler, SSC 2018, sha 49577978…) para Python.

Não há Stata nesta máquina. A revisão independente (2026-10-31) mostrou que o nosso motor
(``rifle_sim``) difere do ado em pontos que podem mudar a conclusão sobre o ``nostitch``. Este
módulo reproduz o ado passo a passo, com a linha correspondente citada:

- l.33-37: residualiza o resultado por período (``reg y i.period``); o ``reg`` do Stata usa só as
  linhas com resultado observado, então é descontar a média do período nas células observadas;
- l.41-47: ``leaderid = group(leader)`` é a IDENTIDADE GLOBAL do líder; linhas com faltante saem;
- l.49-56 (padrão, costura): o tempo é renumerado 1..n dentro da unidade, emendando as lacunas;
- l.58-76 (``nostitch``): cada bloco contíguo vira a unidade; sai o bloco cujo ``sd(leader_id)`` é
  0 (um só líder com 2+ linhas); bloco de UMA linha tem ``sd`` faltante no Stata e FICA;
- l.83: R² real de ``areg y, absorb(leader)``: grupos = identidade do líder;
- l.88-92: ``stint`` muda quando o líder ou a unidade muda, na ordem (unidade, tempo);
- l.103-120: cada permutação sorteia a ordem dos stints na unidade e recoloca a IDENTIDADE do
  líder do stint nas posições, mantendo a duração; R² de ``areg y, absorb(leader2)``;
- l.142-158: valor-p = fração de permutações com R² ESTRITAMENTE maior que o real; a média
  usada na Diferença inclui a linha do dado real (``sum r2`` sobre todas as linhas).

Entrada: arrays por célula (unidade, período de calendário, líder, y com NaN para faltante).
"""

import numpy as np


def preparar(unidade, periodo, lider, y, stitch=True):
    """Passos l.33-92 do ado. Devolve a estrutura pronta para o teste."""
    unidade, periodo, lider, y = map(np.asarray, (unidade, periodo, lider, y))
    obs = ~np.isnan(y)
    # l.33-37: resíduo do período nas células observadas
    _, pinv = np.unique(periodo[obs], return_inverse=True)
    yo = y[obs] - (np.bincount(pinv, weights=y[obs]) / np.bincount(pinv))[pinv]
    u, t, lid = unidade[obs], periodo[obs], lider[obs]
    _, lid = np.unique(lid, return_inverse=True)  # l.42 identidade global
    ordem = np.lexsort((t, u))
    u, t, lid, yo = u[ordem], t[ordem], lid[ordem], yo[ordem]
    if stitch:
        _, unid = np.unique(u, return_inverse=True)
    else:
        # l.58-76: bloco contíguo = nova unidade; sai bloco de 2+ linhas com um só líder
        quebra = np.r_[True, (u[1:] != u[:-1]) | (t[1:] != t[:-1] + 1)]
        bloco = np.cumsum(quebra) - 1
        nb = bloco.max() + 1
        tam = np.bincount(bloco, minlength=nb)
        # sd(leader_id) == 0 <=> todos iguais; com uma linha o sd é faltante e o bloco fica
        lmin = np.full(nb, np.iinfo(np.int64).max)
        lmax = np.full(nb, -1)
        np.minimum.at(lmin, bloco, lid)
        np.maximum.at(lmax, bloco, lid)
        fica = ~((tam >= 2) & (lmin == lmax))
        sel = fica[bloco]
        u, t, lid, yo, bloco = u[sel], t[sel], lid[sel], yo[sel], bloco[sel]
        _, unid = np.unique(bloco, return_inverse=True)
    # l.88-92: stint muda com o líder ou a unidade
    novo = np.r_[True, (lid[1:] != lid[:-1]) | (unid[1:] != unid[:-1])]
    stint = np.cumsum(novo) - 1
    st_unid = unid[novo]
    st_lid = lid[novo]
    st_tam = np.bincount(stint)
    return {
        "y": yo,
        "lid": lid,
        "unid": unid,
        "st_unid": st_unid,
        "st_lid": st_lid,
        "st_tam": st_tam,
        "nlid": int(lid.max()) + 1,
    }


def r2(y, grupo, nlid):
    """R² de ``areg y, absorb(grupo)``: 1 - SQ dentro dos grupos / SQ total."""
    soma = np.bincount(grupo, weights=y, minlength=nlid)
    n = np.bincount(grupo, minlength=nlid)
    ssb = (soma[n > 0] ** 2 / n[n > 0]).sum() - y.sum() ** 2 / len(y)
    sst = ((y - y.mean()) ** 2).sum()
    return ssb / sst


def teste(e, n_perm, rng):
    """l.83-158: R² real, permutações dos stints e valor-p (estritamente maior)."""
    real = r2(e["y"], e["lid"], e["nlid"])
    perm = np.empty(n_perm)
    for k in range(n_perm):
        ordem = np.lexsort((rng.random(len(e["st_lid"])), e["st_unid"]))  # l.104-106
        lid2 = np.repeat(e["st_lid"][ordem], e["st_tam"][ordem])  # l.108-120
        perm[k] = r2(e["y"], lid2, e["nlid"])
    media = (perm.sum() + real) / (n_perm + 1)  # l.149-152
    return real - media, float((perm > real).mean())  # l.144-156
