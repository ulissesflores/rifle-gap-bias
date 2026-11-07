"""As saídas congeladas são as registradas nas cadeias de hash do estudo de origem."""

import hashlib
import json

from conftest import RAIZ

ORIGEM = RAIZ / "data" / "origem"


def _linhas(nome):
    """Devolve as linhas (com o fim de linha) do manifesto ``<nome>.manifest.jsonl`` da origem."""
    return (ORIGEM / f"{nome}.manifest.jsonl").read_bytes().splitlines(keepends=True)


def test_cadeias_encadeadas():
    """Cada registro cita o sha256 da linha anterior (``prev_hash``) e a sequência é contínua."""
    for nome in ("piloto", "analise", "preregistro"):
        linhas = _linhas(nome)
        for k, linha in enumerate(linhas):
            reg = json.loads(linha)
            assert reg["seq"] == k + 1
            if k:
                assert reg["prev_hash"] == hashlib.sha256(linhas[k - 1]).hexdigest()


# Saídas do piloto antigo cujo MÓDULO foi registrado antes de rodar, mas cuja SAÍDA não entrou
# na cadeia (lacuna de proveniência declarada em REPRODUCIBILITY.md; o sha256 delas está fixado
# em montar_results.py desde 2026-10-31). Toda outra saída tem de estar registrada.
SEM_REGISTRO = {
    "diagnostico_borda.json",
    "diagnostico_costura.json",
    "simulacoes.json",
    "simulacoes_v2.json",
}


def test_congelado_esta_registrado():
    """O sha256 de cada saída congelada está na cadeia do seu módulo, salvo as quatro exceções."""
    fora = set()
    for pasta in ("piloto", "analise"):
        registrados = {json.loads(x)["sha256"] for x in _linhas(pasta)}
        for arq in (RAIZ / "data" / "congelado" / pasta).rglob("*.json"):
            if hashlib.sha256(arq.read_bytes()).hexdigest() not in registrados:
                fora.add(arq.name)
    assert fora == SEM_REGISTRO
