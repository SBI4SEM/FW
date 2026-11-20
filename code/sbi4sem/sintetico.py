"""Dados sintéticos para testar o software. Não representam estudantes nem organoides."""
from __future__ import annotations

import numpy as np


def estudantes(n_por_braco: int = 30, efeito_A: float = 0.0, r_pre_pos: float = 0.6,
               estratos=("EscolaX-1", "EscolaX-2"), seed: int = 0):
    """Lista de dicts (braco, estrato, t0, t1). t1 tem correlação ~r com t0; `efeito_A`
    é somado a t1 no braço A (em pontos do escore, escala com DP 10)."""
    rng = np.random.default_rng(seed)
    out = []
    for b in "ABC":
        for i in range(n_por_braco):
            t0 = rng.normal(50, 10)
            t1 = 50 + r_pre_pos * (t0 - 50) + rng.normal(0, 10 * np.sqrt(1 - r_pre_pos**2)) + (efeito_A if b == "A" else 0)
            out.append({"braco": b, "estrato": estratos[i % len(estratos)], "t0": t0, "t1": t1})
    return out


def serie_autocorrelacionada(n: int = 600, n_carac: int = 80, n_classes: int = 3,
                             rho: float = 0.97, persist: int = 40, seed: int = 0):
    """Características = ruído AR(1) persistente, INDEPENDENTE dos rótulos (acerto real = acaso);
    rótulos persistem em trechos de `persist` amostras. Serve para mostrar o vazamento."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n, n_carac))
    X[0] = rng.normal(size=n_carac)
    for t in range(1, n):
        X[t] = rho * X[t - 1] + np.sqrt(1 - rho**2) * rng.normal(size=n_carac)
    trechos = rng.integers(0, n_classes, n // persist + 1)
    y = np.repeat(trechos, persist)[:n]
    return X, y


def padroes_temporais(n: int = 300, n_carac: int = 40, L: int = 20, seed: int = 0):
    """Características com sinal linear + ruído e padrões-alvo (n x L) gerados por mistura linear."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n_carac))
    M = rng.normal(size=(n_carac, L)) / np.sqrt(n_carac)
    T = X @ M + 0.5 * rng.normal(size=(n, L))
    return X, T
