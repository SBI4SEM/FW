"""Alocação aleatória estratificada em blocos permutados (seção 5.3 do artigo).

Três braços (A = SBI, B = IA inspirada no cérebro, C = BCI com EEG aberto), razão 1:1:1,
estratos = escola x série. A sequência deve ser gerada e guardada por pessoa externa ao
ensino; o pesquisador recebe apenas o carimbo (hash SHA-256) para o pré-registro e a
alocação de cada estudante, na ordem de inclusão, depois do pré-teste.

Uso:
    python -m sbi4sem.randomizacao --estratos "EscolaX-1:30,EscolaX-2:30" --saida sequencia.csv
    (sem --seed, a semente é sorteada com `secrets` e impressa: guarde-a em local separado)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import secrets

BRACOS = ("A", "B", "C")


def gerar_sequencia(estratos: dict[str, int], seed: int, tamanhos_bloco=(3, 6)) -> dict[str, list[str]]:
    """Sequência de braços por estrato; `estratos` dá a capacidade (n máximo) de cada um."""
    if any(t % len(BRACOS) for t in tamanhos_bloco):
        raise ValueError("tamanhos de bloco devem ser múltiplos de 3")
    rng = random.Random(seed)
    saida: dict[str, list[str]] = {}
    for est in sorted(estratos):
        seq: list[str] = []
        while len(seq) < estratos[est]:
            tb = rng.choice(tamanhos_bloco)
            bloco = list(BRACOS) * (tb // len(BRACOS))
            rng.shuffle(bloco)
            seq.extend(bloco)
        saida[est] = seq[: estratos[est]]
    return saida


def carimbo(sequencia: dict[str, list[str]]) -> str:
    """SHA-256 da sequência em forma canônica: registra-se no pré-registro, sem revelá-la."""
    canon = json.dumps(sequencia, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def alocar(sequencia: dict[str, list[str]], estrato: str, ordem_inclusao: int) -> str:
    """Braço do estudante que é o `ordem_inclusao`-ésimo (a partir de 1) incluído no estrato."""
    return sequencia[estrato][ordem_inclusao - 1]


def _estratos_cli(texto: str) -> dict[str, int]:
    out = {}
    for item in texto.split(","):
        nome, n = item.rsplit(":", 1)
        out[nome.strip()] = int(n)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estratos", required=True, help='ex.: "EscolaX-1:30,EscolaX-2:30"')
    ap.add_argument("--seed", type=int, default=None, help="semente (padrão: sorteada com secrets)")
    ap.add_argument("--saida", default="sequencia.csv")
    a = ap.parse_args(argv)
    seed = a.seed if a.seed is not None else secrets.randbits(63)
    seq = gerar_sequencia(_estratos_cli(a.estratos), seed)
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estrato", "ordem_inclusao", "braco"])
        for est, lista in seq.items():
            for i, b in enumerate(lista, 1):
                w.writerow([est, i, b])
    print(f"semente (guardar com a pessoa externa): {seed}")
    print(f"carimbo SHA-256 (registrar no pré-registro): {carimbo(seq)}")


if __name__ == "__main__":
    main()
