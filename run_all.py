#!/usr/bin/env python3
"""Replica em um comando o artigo deste pacote.

Artigo: "O prefeito melhora a cidade além do acaso? Dado faltando na troca de prefeito faz o
teste dizer que sim".

Caminho leve (padrão, minutos): confere a cadeia de proveniência da última rodada selada, roda os
testes (todo número do paper contra ``output/results.json``, o port contra contas feitas à mão e
contra enumeração exata, a anonimização, as cadeias do estudo de origem e o determinismo) e remonta
resultados, tabela e figuras a partir dos dados congelados.

    python run_all.py

Caminho completo (horas de CPU): refaz, a partir do painel anonimizado, as cinco simulações do
pacote fiel e exige que cada saída seja idêntica, byte a byte, à congelada em ``data/congelado/``.

    python run_all.py --completo

O que não é refeito aqui está em REPRODUCIBILITY.md (as simulações do motor próprio do estudo, o
piloto antigo e a análise dos dados reais, que dependem de dados com CPF).
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPLETOS = [
    "verificacoes_port",
    "diagnostico_ado",
    "diagnostico_ado_mascara_real",
    "diagnostico_ado_escala",
    "diagnostico_ado_juizes",
]


def rodar(*cmd):
    """Roda um comando a partir da raiz e para tudo se ele falhar.

    Parameters
    ----------
    *cmd : str
        Programa e argumentos.
    """
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f"[FAIL] {' '.join(cmd)} saiu com {r.returncode}")


def completo():
    """Refaz as simulações do pacote fiel e compara cada saída com a congelada."""
    (ROOT / "output" / "rerun").mkdir(parents=True, exist_ok=True)
    for m in COMPLETOS:
        rodar(sys.executable, f"code/{m}.py")
    divergentes = []
    for m in COMPLETOS:
        novo = (ROOT / "output" / "rerun" / f"{m}.json").read_bytes()
        congelado = (ROOT / "data" / "congelado" / "piloto" / "saidas" / f"{m}.json").read_bytes()
        igual = hashlib.sha256(novo).digest() == hashlib.sha256(congelado).digest()
        print(f"{'[OK]  ' if igual else '[FAIL]'} {m}: refeito {'=' if igual else '!='} congelado")
        if not igual:
            divergentes.append(m)
    if divergentes:
        sys.exit(f"[FAIL] {len(divergentes)} saída(s) diferente(s) da congelada")


def main():
    """Executa o caminho leve e, com ``--completo``, também a rodada completa."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--completo", action="store_true", help="refaz as simulações (horas de CPU)")
    a = ap.parse_args()
    rodar(sys.executable, "scripts/verify_chain.py")
    rodar(sys.executable, "-m", "pytest", "-q", "tests")
    rodar(sys.executable, "code/montar_results.py")
    rodar(sys.executable, "scripts/make_tables.py")
    rodar(sys.executable, "scripts/make_figures.py")
    rodar(sys.executable, "scripts/verify_figures.py")
    if a.completo:
        completo()
    rodar(sys.executable, "scripts/verify_chain.py")
    print("[PASS] replicação concluída; cadeia íntegra")


if __name__ == "__main__":
    main()
