"""As verificações do port refeitas aqui reproduzem bit a bit a saída congelada da origem."""

import json

import verificacoes_port as V
from conftest import RAIZ

CONGELADO = RAIZ / "data" / "congelado" / "piloto" / "saidas" / "verificacoes_port.json"


def test_enumeracao_media_e_nostitch_iguais_ao_congelado():
    """Os três blocos determinísticos dão exatamente o que foi publicado."""
    ref = json.loads(CONGELADO.read_text(encoding="utf-8"))
    assert V.bloco_ponta() == ref["ponta"]
    assert V.bloco_media() == ref["media_inclui_real"]
    assert V.bloco_nostitch() == ref["nostitch"]


def test_todos_os_blocos_passam():
    """As verificações publicadas passaram (valor-p a 0,01 do exato; média com a linha real)."""
    ref = json.loads(CONGELADO.read_text(encoding="utf-8"))
    assert all(ref[k]["passa"] for k in ("ponta", "media_inclui_real", "nostitch"))
