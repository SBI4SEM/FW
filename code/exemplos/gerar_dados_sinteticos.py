"""Gera a bateria de dados sintéticos em JSON.

    cd FW/code && python exemplos/gerar_dados_sinteticos.py --saida ../dados_sinteticos
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sbi4sem.bateria import gerar_todos  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "..", "..", "dados_sinteticos"))
    a = ap.parse_args()
    for nome, m in gerar_todos(a.saida).items():
        print(f"{nome:28s} {m['bytes']:>9,d} bytes  sha256 {m['sha256'][:12]}…")
