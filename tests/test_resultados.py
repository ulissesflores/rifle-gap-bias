"""``output/results.json`` é o que ``code/montar_results.py`` monta dos dados congelados."""

import subprocess
import sys

from conftest import RAIZ


def test_results_json_remontado_identico():
    """Remonta numa cópia e compara byte a byte com o arquivo publicado."""
    publicado = (RAIZ / "output" / "results.json").read_bytes()
    r = subprocess.run(
        [sys.executable, str(RAIZ / "code" / "montar_results.py")], capture_output=True, text=True
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert (RAIZ / "output" / "results.json").read_bytes() == publicado
