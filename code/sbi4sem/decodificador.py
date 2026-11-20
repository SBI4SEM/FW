"""Decodificador linear com validação por blocos temporais (teste 2 da tarefa-padrão).

Duas funções: (i) classificar padrões (regressão ridge em alvos -1/+1, um contra todos) e
(ii) gerar padrões temporais (regressão ridge multissaída do vetor de características
para o padrão-alvo). Ambos são validados por BLOCOS TEMPORAIS CONTÍGUOS, com uma folga
(`gap`) que remove da amostra de treino as janelas vizinhas de cada bloco de teste, para
evitar vazamento por autocorrelação (a validação cruzada aleatória infla a acurácia
quando amostras vizinhas no tempo compartilham ruído ou estado lento).

As amostras DEVEM estar em ordem temporal. A padronização (média e desvio) é ajustada só
no treino de cada divisão. As probabilidades devolvidas são softmax dos escores: servem
para ordenar confiança, e NÃO são calibradas.
"""
from __future__ import annotations

import numpy as np


def divisoes_por_blocos(n: int, n_blocos: int = 5, gap: int = 0):
    """Gera (índices_treino, índices_teste); o teste é um bloco contíguo."""
    if n_blocos < 2 or n < n_blocos:
        raise ValueError("n_blocos inválido")
    arestas = np.linspace(0, n, n_blocos + 1).astype(int)
    for b in range(n_blocos):
        ini, fim = arestas[b], arestas[b + 1]
        treino = np.concatenate([np.arange(0, max(0, ini - gap)), np.arange(min(n, fim + gap), n)])
        if len(treino) == 0:
            raise ValueError(f"gap = {gap} deixa o bloco {b} sem amostras de treino")
        yield treino, np.arange(ini, fim)


def divisoes_aleatorias(n: int, k: int = 5, seed: int = 0):
    """Validação cruzada ALEATÓRIA: só para demonstrar o vazamento; não usar no protocolo."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    for parte in np.array_split(idx, k):
        yield np.setdiff1d(idx, parte), np.sort(parte)


class _Ridge:
    def __init__(self, lam: float = 1.0):
        self.lam = lam

    def _ajusta(self, X, Y):
        self.mu_ = X.mean(0)
        self.sd_ = X.std(0) + 1e-12
        Z = (X - self.mu_) / self.sd_
        self.ymu_ = Y.mean(0)
        A = Z.T @ Z + self.lam * np.eye(Z.shape[1])
        self.W_ = np.linalg.solve(A, Z.T @ (Y - self.ymu_))
        return self

    def _escores(self, X):
        return ((X - self.mu_) / self.sd_) @ self.W_ + self.ymu_


class DecodificadorLinear(_Ridge):
    """Classificador linear (ridge, um contra todos)."""

    def fit(self, X, y):
        X = np.asarray(X, float)
        self.classes_ = np.unique(y)
        Y = -np.ones((len(y), len(self.classes_)))
        for j, c in enumerate(self.classes_):
            Y[np.asarray(y) == c, j] = 1.0
        return self._ajusta(X, Y)

    def decision_function(self, X):
        return self._escores(np.asarray(X, float))

    def predict(self, X):
        return self.classes_[np.argmax(self.decision_function(X), axis=1)]

    def predict_proba(self, X):
        s = self.decision_function(X)
        e = np.exp(s - s.max(1, keepdims=True))
        return e / e.sum(1, keepdims=True)


class GeradorDePadroes(_Ridge):
    """Regressão linear de características para um padrão temporal-alvo (n x L)."""

    def fit(self, X, T):
        return self._ajusta(np.asarray(X, float), np.asarray(T, float))

    def predict(self, X):
        return self._escores(np.asarray(X, float))


def avaliar_classificacao(X, y, n_blocos: int = 5, gap: int = 0, lam: float = 1.0, divisoes=None):
    """Acurácia por bloco de teste. Devolve (acuracias_por_bloco, acuracia_media)."""
    X, y = np.asarray(X, float), np.asarray(y)
    divs = divisoes if divisoes is not None else divisoes_por_blocos(len(y), n_blocos, gap)
    acc = []
    for tr, te in divs:
        m = DecodificadorLinear(lam).fit(X[tr], y[tr])
        acc.append(float(np.mean(m.predict(X[te]) == y[te])))
    return np.array(acc), float(np.mean(acc))


def nrmse(previsto, alvo) -> float:
    """Raiz do erro quadrático médio normalizada pelo desvio-padrão do alvo (0 = perfeito;
    1 = tão ruim quanto prever a média). Métrica do protocolo para a geração de padrões."""
    p, a = np.asarray(previsto, float).ravel(), np.asarray(alvo, float).ravel()
    sd = a.std()
    if sd == 0:
        raise ValueError("alvo constante: NRMSE indefinido")
    return float(np.sqrt(np.mean((p - a) ** 2)) / sd)


def avaliar_geracao(X, T, n_blocos: int = 5, gap: int = 0, lam: float = 1.0, metrica: str = "r"):
    """Geração de padrões avaliada em blocos não vistos.

    metrica="r": correlação de Pearson média por padrão; metrica="nrmse": NRMSE do bloco."""
    X, T = np.asarray(X, float), np.asarray(T, float)
    vals = []
    for tr, te in divisoes_por_blocos(len(X), n_blocos, gap):
        m = GeradorDePadroes(lam).fit(X[tr], T[tr])
        P = m.predict(X[te])
        if metrica == "nrmse":
            vals.append(nrmse(P, T[te]))
            continue
        for p, t in zip(P, T[te]):
            if p.std() > 0 and t.std() > 0:
                vals.append(np.corrcoef(p, t)[0, 1])
    return float(np.mean(vals)) if vals else float("nan")


def acaso_por_permutacao(X, y, n_perm: int = 100, n_blocos: int = 5, gap: int = 0, lam: float = 1.0, seed: int = 0):
    """Distribuição nula da acurácia por blocos com rótulos DESLOCADOS CIRCULARMENTE.

    O deslocamento circular preserva a autocorrelação dos rótulos (embaralhar amostra a
    amostra a destruiria e daria um acaso otimista demais). Devolve (acc_observada,
    distribuição nula, p unilateral)."""
    X, y = np.asarray(X, float), np.asarray(y)
    _, obs = avaliar_classificacao(X, y, n_blocos, gap, lam)
    rng = np.random.default_rng(seed)
    n = len(y)
    if n < 10:
        raise ValueError("permutação circular exige n >= 10 (com menos, o deslocamento pode ser nulo)")
    nulas = []
    for _ in range(n_perm):
        k = int(rng.integers(n // 10, n - n // 10))
        nulas.append(avaliar_classificacao(X, np.roll(y, k), n_blocos, gap, lam)[1])
    nulas = np.array(nulas)
    return obs, nulas, float((np.sum(nulas >= obs) + 1) / (n_perm + 1))


def comparar_validacoes(X, y, n_blocos: int = 5, gap: int = 10, lam: float = 1.0, seed: int = 0):
    """Acurácia com validação aleatória x por blocos (demonstra o vazamento)."""
    _, a_alea = avaliar_classificacao(X, y, lam=lam, divisoes=divisoes_aleatorias(len(y), n_blocos, seed))
    _, a_blocos = avaliar_classificacao(X, y, n_blocos, gap, lam)
    return {"aleatoria": a_alea, "blocos": a_blocos}
