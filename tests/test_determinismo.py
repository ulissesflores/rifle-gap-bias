"""Uma célula pequena do pacote fiel, rodada duas vezes com a mesma semente, dá o mesmo valor."""

import diagnostico_ado as A


def test_celula_pequena_reproduz(monkeypatch):
    """Lacuna no período 9 com costura, 3 bases e 50 permutações: as duas rodadas são idênticas."""
    monkeypatch.setattr(A, "BASES", 3)
    monkeypatch.setattr(A, "PERM", 50)
    assert A.rodar(1) == A.rodar(1)
