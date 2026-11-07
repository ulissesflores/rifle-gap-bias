#!/usr/bin/env python3
"""Confere ``rifle_ado`` contra contas feitas à mão num painel pequeno (sem sorteio)."""

import numpy as np
import rifle_ado as R


def r2_mao(y, grupos):
    """R² de efeitos fixos de grupo, calculado de forma independente (dicionário de grupos)."""
    g = {}
    for v, k in zip(y, grupos, strict=False):
        g.setdefault(k, []).append(v)
    ssw = sum(((np.array(v) - np.mean(v)) ** 2).sum() for v in g.values())
    return 1 - ssw / ((np.array(y) - np.mean(y)) ** 2).sum()


def test_costura_e_permutacao():
    """A costura e uma permutação forçada dão os resíduos e o R² feitos à mão."""
    # unidade A: x x y y nos períodos 1-4; unidade B: z w w nos períodos 1-3
    u = ["A"] * 4 + ["B"] * 3
    t = [1, 2, 3, 4, 1, 2, 3]
    lid = ["x", "x", "y", "y", "z", "w", "w"]
    y = [1.0, 2.0, 3.0, 4.0, 0.0, 1.0, 5.0]
    e = R.preparar(u, t, lid, y)
    # resíduos à mão: médias de período 0,5 1,5 4 4
    res = [0.5, 0.5, -1.0, 0.0, -0.5, -0.5, 1.0]
    assert np.allclose(e["y"], res)
    assert np.isclose(R.r2(e["y"], e["lid"], e["nlid"]), r2_mao(res, lid))
    # permutação forçada: B passa a w w z (stints em ordem invertida); A mantém
    ordem = np.array([0, 1, 3, 2])  # stints: A:x, A:y, B:z, B:w
    lid2 = np.repeat(e["st_lid"][ordem], e["st_tam"][ordem])
    nomes = sorted(set(lid))
    esperado = ["x", "x", "y", "y", "w", "w", "z"]
    assert [nomes[i] for i in lid2] == esperado
    assert np.isclose(R.r2(e["y"], lid2, e["nlid"]), r2_mao(res, esperado))


def test_costura_funde_mesma_pessoa():
    """A mesma pessoa dos dois lados de uma lacuna vira um só trecho depois da costura."""
    # a b [lacuna] b c: costurado vira a b b c, e b vira UM stint (ado l.88-92)
    e = R.preparar(["A"] * 4, [1, 2, 4, 5], ["a", "b", "b", "c"], [0.0, 1.0, 2.0, 3.0])
    assert list(e["st_tam"]) == [1, 2, 1]


def test_nostitch_blocos():
    """Sem costura, o bloco de um líder só sai e o de uma linha fica."""
    # unidade A: 1,2 (a b) | 4 (b): os dois blocos ficam (o de uma linha tem sd faltante)
    # unidade B: 1,2 (c c) | 4,5 (d e): o primeiro sai (sd = 0), o segundo fica
    u = ["A", "A", "A", "B", "B", "B", "B"]
    t = [1, 2, 4, 1, 2, 4, 5]
    lid = ["a", "b", "b", "c", "c", "d", "e"]
    e = R.preparar(u, t, lid, [1.0, 2, 3, 4, 5, 6, 7], stitch=False)
    assert len(e["y"]) == 5
    assert len(set(e["unid"].tolist())) == 3
    # a mesma pessoa (b) nos dois blocos de A continua com a mesma identidade (absorb leader)
    nomes = sorted(set(lid))
    assert [nomes[i] for i in e["lid"][:3]] == ["a", "b", "b"]


if __name__ == "__main__":
    test_costura_e_permutacao()
    test_costura_funde_mesma_pessoa()
    test_nostitch_blocos()
    print("ok: 3 testes")
