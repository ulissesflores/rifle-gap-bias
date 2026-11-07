"""Põe ``code/`` e ``scripts/`` no caminho de importação dos testes."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for sub in ("code", "scripts"):
    sys.path.insert(0, str(RAIZ / sub))
