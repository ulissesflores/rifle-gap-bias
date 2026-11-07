#!/usr/bin/env python3
"""Gera as TABELAS DE DADOS do artigo a partir de `output/results.json` (PLAN §11, classe 2).

Mesma fonte das figuras, mesma disciplina: numero de tabela nunca e digitado no paper.
Cada celula numerica sai ANCORADA no marcador que `verify_figures.py` cobra:

    <!-- num:results.<dot.path> -->valor

O marcador vem imediatamente ANTES do numero que governa. Assim, editar o texto sem
reexecutar a analise vira falha mecanica, nao revisao humana.

Um arquivo por locale, nome PLANO (mesma razao de proveniencia das figuras):

    output/tables/tabN_<slug>.<locale>.md

TEMPLATE: `tab1_exemplo` e um exemplo executavel para ser SUBSTITUIDO pelas tabelas
reais. Cada tabela vira uma funcao `tabN_<slug>(results, rotulos) -> list[list[Celula]]`
registrada em `TABELAS`.

    python3 scripts/make_tables.py
    python3 scripts/make_tables.py --locale en
"""

from __future__ import annotations

import argparse
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES = ROOT / "output" / "tables"


class Num:
    """Celula numerica ancorada em `results.json`: renderiza `<!-- num:path -->valor`."""

    def __init__(self, caminho: str, valor, casas: int | None = None):
        """Guarda o caminho da âncora, o valor e o número de casas decimais.

        Parameters
        ----------
        caminho : str
            Caminho pontuado do valor em ``results.json``.
        valor : int or float
            Valor numérico a exibir.
        casas : int, optional
            Casas decimais; ``None`` exibe o valor como está.
        """
        self.caminho, self.valor, self.casas = caminho, valor, casas

    def __str__(self) -> str:
        """Devolve a âncora ``<!-- num:caminho -->`` seguida do valor formatado."""
        texto = f"{self.valor:.{self.casas}f}" if self.casas is not None else f"{self.valor}"
        return f"<!-- num:{self.caminho} -->{texto}"


def carregar_results() -> dict:
    """Lê ``output/results.json``, a única fonte de número; ausente é erro alto.

    Returns
    -------
    dict
        Conteúdo de ``results.json``.
    """
    p = ROOT / "output" / "results.json"
    if not p.exists():
        raise SystemExit(f"[FAIL] {p} nao existe — rode a analise (fase A7) antes de montar tabela")
    return json.loads(p.read_text(encoding="utf-8"))


def carregar_locales(apenas: str | None) -> dict[str, dict]:
    """Carrega os dicionários de rótulos de ``locales/labels.<locale>.json``.

    Parameters
    ----------
    apenas : str or None
        Se dado, devolve só este locale; ``None`` devolve todos os declarados.

    Returns
    -------
    dict
        Locale -> dicionário de rótulos.
    """
    achados = sorted((ROOT / "locales").glob("labels.*.json"))
    if not achados:
        raise SystemExit(
            f"[FAIL] nenhum {ROOT}/locales/labels.<locale>.json — declare ao menos um idioma"
        )
    fora = {p.name.split(".")[1]: json.loads(p.read_text(encoding="utf-8")) for p in achados}
    if apenas:
        if apenas not in fora:
            raise SystemExit(f"[FAIL] locale '{apenas}' nao declarado (tem: {', '.join(fora)})")
        return {apenas: fora[apenas]}
    return fora


def render_md(rotulos: dict, linhas: list[list]) -> str:
    """GFM puro: so pipe. Layout fixo e largura de coluna sao do estagio DOCX (canon)."""
    colunas = list(rotulos["colunas"].values())
    corpo = [f"| {' | '.join(colunas)} |", f"|{'---|' * len(colunas)}"]
    corpo += [f"| {' | '.join(str(c) for c in linha)} |" for linha in linhas]
    fonte = rotulos.get("fonte", "")
    return "\n".join([f"**{rotulos['titulo']}**", "", *corpo, "", fonte, ""])


# --------------------------------------------------------------------------- #
# tabelas — SUBSTITUIR pelas do artigo                                        #
# --------------------------------------------------------------------------- #
class NumBR(Num):
    """Como `Num`, com os separadores do locale só no VALOR e arredondamento decimal exato.

    O caminho da âncora mantém os pontos. O arredondamento é meio para cima:
    `round()` binário fazia 2,15 virar 2,1. ``SEP`` é trocado por locale em ``main``.
    """

    SEP = {"decimal": ",", "milhar": "."}

    def __str__(self) -> str:
        """Devolve a âncora seguida do valor nos separadores do locale, arredondado em decimal."""
        troca = str.maketrans({",": self.SEP["milhar"], ".": self.SEP["decimal"]})
        if self.casas is None:
            if isinstance(self.valor, int):
                # milhar como no texto (10.000 / 10,000)
                return f"<!-- num:{self.caminho} -->{f'{self.valor:,}'.translate(troca)}"
            return super().__str__()
        q = Decimal(str(self.valor)).quantize(
            Decimal(1).scaleb(-self.casas), rounding=ROUND_HALF_UP
        )
        return f"<!-- num:{self.caminho} -->{str(q).translate(troca)}"


# (bloco de resultados, chave da célula): todas as células do pacote fiel citadas no texto
CELULAS = (
    [
        ("ado", k)
        for k in (
            "sem_lacuna",
            "p9",
            "meio",
            "p9_rho0",
            "p9_nostitch",
            "aleatoria_nostitch",
            "sem_lacuna_poder",
            "meio_poder",
        )
    ]
    + [
        ("ado_juizes", k)
        for k in (
            "sem_lacuna_meio867",
            "sem_lacuna_poder10_meio867",
            "p9_nostitch_poder10",
            "aleatoria2_nostitch_poder10",
            "sem_lacuna_poder05",
            "p9_nostitch_poder05",
        )
    ]
    + [("ado_escala", f"{c}_N5468") for c in ("p9", "na_troca", "aleatoria")]
    + [
        ("ado_juizes", k)
        for k in (
            "sem_lacuna_N5468",
            "p9_nostitch_N5468",
            "na_troca_nostitch_N5468",
            "aleatoria_nostitch_N5468",
        )
    ]
    + [
        ("ado_mascara_real", k)
        for k in ("interior_costura", "interior_nostitch", "so_borda_costura")
    ]
)


def tab1_celulas(results: dict, rotulos: dict) -> list[list]:
    """Monta a tabela de desenho e resultado de cada célula.

    As colunas são N efetivo, lacuna, tratamento, ρ, efeito, rejeição e intervalo.

    Parameters
    ----------
    results : dict
        Conteúdo de ``results.json``.
    rotulos : dict
        Rótulos do locale para a tabela.

    Returns
    -------
    list of list
        Uma linha por célula de ``CELULAS``.
    """
    linhas = []
    for bloco, k in CELULAS:
        c = results[bloco]["celulas"][k]
        n_campo = "N" if "N" in c else "municipios"
        lacuna = (
            c.get("lacuna")
            or c.get("condicao")
            or rotulos["mascara_real"][k.split("_")[0] + ("_borda" if "borda" in k else "")]
        )
        modo = c.get("modo") or ("nostitch" if "nostitch" in k else "costura")
        modo = rotulos.get("modo", {}).get(modo, modo)
        rho = c.get("rho", 0.21696453979704527)
        linhas.append(
            [
                rotulos["modulo"][bloco],
                NumBR(f"{bloco}.celulas.{k}.{n_campo}", c[n_campo]),
                NumBR(f"{bloco}.celulas.{k}.celulas", c["celulas"]) if "celulas" in c else "—",
                rotulos["lacuna"].get(lacuna, lacuna),
                modo,
                f"{rho:.3f}".replace(".", NumBR.SEP["decimal"]),
                f"{c.get('prop', 0.0):.0%}",
                NumBR(f"{bloco}.celulas.{k}.taxa_pct", c["taxa_pct"], casas=1),
                f"{NumBR(f'{bloco}.celulas.{k}.ic95_pct.0', c['ic95_pct'][0], casas=2)}"
                f"{rotulos.get('ate', ' a ')}"
                f"{NumBR(f'{bloco}.celulas.{k}.ic95_pct.1', c['ic95_pct'][1], casas=2)}",
            ]
        )
    return linhas


TABELAS = {"tab1_celulas": tab1_celulas}


def main(argv: list[str] | None = None) -> int:
    """Gera as tabelas Markdown de cada locale declarado em ``output/tables/``.

    Parameters
    ----------
    argv : list of str, optional
        Argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns
    -------
    int
        Código de saída (0 = tudo gerado).
    """
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--locale", help="gerar so este idioma (default: todos os declarados)")
    a = ap.parse_args(argv)

    results = carregar_results()
    locales = carregar_locales(a.locale)
    TABLES.mkdir(parents=True, exist_ok=True)

    escritos = 0
    for loc, labels in locales.items():
        NumBR.SEP = labels.get("numero", {"decimal": ",", "milhar": "."})
        for stem, montar in TABELAS.items():
            rotulos = labels.get("tabelas", {}).get(stem)
            if rotulos is None:
                raise SystemExit(
                    f"[FAIL] labels.{loc}.json nao tem rotulos para '{stem}' — "
                    "paridade por locale e gate"
                )
            destino = TABLES / f"{stem}.{loc}.md"
            destino.write_text(render_md(rotulos, montar(results, rotulos)), encoding="utf-8")
            print(f"[ok] {destino.relative_to(ROOT)}")
            escritos += 1
    print(f"[PASS] {escritos} tabela(s) em {len(locales)} locale(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
