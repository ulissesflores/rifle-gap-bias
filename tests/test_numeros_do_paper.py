"""Todo número ancorado no paper (``<!-- num:caminho -->valor``) bate com ``results.json``."""

import json
import re
import zipfile

import pytest
import verify_figures

EDICOES = ("pt-br", "en", "es", "it")


def test_todo_numero_ancorado_bate():
    """O verificador de figuras, tabelas e números termina sem nenhuma violação."""
    assert verify_figures.main([]) == 0


def test_nenhuma_ancora_malformada():
    """Toda âncora ``num:`` exportada do paper e da tabela tem caminho com pontos.

    Uma âncora malformada passaria em silêncio.
    """
    from conftest import RAIZ

    publicados = json.loads((RAIZ / "data" / "numeros_publicados.json").read_text("utf-8"))
    textos = ["\n".join(ed["ancoras"]) for ed in publicados["edicoes"].values()] + [
        arq.read_text(encoding="utf-8") for arq in (RAIZ / "output" / "tables").glob("*.md")
    ]
    for texto in textos:
        assert texto.count("<!-- num:") == len(verify_figures.MARCADOR.findall(texto))


@pytest.mark.parametrize("edicao", EDICOES)
def test_numeros_estao_no_artigo_publicado(edicao):
    """Cada número ancorado aparece no texto do DOCX publicado de cada edição.

    Liga os números conferidos contra ``results.json`` ao artefato que o leitor recebe, e
    não só à fonte do laboratório. O artigo entra no repositório só com o DOI; antes disso o
    DOCX não existe e o teste é pulado.
    """
    from conftest import RAIZ

    nome = "paper-final.docx" if edicao == "pt-br" else f"paper-final-{edicao}.docx"
    docx = RAIZ / "docs" / "paper" / nome
    if not docx.exists():
        pytest.skip(f"{nome} ausente (o artigo entra no repositório com o DOI)")
    with zipfile.ZipFile(docx) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    texto = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml)).replace("\u200b", "")
    publicados = json.loads((RAIZ / "data" / "numeros_publicados.json").read_text("utf-8"))
    faltam = [
        a
        for a in publicados["edicoes"][edicao]["ancoras"]
        if verify_figures.MARCADOR.match(a).group(2).rstrip(".,") not in texto
    ]
    assert not faltam, faltam[:5]
