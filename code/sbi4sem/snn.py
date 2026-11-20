"""Equivalente do braço B: rede pulsada com sinapses AMPA e NMDA (didática).

Neurônios integra-e-dispara com perda (LIF), população excitatória e inibitória, com
condutâncias sinápticas AMPA (rápida), NMDA (lenta, com bloqueio de Mg2+ dependente da
voltagem) e GABA. O "bloqueio farmacológico" é a redução multiplicativa dos pesos AMPA e/ou
NMDA (0 = sem bloqueio, 1 = bloqueio total), o que permite repetir no silício o desenho
do teste 1 (basal, bloqueio de AMPA, de NMDA, de ambos, lavagem = volta a 0).

TTX NÃO é bloqueio de AMPA+NMDA. A tetrodotoxina bloqueia os canais de sódio dependentes de
voltagem, isto é, a GERAÇÃO de potenciais de ação; os receptores sinápticos continuam
funcionando, de modo que a entrada ainda despolariza as células (potenciais subliminares),
mas nenhum spike é emitido. Aqui isso é `bloqueio_na` (0 = sem bloqueio, 1 = bloqueio total):
o limiar de disparo sobe em direção ao potencial de reversão excitatório e, com 1, nenhum
spike é gerado. Após cada simulação, `vm_medio_exc` guarda o potencial de membrana médio dos
neurônios excitatórios, que separa os dois controles: com AMPA+NMDA bloqueados a membrana
fica perto do repouso; com TTX ela fica despolarizada pela entrada, mas sem spikes.

SEM PLASTICIDADE sináptica: só a transmissão aguda (hipóteses F1, F2, F3 e F5); não reproduz F4.
Parâmetros são valores didáticos típicos, NÃO ajustados a dados de organoides. Nada aqui
prevê o resultado do experimento com tecido vivo: serve para o estudante praticar o desenho
e a análise, com a vantagem de ser reprodutível por semente.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ParametrosRede:
    n_exc: int = 80
    n_inh: int = 20
    n_entrada: int = 20
    dt_ms: float = 0.5
    tau_m: float = 20.0
    tau_ampa: float = 2.0
    tau_nmda: float = 100.0
    tau_gaba: float = 6.0
    v_rep: float = -70.0
    v_lim: float = -50.0
    v_reset: float = -65.0
    refrat_ms: float = 2.0
    e_exc: float = 0.0
    e_inh: float = -75.0
    mg: float = 1.0  # mM
    w_entrada: float = 3.5
    w_ee: float = 0.2
    w_ei: float = 0.3
    w_ie: float = 1.0
    w_ii: float = 0.5
    fracao_nmda: float = 0.5  # fração do peso excitatório mediada por NMDA
    p_conexao: float = 0.2


class RedeSNN:
    def __init__(self, par: ParametrosRede | None = None, seed: int = 0):
        self.p = par or ParametrosRede()
        p = self.p
        rng = np.random.default_rng(seed)
        self.n = p.n_exc + p.n_inh
        ne = p.n_exc
        C = lambda a, b: (rng.random((a, b)) < p.p_conexao).astype(float)
        self.Win = C(self.n, p.n_entrada) * p.w_entrada
        self.Wexc = np.zeros((self.n, self.n))   # pré excitatório -> pós
        self.Wexc[:ne, :ne] = C(ne, ne) * p.w_ee
        self.Wexc[ne:, :ne] = C(p.n_inh, ne) * p.w_ei
        np.fill_diagonal(self.Wexc, 0)
        self.Winh = np.zeros((self.n, self.n))   # pré inibitório -> pós
        self.Winh[:ne, ne:] = C(ne, p.n_inh) * p.w_ie
        self.Winh[ne:, ne:] = C(p.n_inh, p.n_inh) * p.w_ii
        self._rng = np.random.default_rng(seed + 1)

    def simular(self, taxas_entrada_hz, dur_ms: float = 400.0, bloqueio_ampa: float = 0.0,
                bloqueio_nmda: float = 0.0, n_bins: int = 4, bloqueio_na: float = 0.0):
        """Devolve contagens de disparos dos neurônios excitatórios em `n_bins` janelas
        (vetor de comprimento n_exc * n_bins).

        `bloqueio_ampa` e `bloqueio_nmda` reduzem os pesos sinápticos (0 a 1). `bloqueio_na`
        (0 a 1) representa o TTX: bloqueia a geração de spikes sem tocar nas sinapses."""
        if not 0.0 <= bloqueio_na <= 1.0:
            raise ValueError("bloqueio_na deve estar entre 0 e 1")
        p, rng = self.p, self._rng
        fa, fn = 1 - bloqueio_ampa, 1 - bloqueio_nmda
        wa, wn = 1 - p.fracao_nmda, p.fracao_nmda
        taxas = np.asarray(taxas_entrada_hz, float)
        passos = int(dur_ms / p.dt_ms)
        v = np.full(self.n, p.v_rep) + rng.normal(0, 2, self.n)
        gA = np.zeros(self.n); gN = np.zeros(self.n); gG = np.zeros(self.n)
        refr = np.zeros(self.n)
        dA, dN, dG = (np.exp(-p.dt_ms / t) for t in (p.tau_ampa, p.tau_nmda, p.tau_gaba))
        disparos = np.zeros((passos, self.n))
        spk = np.zeros(self.n)
        v_lim = p.v_lim + bloqueio_na * (p.e_exc - p.v_lim)  # TTX: limiar efetivo sobe
        gera_spikes = bloqueio_na < 1.0                       # TTX total: nenhum spike
        v_soma = np.zeros(self.n)
        for t in range(passos):
            ent = (rng.random(p.n_entrada) < taxas * p.dt_ms * 1e-3).astype(float)
            drive = self.Win @ ent + self.Wexc @ spk
            gA = gA * dA + wa * fa * drive
            gN = gN * dN + wn * fn * drive * 0.1  # NMDA: mais lento e com menor pico por disparo
            gG = gG * dG + self.Winh @ spk
            bmg = 1.0 / (1.0 + (p.mg / 3.57) * np.exp(-0.062 * v))
            dv = (-(v - p.v_rep) + gA * (p.e_exc - v) + gN * bmg * (p.e_exc - v) + gG * (p.e_inh - v)) / p.tau_m
            v = v + p.dt_ms * dv + rng.normal(0, 0.3 * np.sqrt(p.dt_ms / 0.5), self.n)  # ruído ~ sqrt(dt); idêntico em dt = 0,5 ms
            ativo = refr <= 0
            v = np.where(ativo, v, p.v_reset)
            spk = ((v >= v_lim) & ativo & gera_spikes).astype(float)
            v_soma += v
            v = np.where(spk > 0, p.v_reset, v)
            refr = np.where(spk > 0, p.refrat_ms, refr - p.dt_ms)
            disparos[t] = spk
        ne = p.n_exc
        self.vm_medio_exc = float(v_soma[:ne].mean() / passos)
        janelas = np.array_split(disparos[:, :ne], n_bins, axis=0)
        return np.concatenate([j.sum(0) for j in janelas])


def gerar_padroes(n_classes: int = 3, n_entrada: int = 20, taxa_base: float = 8.0, taxa_pico: float = 45.0, seed: int = 0):
    """Um padrão de taxas de entrada por classe: cada classe excita um subconjunto das entradas."""
    rng = np.random.default_rng(seed)
    padroes = np.full((n_classes, n_entrada), taxa_base)
    for c in range(n_classes):
        padroes[c, rng.choice(n_entrada, n_entrada // 3, replace=False)] = taxa_pico
    return padroes


def gerar_conjunto(rede: RedeSNN, padroes, n_por_classe: int = 40, bloqueio_ampa: float = 0.0,
                   bloqueio_nmda: float = 0.0, dur_ms: float = 400.0, n_bins: int = 4, seed: int = 0,
                   bloqueio_na: float = 0.0):
    """Tentativas intercaladas no tempo (ordem temporal preservada); devolve X, y.
    `bloqueio_na` representa o TTX (ver `RedeSNN.simular`)."""
    rng = np.random.default_rng(seed)
    k = len(padroes)
    ordem = np.concatenate([rng.permutation(k) for _ in range(n_por_classe)])
    X = np.array([rede.simular(padroes[c], dur_ms, bloqueio_ampa, bloqueio_nmda, n_bins, bloqueio_na) for c in ordem])
    return X, ordem
