#!/usr/bin/env python3
"""Teste de ponta a ponta de ``rifle_ado.teste``: sorteio, média com a linha real e valor-p estrito.

Pedido da terceira rodada de revisão (2026-11-02): os três testes de ``teste_rifle_ado.py``
conferem a preparação e o R², mas nenhum chama ``R.teste``. Aqui, num painel pequeno com um
líder que VOLTA (unidade 1: A A B A A) e outro sem retorno (unidade 2: C D D E E), todas as
6 x 6 = 36 ordens de passagens são enumeradas à mão. Como o sorteio do pacote é uniforme e
independente por unidade, o valor-p exato é a fração das 36 ordens com R² estritamente maior que
o real, e o valor-p de ``R.teste`` com muitas permutações tem de ficar perto dele. Também confere
a Diferença: real menos a média que inclui a linha real (l.149-152 do ado).

Semente do sorteio: 18112026 (nova, registrada na cadeia antes de rodar).
"""

import itertools

import numpy as np
import rifle_ado as R

SEMENTE, N_PERM = 18112026, 200_000


def painel():
    """Monta o painel de 2 unidades com líder que volta (A A B A A; C D D E E).

    Returns
    -------
    dict
        Painel preparado por ``R.preparar``.
    """
    u = [1] * 5 + [2] * 5
    t = list(range(1, 6)) * 2
    lid = ["A", "A", "B", "A", "A", "C", "D", "D", "E", "E"]
    y = [0.3, 1.9, -0.7, 2.4, 1.1, -1.2, 0.8, 1.5, -0.4, 0.2]
    return R.preparar(u, t, lid, y)


def exato(e):
    """Valor-p e média exatos, enumerando as ordens de passagens de cada unidade."""
    real = R.r2(e["y"], e["lid"], e["nlid"])
    por_unid = [np.flatnonzero(e["st_unid"] == k) for k in np.unique(e["st_unid"])]
    r2s = []
    for ordens in itertools.product(*(itertools.permutations(ix) for ix in por_unid)):
        ordem = np.concatenate(ordens)
        lid2 = np.repeat(e["st_lid"][ordem], e["st_tam"][ordem])
        r2s.append(R.r2(e["y"], lid2, e["nlid"]))
    r2s = np.array(r2s)
    return real, float((r2s > real).mean()), float(r2s.mean()), len(r2s)


def test_teste_ponta_a_ponta():
    """``R.teste`` fica perto do valor-p e da Diferença exatos das 36 ordens."""
    e = painel()
    assert e["st_tam"].tolist() == [2, 1, 2, 1, 2, 2]  # A, B, A de volta; C, D, E
    real, p_exato, media_exata, n = exato(e)
    assert n == 36
    diff, p = R.teste(e, N_PERM, np.random.default_rng(SEMENTE))
    assert abs(p - p_exato) < 0.01, (p, p_exato)
    # Diferença = real - média (permutações + linha real) / (n + 1);
    # com n grande ~ real - média exata
    assert abs(diff - (real - media_exata)) < 0.005, (diff, real - media_exata)


if __name__ == "__main__":
    test_teste_ponta_a_ponta()
    print("ok")
