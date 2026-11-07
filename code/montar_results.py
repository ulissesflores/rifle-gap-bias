#!/usr/bin/env python3
"""Monta ``output/results.json``, a ÚNICA fonte de número do paper, a partir das saídas seladas.

Cada arquivo de origem tem o sha256 fixado aqui. Se algum mudar, o script para e nada é
escrito. O ``results.json`` reproduz os JSONs de origem (sob a chave de cada um) e acrescenta só
derivados determinísticos: intervalos exatos de Clopper-Pearson para as taxas de rejeição e
as contagens de rejeições.

Origem: ``data/congelado/`` (cópias das saídas do estudo de origem, com o sha256 fixado
abaixo). Cadeias de hash das origens: ``data/origem/{piloto,analise,preregistro}.manifest.jsonl``.

    python code/montar_results.py [--origem <pasta>]
"""

import argparse
import hashlib
import json
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
ORIGEM_PADRAO = ROOT / "data" / "congelado"
FONTES = {
    "costura": (
        "piloto/saidas/diagnostico_costura.json",
        "7f39dd98b518134891782bf13ffcad1e2a422591c58c5200e83856e609debf57",
    ),
    "borda": (
        "piloto/saidas/diagnostico_borda.json",
        "04e13d5fc4d4d685e98aa6a2824b1422a4b5f700ccd96ba1be212b61990cac16",
    ),
    "piloto_v1": (
        "piloto/saidas/simulacoes.json",
        "f598bf57298e3000b362ee97bb3a63163337e93990e5ec1b5b0890449c91b00c",
    ),
    "piloto_v2": (
        "piloto/saidas/simulacoes_v2.json",
        "767352b4dccf6c51a234efce24d3c95f00de96e90ed4c7cb6f7a5772d8ec67dd",
    ),
    "confirmacao": (
        "piloto/saidas/confirmacao_tamanho_v2.json",
        "0c98e2ab1a0a4a46b4119653a78b0118400da37688753fc5f660000a2ebf2616",
    ),
    "resultado": (
        "analise/saidas/resultado_v2.json",
        "31c3598ad61009090accb8d3ab3cc1588cbdab2483b49abb7cece19fe83e346d",
    ),
    "corrigido": (
        "analise/saidas/resultado_v2_corrigido.json",
        "cfd199cd9c56ed239ac46305fcb8e02f6227ffded9e7c656a6e40348ca7bb592",
    ),
    "d1_d4": (
        "analise/saidas/diagnostico_calibracao.json",
        "c0e7d7b769858c5ee34a67948569d268fa8f9f3257eaa1965e6b83b41db26414",
    ),
    "d5": (
        "analise/saidas/diagnostico_heterocedasticidade.json",
        "ac71aff0aadaa6784e55e8d49db593e42e8277ea1c7a190eb47f5c64d5768fce",
    ),
    "alinhamento_motor": (
        "piloto/saidas/diagnostico_alinhamento.json",
        "5491adba73d5cff5f1adfcabbbe71c086a1cfb2d1790db1d880cac7c365e9bd4",
    ),
    "escala_motor": (
        "piloto/saidas/diagnostico_escala.json",
        "5ff43eb1806a11c623d18561ae322bb2c32bb83aa48118a5212dfeead24b52bf",
    ),
    "ado": (
        "piloto/saidas/diagnostico_ado.json",
        "f3061d971801a02535ea0b08bc223b7bc176cb76b30cf7d5a42503b74fb89326",
    ),
    "ado_escala": (
        "piloto/saidas/diagnostico_ado_escala.json",
        "f3f25245229b88af2070de9646e9489e193845ec216c1e7827f3cc908aac1563",
    ),
    "ado_mascara_real": (
        "piloto/saidas/diagnostico_ado_mascara_real.json",
        "d7f31226cacb48d9d4f5914cbe3031a03a2f7b88febd46ae45fffbd69bd8734f",
    ),
    "ado_juizes": (
        "piloto/saidas/diagnostico_ado_juizes.json",
        "1f2d332e746edb57ccca6db0defc13f02968582bd1cf81dffbb60e8e19e40e5c",
    ),
    "verificacoes_port": (
        "piloto/saidas/verificacoes_port.json",
        "c94011105838a44e05cc27fc449913d3737c7170caa026b2fd8367faea9201e9",
    ),
    "iptu": (
        "analise/saidas/nota_iptu.json",
        "2ca51b33c91029462a49816e654032ac4fb2fa6135ba1d31f214f0b0455b7d28",
    ),
    "astra_reproducao": (
        "analise/revisao-astra/astra_reproducao.json",
        "60e33ec83941dc68f92331f3fda0e5d9ff602a9e3f93edbbbe0d10e963c3e095",
    ),
    "astra_simulacoes": (
        "analise/revisao-astra/astra_simulacoes.json",
        "48684b8d607838cfd7d0477fd323b93ec55ba28f88137b4e808d85050a924188",
    ),
    "astra_injecao": (
        "analise/revisao-astra/astra_injecao.json",
        "0af55d4b38f5ad03474cd121e3faa64fabb4003e67e043f0b23263b22cef3307",
    ),
    "astra_decomposicao": (
        "analise/revisao-astra/astra_decomposicao.json",
        "980a81c1761bc701fe16d45fa96be50cd8a5d519ea903ce99eb293a79f75b33e",
    ),
}


def ic(taxa, bases):
    """Rejeições e intervalo exato de 95% (Clopper-Pearson) de uma taxa medida em ``bases``."""
    k = round(taxa * bases)
    ci = binomtest(k, bases).proportion_ci(confidence_level=0.95, method="exact")
    return {
        "rejeicoes": k,
        "bases": bases,
        "taxa": k / bases,
        "ic95": [round(ci.low, 4), round(ci.high, 4)],
    }


PCT = {
    "p_q_real_maior",
    "rejeicao_teste",
    "taxa",
    "poder_T1",
    "fracao_abaixo_do_limiar_T2_selado",
    "T1",
    "T2",
    "fracao_lacuna_vizinha_de_troca",
    "fracao_mesma_pessoa_dos_dois_lados",
    "concentracao_SS_10pct",
    "D1_parte_entre_municipios_real",
}


def com_pct(x):
    """Acrescenta ``<chave>_pct`` (valor x 100) ao lado de taxas e frações, para citar em %."""
    if isinstance(x, dict):
        extra = {}
        for k, v in x.items():
            if k in PCT and isinstance(v, (int, float)) and not isinstance(v, bool):
                extra[f"{k}_pct"] = round(v * 100, 6)
            if k in ("ic95", "T1_IC95", "T2_IC95") and isinstance(v, list) and len(v) == 2:
                extra[f"{k}_pct"] = [round(float(a) * 100, 6) for a in v]
            com_pct(v)
        x.update(extra)
    elif isinstance(x, list):
        for v in x:
            com_pct(v)
    return x


def main():
    """Confere o sha256 de cada origem, monta ``results.json`` e o grava.

    Uma origem com sha256 diferente aborta com ``SystemExit`` sem escrever nada.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", type=Path, default=ORIGEM_PADRAO)
    a = ap.parse_args()
    res = {"fontes": {}}
    for chave, (rel, sha) in FONTES.items():
        dado = (a.origem / rel).read_bytes()
        h = hashlib.sha256(dado).hexdigest()
        if h != sha:
            raise SystemExit(f"[FAIL] {rel}: sha256 {h} != {sha}")
        res["fontes"][chave] = {"caminho": rel, "sha256": sha}
        res[chave] = json.loads(dado)
    # tamanho sob nulo da costura e da borda, com intervalo exato
    tam = {}
    for chave in ("costura", "borda"):
        for nome, r in res[chave]["rodadas"].items():
            tam[nome] = {
                **ic(r["rejeicao_sob_nulo"], r["bases"]),
                "rho": r["rho"],
                "municipios": r["municipios"],
            }
    res["tamanho_sob_nulo"] = tam
    com_pct(res)
    out = ROOT / "output" / "results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {out} ({len(FONTES)} fontes conferidas)")


if __name__ == "__main__":
    main()
