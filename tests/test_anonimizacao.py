"""O painel público não traz CPF nem nome, e mantém a estrutura usada nas simulações."""

import csv
import re

import painel
from conftest import RAIZ


def test_sem_identificador_pessoal():
    """Nenhum arquivo de ``data/`` contém CPF, e o código de prefeito tem dois dígitos."""
    cpf = re.compile(r"cpf|\d{3}\.?\d{3}\.?\d{3}-?\d{2}", re.IGNORECASE)
    for arq in (RAIZ / "data").rglob("*.csv"):
        assert not cpf.search(arq.read_text(encoding="utf-8")), arq
    with (RAIZ / "data" / "mandatos.csv").open(encoding="utf-8") as f:
        assert all(re.fullmatch(r"\d{2}", r["prefeito"]) for r in csv.DictReader(f))


def test_painel_do_artigo():
    """5.468 municípios com prefeito nos dez períodos e ao menos dois prefeitos (Seção 4.2)."""
    assert len(painel.lideres()) == 5468
