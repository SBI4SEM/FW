"""Análise do desfecho primário (seções 5.1 e 5.5 do artigo).

ANCOVA do escore em T1, com T0 e os estratos como covariáveis, contrastando o braço A
(SBI) com os comparadores agrupados (B + C). Contrastes pareados A-B e A-C são
exploratórios. Relata-se diferença ajustada e g de Hedges com IC de 95%; o valor de p
não é regra de decisão. A regra de decisão (H1 / desfavorável à SBI / H3 / inconclusivo) usa o menor efeito
de interesse prático fixado no pré-registro, NA ESCALA DE g (valor de partida g = 0,30, a
confirmar). O d da Tabela 4 (`amostra.py`) é parâmetro de planejamento amostral, e não de decisão.

Observação: g é a diferença ajustada dividida pelo desvio-padrão agrupado de T1 dentro
dos grupos (com fator J de Hedges); o IC de g divide os limites do IC da diferença pelo
mesmo desvio-padrão (aproximação, adequada para um piloto).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


H1_SUSTENTADA = "H1 sustentada"
DESFAVORAVEL = "desfavorável à SBI (efeito negativo apreciável)"
H3_COMPATIVEL = "H3 compatível (sem diferença apreciável entre temas)"
INCONCLUSIVO = "inconclusivo"


@dataclass
class ResultadoAncova:
    n: int
    n_tratado: int
    n_controle: int
    diferenca_ajustada: float
    ic_diferenca: tuple[float, float]
    g_hedges: float
    ic_g: tuple[float, float]
    gl_residual: int


def _dummies(estrato):
    estrato = np.asarray(estrato)
    niveis = sorted(set(estrato.tolist()))
    return np.column_stack([(estrato == k).astype(float) for k in niveis[1:]]) if len(niveis) > 1 else np.empty((len(estrato), 0))


def ancova(y1, y0, tratado, estrato=None, nivel: float = 0.95) -> ResultadoAncova:
    """y1 ~ tratado + y0 + estratos. `tratado` é 0/1 (1 = braço de interesse)."""
    y1, y0, tratado = (np.asarray(v, dtype=float) for v in (y1, y0, tratado))
    if not (np.all(np.isfinite(y1)) and np.all(np.isfinite(y0)) and np.all(np.isfinite(tratado))):
        raise ValueError("T0/T1 ausentes ou não finitos: use `completos()` (sensibilidade) ou "
                         "imputação pré-registrada (ITT) antes da ANCOVA")
    n = len(y1)
    cols = [np.ones(n), tratado, y0]
    X = np.column_stack(cols + ([_dummies(estrato)] if estrato is not None else []))
    beta, *_ = np.linalg.lstsq(X, y1, rcond=None)
    resid = y1 - X @ beta
    gl = n - X.shape[1]
    if gl <= 0:
        raise ValueError("amostra insuficiente para o modelo")
    s2 = float(resid @ resid) / gl
    cov = s2 * np.linalg.inv(X.T @ X)
    dif, ep = float(beta[1]), float(np.sqrt(cov[1, 1]))
    t = stats.t.ppf(0.5 + nivel / 2, gl)
    ic = (dif - t * ep, dif + t * ep)

    g1, g0 = y1[tratado == 1], y1[tratado == 0]
    n1, n0 = len(g1), len(g0)
    sd_agr = float(np.sqrt(((n1 - 1) * g1.var(ddof=1) + (n0 - 1) * g0.var(ddof=1)) / (n1 + n0 - 2)))
    j = 1 - 3 / (4 * (n1 + n0 - 2) - 1)
    return ResultadoAncova(
        n=n, n_tratado=n1, n_controle=n0,
        diferenca_ajustada=dif, ic_diferenca=ic,
        g_hedges=j * dif / sd_agr, ic_g=(j * ic[0] / sd_agr, j * ic[1] / sd_agr),
        gl_residual=gl,
    )


def decidir(ic_g: tuple[float, float], g: float, limiar: float = 0.30) -> str:
    """Regra de decisão pré-registrada, em unidades do tamanho de efeito (g).

    H1 sustentada: IC exclui zero (limite inferior > 0) e a estimativa alcança +limiar.
    Desfavorável à SBI: simétrica de H1; IC exclui zero (limite superior < 0) e a estimativa
        chega a -limiar. Não é "inconclusivo": o braço SBI teve desempenho apreciavelmente inferior.
    H3 compatível: IC inteiramente dentro de [-limiar, +limiar].
    Caso contrário: inconclusivo (o desfecho mais provável num piloto), inclusive quando o IC
        exclui zero mas a estimativa não alcança o limiar de interesse prático.
    As quatro categorias são mutuamente exclusivas.
    """
    lo, hi = ic_g
    if lo > 0 and g >= limiar:
        return H1_SUSTENTADA
    if hi < 0 and g <= -limiar:
        return DESFAVORAVEL
    if lo >= -limiar and hi <= limiar:
        return H3_COMPATIVEL
    return INCONCLUSIVO


def analisar_piloto(dados: list[dict], limiar: float = 0.30) -> dict:
    """`dados`: dicts com chaves braco ('A','B','C'), t0, t1, estrato.

    Retorna o contraste primário (A vs B+C) e os pareados exploratórios (A-B, A-C).
    """
    def contraste(bracos_controle):
        sub = [d for d in dados if d["braco"] == "A" or d["braco"] in bracos_controle]
        r = ancova(
            [d["t1"] for d in sub], [d["t0"] for d in sub],
            [1.0 if d["braco"] == "A" else 0.0 for d in sub],
            [d["estrato"] for d in sub],
        )
        return r, decidir(r.ic_g, r.g_hedges, limiar)

    out = {"primario_A_vs_BC": contraste(("B", "C"))}
    out["exploratorio_A_vs_B"] = contraste(("B",))
    out["exploratorio_A_vs_C"] = contraste(("C",))
    return out


def fluxo(dados: list[dict]) -> dict:
    """Fluxo de participantes por braço (CONSORT): randomizados, com T1 e atrito.

    Um registro sem T1 tem `t1` igual a None. A análise por intenção de tratar exige
    manter todos os randomizados; aqui só se mede o atrito e se separa o conjunto completo.
    """
    out = {}
    for b in sorted({d["braco"] for d in dados}):
        reg = [d for d in dados if d["braco"] == b]
        com = [d for d in reg if d.get("t1") is not None]
        out[b] = {"randomizados": len(reg), "com_t1": len(com),
                  "atrito": 1 - len(com) / len(reg) if reg else float("nan")}
    return out


def completos(dados: list[dict]) -> list[dict]:
    """Casos completos (T0 e T1 presentes). É análise de sensibilidade, não ITT."""
    return [d for d in dados if d.get("t0") is not None and d.get("t1") is not None]


def proporcao_teto(t0, maximo: float, margem_relativa: float = 0.10) -> float:
    """Proporção de escores em T0 a menos de `margem_relativa` x máximo do teto.

    O limiar de proporção que aciona a troca do desfecho primário (efeito de teto,
    seção 5.6) é fixado no pré-registro; este número é a entrada para a regra.
    """
    t0 = np.asarray([v for v in t0 if v is not None], float)
    return float(np.mean(t0 >= maximo * (1 - margem_relativa)))
