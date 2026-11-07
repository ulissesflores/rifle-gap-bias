#!/usr/bin/env python3
"""Gate figura/tabela <-> claim de um artigo codex-hash (PLAN §11, classes 1 e 2).

Prova mecanicamente tres coisas sobre o par (paper canonico, artefatos selados):

  (a) CITACAO BIDIRECIONAL — toda `Figura N`/`Tabela N` citada no paper tem arquivo
      correspondente em `output/figures/` / `output/tables/`, E todo arquivo gerado
      la e citado no paper. As duas direcoes falham: figura orfa e citacao morta sao
      o mesmo defeito visto de lados opostos.
  (b) NUMERO ANCORADO — todo numero que o texto marca com `<!-- num:<dot.path> -->`
      bate com o valor em `output/results.json`. O marcador vem IMEDIATAMENTE ANTES
      do numero que governa; o primeiro token numerico depois dele e o valor sob
      contrato. Arredondamento do texto e aceito (compara com o valor de results.json
      arredondado a mesma casa decimal exibida); alterar o digito nao e.
  (c) PARIDADE POR LOCALE — todo grafico/tabela com texto existe em TODOS os idiomas
      declarados em `locales/labels.<locale>.json`. Convencao de nome PLANA:
      `output/figures/figN_<slug>.<locale>.png`. Plana de proposito: `stages.json`
      sela `output/figures/*.png` (nao-recursivo), entao subpasta por idioma escaparia
      silenciosamente do estagio `figures` da cadeia de proveniencia.

Puro stdlib, offline. Exit 0 = tudo bate; exit 1 = ha violacao (toda violacao e
impressa com `[FAIL]`).

    python3 scripts/verify_figures.py                        # verifica ESTE projeto
    python3 scripts/verify_figures.py --fixture-positivo     # controle positivo -> 0
    python3 scripts/verify_figures.py --fixture-negativo figura-nao-citada
    python3 scripts/verify_figures.py --fixture-negativo numero-figura-divergente
    python3 scripts/verify_figures.py --fixture-negativo numero-tabela-divergente
    python3 scripts/verify_figures.py --fixture-negativo locale-faltando
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# `Figura 3` / `Figure 3` / `Tabela 2` / `Table 2` — o numero e o que importa.
CITACAO = re.compile(r"\b(?:Figura|Figure|Tabela|Table|Tabla|Tabella)\s+(\d+)\b", re.IGNORECASE)
E_FIGURA = re.compile(r"\b(?:Figura|Figure)\b", re.IGNORECASE)
# `<!-- num:results.a.b -->` seguido do numero que ele ancora.
MARCADOR = re.compile(r"<!--\s*num:([A-Za-z0-9_.\[\]-]+)\s*-->\s*\*{0,2}(-?[\d.,]+)")
# `fig3_slug.pt-br.png` -> ("fig3_slug", "pt-br");  `tab2_slug.en.md` -> ("tab2_slug", "en")
ARTEFATO = re.compile(r"^((?:fig|tab)\d+_[^.]+)\.([A-Za-z-]+)\.[a-z]+$")
NUMERO_NO_STEM = re.compile(r"^(?:fig|tab)(\d+)_")


def _num(texto: str, decimal: str = ",") -> Decimal:
    """Numero como o texto o exibe, nos separadores da edicao.

    ``decimal=","`` (pt-BR, es, it): virgula decimal e ponto de milhar; ``decimal="."`` (en):
    ponto decimal e virgula de milhar.
    """
    milhar = "." if decimal == "," else ","
    # grupo de milhar exige primeiro digito nao nulo: "0.031" e decimal, nunca 31
    grupo = re.escape(milhar)
    if re.fullmatch(rf"-?[1-9]\d{{0,2}}(?:{grupo}\d{{3}})+(?:{re.escape(decimal)}\d+)?", texto):
        texto = texto.replace(milhar, "")
    return Decimal(texto.replace(decimal, "."))


def _buscar(dados, caminho: str):
    """Dot-path em results.json; `a.b.0.c` desce por dict e por indice de lista."""
    alvo = dados
    for parte in caminho.split("."):
        if isinstance(alvo, list):
            alvo = alvo[int(parte)]
        else:
            alvo = alvo[parte]
    return alvo


def _ler_json(caminho: Path):
    """Lê e decodifica o JSON de ``caminho`` (UTF-8)."""
    return json.loads(caminho.read_text(encoding="utf-8"))


def _edicoes(raiz: Path) -> dict[str, Path]:
    """Edicoes do paper canonico: `paper-final.md` (pt-br) e `paper-final-<locale>.md`."""
    pasta = raiz / "docs" / "paper"
    edicoes = {}
    for p in sorted(pasta.glob("paper-final*.md")):
        resto = p.stem.removeprefix("paper-final")
        edicoes[resto.removeprefix("-") or "pt-br"] = p
    return edicoes


def _decimal(raiz: Path, loc: str) -> str:
    """Separador decimal do locale, lido de ``locales/labels.<locale>.json``."""
    labels = raiz / "locales" / f"labels.{loc}.json"
    if labels.exists():
        return _ler_json(labels).get("numero", {}).get("decimal", ",")
    return ","


def _artefatos(pasta: Path, sufixos: tuple[str, ...]) -> dict[str, dict[str, Path]]:
    """`{stem: {locale: caminho}}` dos arquivos que casam a convencao de nome."""
    fora: dict[str, dict[str, Path]] = {}
    for p in sorted(pasta.glob("*")):
        if p.suffix.lower() not in sufixos:
            continue
        m = ARTEFATO.match(p.name)
        if m:
            fora.setdefault(m.group(1), {})[m.group(2)] = p
    return fora


def verificar(raiz: Path) -> list[str]:
    """Devolve a lista de violacoes (vazia == tudo bate)."""
    problemas: list[str] = []

    publicados = raiz / "data" / "numeros_publicados.json"
    textos: dict[str, str] = {
        loc: p.read_text(encoding="utf-8") for loc, p in _edicoes(raiz).items()
    }
    if not textos and publicados.exists():
        # repositorio publico: o paper vai como PDF/DOCX, e o laboratorio exporta para
        # este JSON exatamente os trechos que este gate le (ancoras e citacoes), por edicao
        trechos = _ler_json(publicados)
        for loc, ed in trechos["edicoes"].items():
            textos[loc] = "\n".join(ed["ancoras"] + ed["citacoes"])
    if not textos:
        return [f"paper canonico ausente: {raiz}/docs/paper/paper-final*.md (nem {publicados})"]

    figuras = _artefatos(raiz / "output" / "figures", (".png", ".pdf", ".svg"))
    tabelas = _artefatos(raiz / "output" / "tables", (".md", ".csv", ".tex"))

    for loc, texto in textos.items():
        decimal = _decimal(raiz, loc)
        # ---- (a) citacao bidirecional ------------------------------------------------
        citados_fig: set[int] = set()
        citados_tab: set[int] = set()
        for m in CITACAO.finditer(texto):
            alvo = citados_fig if E_FIGURA.match(m.group(0)) else citados_tab
            alvo.add(int(m.group(1)))

        for rotulo, gerados, citados in (
            ("Figura", figuras, citados_fig),
            ("Tabela", tabelas, citados_tab),
        ):
            numerados = {int(NUMERO_NO_STEM.match(stem).group(1)): stem for stem in gerados}
            for n in sorted(citados - set(numerados)):
                problemas.append(f"[{loc}] {rotulo} {n} citada no paper e nao tem arquivo gerado")
            for n in sorted(set(numerados) - citados):
                problemas.append(
                    f"[{loc}] {rotulo} {n} gerada ({numerados[n]}) e NAO e citada no paper"
                )

        # ---- (b) numero ancorado -----------------------------------------------------
        results = raiz / "output" / "results.json"
        marcadores = list(MARCADOR.finditer(texto))
        if marcadores and not results.exists():
            problemas.append(f"paper ancora {len(marcadores)} numero(s) mas {results} nao existe")
        elif marcadores:
            dados = _ler_json(results)
            for m in marcadores:
                caminho, exibido = m.group(1), m.group(2).rstrip(".,")
                try:
                    valor = _buscar(dados, caminho.removeprefix("results."))
                except (KeyError, IndexError, ValueError, TypeError):
                    problemas.append(f"marcador <!-- num:{caminho} --> nao resolve em results.json")
                    continue
                try:
                    dito, real = _num(exibido, decimal), Decimal(str(valor))
                except Exception:
                    problemas.append(
                        f"marcador <!-- num:{caminho} --> nao compara: "
                        f"texto={exibido!r} results={valor!r}"
                    )
                    continue
                casas = -dito.as_tuple().exponent
                if dito != round(real, casas):
                    problemas.append(
                        f"[{loc}] numero divergente em <!-- num:{caminho} -->: "
                        f"paper diz {exibido}, "
                        f"results.json diz {valor}"
                    )

    # ---- (c) paridade por locale -------------------------------------------------
    locales = sorted(p.name.split(".")[1] for p in (raiz / "locales").glob("labels.*.json"))
    if not locales:
        problemas.append(f"nenhum locale declarado em {raiz}/locales/labels.<locale>.json")
    else:
        for rotulo, gerados in (("figura", figuras), ("tabela", tabelas)):
            for stem, por_locale in sorted(gerados.items()):
                for loc in locales:
                    if loc not in por_locale:
                        problemas.append(f"{rotulo} '{stem}' sem versao no locale '{loc}'")

    return problemas


# --------------------------------------------------------------------------- #
# fixtures — o gate prova a si mesmo, como provenance_chain.py._selftest       #
# --------------------------------------------------------------------------- #
FIXTURES = (
    "figura-nao-citada",
    "numero-figura-divergente",
    "numero-tabela-divergente",
    "locale-faltando",
)

_PAPER_OK = """# Artigo de teste

A Figura 1 mostra o piso de ruido medido em <!-- num:results.piso.sigma -->0.031 e a
Tabela 1 resume as <!-- num:results.corpus.n -->248 execucoes do corpus.
"""


def montar_fixture(raiz: Path, defeito: str | None) -> None:
    """Escreve em `raiz` um projeto minimo — correto, ou com UM defeito injetado."""
    for sub in ("docs/paper", "output/figures", "output/tables", "locales"):
        (raiz / sub).mkdir(parents=True, exist_ok=True)

    locales = ["pt-br"] if defeito == "locale-faltando" else ["pt-br", "en"]
    for loc in ("pt-br", "en"):
        (raiz / "locales" / f"labels.{loc}.json").write_text('{"_": "fixture"}', encoding="utf-8")
    for loc in locales:
        (raiz / "output" / "figures" / f"fig1_piso.{loc}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (raiz / "output" / "tables" / f"tab1_corpus.{loc}.md").write_text(
            "| n |\n|---|\n", encoding="utf-8"
        )
    if defeito == "figura-nao-citada":
        # figura 2 existe em todos os locales mas o paper nunca a menciona
        for loc in locales:
            (raiz / "output" / "figures" / f"fig2_orfa.{loc}.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    piso, n = "0.031", "248"
    if defeito == "numero-figura-divergente":
        piso = "0.041"  # o texto da legenda da Figura 1 diverge do results.json
    if defeito == "numero-tabela-divergente":
        n = "512"  # o numero da Tabela 1 diverge do results.json
    (raiz / "docs" / "paper" / "paper-final.md").write_text(
        _PAPER_OK.replace("0.031", piso).replace("248", n), encoding="utf-8"
    )
    (raiz / "output" / "results.json").write_text(
        json.dumps({"piso": {"sigma": 0.031}, "corpus": {"n": 248}}), encoding="utf-8"
    )
    # `locale-faltando` deixa o labels.en.json declarado sem os PNG/MD em `en`.


def rodar_fixture(defeito: str | None) -> int:
    """Roda o gate sobre uma fixture temporária, com ou sem defeito injetado.

    Parameters
    ----------
    defeito : str or None
        Defeito a injetar; ``None`` monta a fixture correta (controle positivo).

    Returns
    -------
    int
        1 se o gate reprovou a fixture, 0 se não achou violação.
    """
    with tempfile.TemporaryDirectory(prefix="verify-figures-fixture-") as tmp:
        raiz = Path(tmp)
        montar_fixture(raiz, defeito)
        problemas = verificar(raiz)
    rotulo = defeito or "positivo (projeto correto)"
    for p in problemas:
        print(f"[FAIL] {p}")
    if problemas:
        print(
            f"[FAIL] fixture '{rotulo}': {len(problemas)} violacao(oes) — "
            "gate REPROVOU (esperado para fixture negativa)"
        )
        return 1
    print(f"[PASS] fixture '{rotulo}': nenhuma violacao")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Roda o gate figura/tabela <-> claim sobre o projeto ou sobre uma fixture.

    Parameters
    ----------
    argv : list of str, optional
        Argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns
    -------
    int
        0 se o gate passou, 1 se houve violação.
    """
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--fixture-negativo",
        choices=FIXTURES,
        help="roda o gate sobre uma fixture com defeito injetado",
    )
    g.add_argument(
        "--fixture-positivo",
        action="store_true",
        help="controle positivo: fixture correta -> exit 0",
    )
    ap.add_argument(
        "--root", type=Path, default=ROOT, help="raiz do projeto (default: pai de scripts/)"
    )
    a = ap.parse_args(argv)

    if a.fixture_negativo:
        return rodar_fixture(a.fixture_negativo)
    if a.fixture_positivo:
        return rodar_fixture(None)

    problemas = verificar(a.root)
    for p in problemas:
        print(f"[FAIL] {p}")
    if problemas:
        print(f"[FAIL] {len(problemas)} violacao(oes) — GATE figura/tabela<->claim REPROVADO")
        return 1
    print("[PASS] figuras, tabelas, numeros ancorados e locales — tudo bate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
