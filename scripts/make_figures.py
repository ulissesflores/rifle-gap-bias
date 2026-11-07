#!/usr/bin/env python3
"""Gera as FIGURAS DE DADOS do artigo a partir de `output/results.json` (PLAN §11, classe 1).

Figura de dado nasce de codigo lendo o resultado selado — nunca desenhada a mao, nunca
por LLM de imagem. Um DATASET POR LOCALE: o grafico e redesenhado para cada idioma
declarado em `locales/labels.<locale>.json`, trocando so o dicionario de rotulos; os
NUMEROS vem sempre do mesmo `results.json`.

Nome do arquivo e PLANO, um PNG e um SVG por figura e locale:

    output/figures/figN_<slug>.<locale>.{png,svg}

As figuras ficam FORA da cadeia (`configs/stages.json`): o arquivo varia com a versao do
matplotlib e da plataforma. O que cada figura afirma e conferido pelos numeros ancorados
(`verify_figures.py` e os testes).

Mapa figura -> afirmacao do artigo (nenhuma figura sem afirmacao):

- `fig1_tipo` (Figura 1, Secao 5.1): na subamostra de 1.000 municipios, a posicao da
  lacuna decide a rejeicao sob o nulo (0,2% a 27,2%, contra 2,2% sem lacuna) e o
  `nostitch` tira a inflacao.
- `fig2_escala` (Figura 2, Secao 5.2): com a costura padrao, a rejeicao cresce com o numero
  de municipios (6,8% com 50 a 89,4% com 5.468 na lacuna vizinha de troca); os pontos
  mostram o `nostitch` e a linha de base sem lacuna.
- `fig3_largura` (Figura 3, Secao 5.5): no dado real, o desvio-padrao da permutacao e quase
  todo da receita propria, contra dois geradores sinteticos.

    python3 scripts/make_figures.py            # todos os locales
    python3 scripts/make_figures.py --locale en
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIGURES = ROOT / "output" / "figures"

# Paleta da casa (skill `dataviz`): legivel em claro e escuro, segura para daltonismo.
PALETA = ["#4878cf", "#d1615d", "#6acc64", "#b47cc7", "#c4ad66", "#77bedb"]
DPI = 200


def carregar_results() -> dict:
    """`output/results.json` e a unica fonte de numero. Ausente = erro alto, nao grafico vazio."""
    p = ROOT / "output" / "results.json"
    if not p.exists():
        raise SystemExit(
            f"[FAIL] {p} nao existe — rode a analise (fase A7) antes de desenhar figura"
        )
    return json.loads(p.read_text(encoding="utf-8"))


# Separadores numéricos do locale em desenho (``labels.<locale>.json`` -> ``numero``).
SEP = {"decimal": ",", "milhar": "."}


def _n(texto: str) -> str:
    """Troca os separadores de ``texto`` (formato Python, ``1,234.5``) pelos do locale."""
    return texto.translate(str.maketrans({",": SEP["milhar"], ".": SEP["decimal"]}))


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


# --------------------------------------------------------------------------- #
# figuras — SUBSTITUIR pelas do artigo                                        #
# --------------------------------------------------------------------------- #
# deslocamento horizontal fixo por marcador: em 5.468 os quatro pontos ficam perto de zero
# e se escondiam
DESLOCA = {
    "s": 0.86,
    "D": 0.93,
    "^": 1.07,
    "x": 1.15,
}  # fator: no eixo log, é a mesma distância em todo N


def _pontos(ax, celulas, marcador, cor, rotulo) -> None:
    """Desenha a taxa de rejeição de cada célula em ``ax``, com o IC de 95% como barra de erro.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Eixo de destino.
    celulas : list of dict
        Células com ``municipios``, ``taxa`` e ``ic95``.
    marcador : str
        Marcador do matplotlib (também escolhe o deslocamento em ``DESLOCA``).
    cor : str
        Cor da série.
    rotulo : str
        Rótulo da série na legenda.
    """
    xs = [c["municipios"] * DESLOCA[marcador] for c in celulas]
    ys = [c["taxa"] for c in celulas]
    err = [[c["taxa"] - c["ic95"][0] for c in celulas], [c["ic95"][1] - c["taxa"] for c in celulas]]
    ax.errorbar(
        xs, ys, yerr=err, fmt=marcador, color=cor, ms=7, mfc="white", capsize=2, lw=1, label=rotulo
    )


def fig2_escala(results: dict, rotulos: dict, ax) -> None:
    """Desenha a costura padrão do pacote (fiel ao rifle.ado): rejeição sob nulo por N e lacuna."""
    cel = results["ado_escala"]["celulas"]
    for i, cond in enumerate(("na_troca", "p9", "aleatoria")):
        pts = sorted((c["N"], c["taxa"], c["ic95"]) for c in cel.values() if c["condicao"] == cond)
        xs = [n for n, _, _ in pts]
        ys = [t for _, t, _ in pts]
        err = [[t - lo for _, t, (lo, _h) in pts], [hi - t for _, t, (_l, hi) in pts]]
        ax.errorbar(
            xs, ys, yerr=err, marker="o", capsize=3, color=PALETA[i], label=rotulos["series"][cond]
        )
    ado, juz = results["ado"]["celulas"], results["ado_juizes"]["celulas"]
    # nostitch em 1.000 (diagnostico_ado) e no painel inteiro (diagnostico_ado_juizes,
    # pedido da revisão)
    for k, k5, m, cor in (
        ("p9_nostitch", "p9_nostitch_N5468", "s", PALETA[1]),
        ("aleatoria_nostitch", "aleatoria_nostitch_N5468", "D", PALETA[2]),
        (None, "na_troca_nostitch_N5468", "^", PALETA[0]),
    ):
        pts = ([ado[k]] if k else []) + [juz[k5]]
        _pontos(ax, pts, m, cor, rotulos["series"][k5])
    _pontos(
        ax,
        [ado["sem_lacuna"], juz["sem_lacuna_N5468"]],
        "x",
        "#333333",
        rotulos["series"]["sem_lacuna"],
    )
    ax.axhline(0.05, color="#333333", ls="--", lw=1, label=rotulos["nominal"])
    ax.set_xscale("log")
    ax.set_xticks([50, 200, 1000, 5468])
    ax.set_xticklabels(["50", "200", "1.000", "5.468"])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel(rotulos["eixo_x"])
    ax.set_ylabel(rotulos["eixo_y"])
    ax.set_title(rotulos["titulo"], fontsize=10)
    ax.legend(fontsize=8, loc="upper left")


def fig1_tipo(results: dict, rotulos: dict, ax) -> None:
    """Desenha N = 1.000, pacote fiel: a posição da lacuna decide; o nostitch conserta."""
    ado = results["ado"]["celulas"]
    ordem = ["sem_lacuna", "p9", "meio", "p9_rho0", "p9_nostitch", "aleatoria_nostitch"]
    y = list(range(len(ordem)))[::-1]
    for yi, k in zip(y, ordem, strict=False):
        t, (lo, hi) = ado[k]["taxa"], ado[k]["ic95"]
        cor = PALETA[1] if lo > 0.05 else PALETA[3] if hi < 0.05 else PALETA[0]
        ax.barh(yi, t, color=cor, height=0.6)
        ax.errorbar(t, yi, xerr=[[t - lo], [hi - t]], fmt="none", ecolor="#333333", capsize=3, lw=1)
        ax.text(hi + 0.005, yi, _n(f"{t:.1%}"), va="center", fontsize=8)
    ax.axvline(0.05, color="#333333", ls="--", lw=1, label=rotulos["nominal"])
    ax.set_yticks(y)
    # N efetivo por barra: as células com lacuna condicionada à posição perdem municípios
    # (revisão, rodada 1)
    n_br = {k: _n(f"{ado[k]['municipios']:,}") for k in ordem}  # milhar do locale
    ax.set_yticklabels([f"{rotulos['series'][k]} (N = {n_br[k]})" for k in ordem], fontsize=8)
    ax.set_xlim(0, 0.4)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel(rotulos["eixo_x"])
    ax.set_title(rotulos["titulo"], fontsize=10)
    ax.legend(fontsize=8, loc="lower right")


def fig3_largura(results: dict, rotulos: dict, ax) -> None:
    """Largura da distribuição de permutação real contra os geradores; a receita própria domina."""
    dec = results["astra_decomposicao"]["versoes"]["principal"]
    linhas = [
        ("real_indice", dec["dp_condicional_exato"]),
        ("real_so_c2", dec["componentes"]["C2"]["dp_contribuicao_isolada_mesmo_denominador"]),
        ("real_sem_c2", dec["componentes"]["C2"]["dp_sem_componente_mesmo_denominador"]),
        # mesma grandeza nos cinco: DP da distribuição de permutação condicional a um conjunto
        # de dados
        # (nos geradores, a média sobre 200 bases nulas; reprodução independente)
        (
            "gerador_d3",
            results["astra_simulacoes"]["versoes"]["principal"]["D3_nulo"]["dp_condicional_media"],
        ),
        (
            "gerador_d5",
            results["astra_simulacoes"]["versoes"]["principal"]["D5_nulo"]["dp_condicional_media"],
        ),
    ]
    y = list(range(len(linhas)))[::-1]
    for yi, (k, v) in zip(y, linhas, strict=False):
        ax.barh(yi, v, color=PALETA[0] if k.startswith("real") else PALETA[3], height=0.6)
        ax.text(v + 0.0001, yi, _n(f"{v:.4f}"), va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([rotulos["series"][k] for k, _ in linhas], fontsize=8)
    ax.set_xlim(0, max(v for _, v in linhas) * 1.18)  # folga para o rótulo da barra maior
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _n(f"{v:.3f}")))
    ax.set_xlabel(rotulos["eixo_x"], fontsize=9)
    ax.set_title(
        rotulos["titulo"], fontsize=10, loc="left"
    )  # à esquerda: o título longo não sai da figura


FIGURAS = {"fig1_tipo": fig1_tipo, "fig2_escala": fig2_escala, "fig3_largura": fig3_largura}


def main(argv: list[str] | None = None) -> int:
    """Gera os PNG de cada figura em cada locale declarado, em ``output/figures/``.

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
    FIGURES.mkdir(parents=True, exist_ok=True)

    escritos = 0
    for loc, labels in locales.items():
        SEP.update(labels.get("numero", {"decimal": ",", "milhar": "."}))
        for stem, desenhar in FIGURAS.items():
            rotulos = labels.get("figuras", {}).get(stem)
            if rotulos is None:
                raise SystemExit(
                    f"[FAIL] labels.{loc}.json nao tem rotulos para '{stem}' — "
                    "paridade por locale e gate"
                )
            fig, ax = plt.subplots(figsize=(8.0, 4.8))
            desenhar(results, rotulos, ax)
            fig.tight_layout()
            destino = FIGURES / f"{stem}.{loc}.png"
            fig.savefig(destino, dpi=DPI)
            # SVG sem data embutida, para o arquivo nao mudar a cada rodada
            fig.savefig(destino.with_suffix(".svg"), metadata={"Date": None})
            plt.close(fig)
            print(f"[ok] {destino.relative_to(ROOT)}")
            escritos += 1
    print(f"[PASS] {escritos} figura(s) em {len(locales)} locale(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
