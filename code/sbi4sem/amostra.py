"""Tamanho amostral por braço (Tabela 4 do artigo).

Aproximação normal para dois grupos, com redução de variância por covariável
(pré-teste) e correção z^2/4 por grupo (aproximação à distribuição t):

    n = 2 (z_{1-a/2} + z_{potência})^2 / d^2 * (1 - r^2) + z_{1-a/2}^2 / 4

r é a correlação pré-pós: suposição (0,6), a substituir pelo dado do piloto.
"""
from __future__ import annotations

import math

from scipy.stats import norm


def n_por_braco(d: float, alpha: float = 0.05, potencia: float = 0.80, r: float = 0.0) -> int:
    """Estudantes por braço para um contraste entre dois braços."""
    if d <= 0:
        raise ValueError("d deve ser positivo")
    if not 0 <= r < 1:
        raise ValueError("r deve estar em [0, 1)")
    za = norm.ppf(1 - alpha / 2)
    zb = norm.ppf(potencia)
    n = 2 * (za + zb) ** 2 / d**2 * (1 - r**2) + za**2 / 4
    return math.ceil(round(n, 9))


def n_braco_a_contraste_agrupado(d: float, alpha: float = 0.05, potencia: float = 0.80, r: float = 0.0) -> int:
    """Aproximação para A contra B+C agrupados, alocação 1:1:1.

    Com A = n e comparadores = 2n, a variância da diferença cai a 3/4 da de dois
    braços de tamanho n; logo n é cerca de 3/4 do valor pareado (aproximação do artigo).
    """
    return math.ceil(round(0.75 * n_por_braco(d, alpha, potencia, r), 9))


def tabela4(ds=(0.30, 0.50, 0.80), r: float = 0.6):
    """Reproduz a Tabela 4: (d, sem covariável a=.05, com pré-teste a=.05, com pré-teste a=.025)."""
    return [
        (d, n_por_braco(d, 0.05), n_por_braco(d, 0.05, r=r), n_por_braco(d, 0.025, r=r))
        for d in ds
    ]


if __name__ == "__main__":
    print("d | sem cov. a=0,05 | pré r=0,6 a=0,05 | pré r=0,6 a=0,025")
    for linha in tabela4():
        print(" | ".join(str(v) for v in linha))
