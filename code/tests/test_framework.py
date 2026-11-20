import numpy as np
import pytest

from sbi4sem import amostra, analise, bloqueio, decodificador as dec, esteira, randomizacao, sintetico
from sbi4sem.snn import RedeSNN, gerar_conjunto, gerar_padroes


# ---------- amostra ----------
def test_tabela4_do_artigo():
    assert amostra.tabela4() == [(0.30, 176, 113, 137), (0.50, 64, 42, 50), (0.80, 26, 17, 21)]


def test_contraste_agrupado_tres_quartos():
    assert amostra.n_braco_a_contraste_agrupado(0.30, 0.05, r=0.6) == 85


# ---------- randomização ----------
def test_randomizacao_reprodutivel_e_balanceada():
    est = {"E1-1": 60, "E1-2": 60}
    s1, s2 = randomizacao.gerar_sequencia(est, 123), randomizacao.gerar_sequencia(est, 123)
    assert s1 == s2 and randomizacao.carimbo(s1) == randomizacao.carimbo(s2)
    assert randomizacao.carimbo(s1) != randomizacao.carimbo(randomizacao.gerar_sequencia(est, 124))
    for seq in s1.values():
        assert len(seq) == 60
        # em blocos de 3 ou 6 permutados, a diferença entre braços nunca passa de 3
        c = [seq.count(b) for b in "ABC"]
        assert max(c) - min(c) <= 3
    assert randomizacao.alocar(s1, "E1-1", 1) == s1["E1-1"][0]


# ---------- análise ----------
def test_ancova_recupera_efeito_e_decisao():
    dados = sintetico.estudantes(n_por_braco=200, efeito_A=6.0, seed=1)  # ~0,6 DP
    r = analise.analisar_piloto(dados)
    prim, veredito = r["primario_A_vs_BC"]
    assert 4.0 < prim.diferenca_ajustada < 8.0
    assert prim.ic_diferenca[0] > 0
    assert veredito == "H1 sustentada"


def test_ancova_sem_efeito_com_amostra_de_piloto_e_inconclusivo():
    dados = sintetico.estudantes(n_por_braco=15, efeito_A=0.0, seed=3)
    _, veredito = analise.analisar_piloto(dados)["primario_A_vs_BC"]
    assert veredito in ("inconclusivo", "H3 compatível (sem diferença apreciável entre temas)")
    assert veredito != "H1 sustentada"


def test_regra_de_decisao_limites():
    assert analise.decidir((0.1, 0.9), 0.5) == "H1 sustentada"
    assert analise.decidir((0.1, 0.9), 0.2) == "inconclusivo"  # IC exclui 0 mas não alcança o limiar
    assert analise.decidir((-0.2, 0.2), 0.0).startswith("H3")
    assert analise.decidir((-0.5, 0.5), 0.0) == "inconclusivo"


def test_regra_de_decisao_efeito_negativo_nao_e_inconclusivo():
    # simétrica de H1: IC inteiro abaixo de zero e estimativa que alcança -limiar
    assert analise.decidir((-0.9, -0.1), -0.5) == analise.DESFAVORAVEL
    assert analise.decidir((-0.9, -0.1), -0.30) == analise.DESFAVORAVEL      # no limiar exato
    # IC exclui zero, mas a estimativa não chega ao limiar de interesse prático: continua inconclusivo
    assert analise.decidir((-0.28, -0.02), -0.15) == "H3 compatível (sem diferença apreciável entre temas)"
    assert analise.decidir((-0.45, -0.05), -0.25) == analise.INCONCLUSIVO
    # estimativa muito negativa, mas IC que alcança zero: inconclusivo
    assert analise.decidir((-0.9, 0.1), -0.5) == analise.INCONCLUSIVO
    # um limiar diferente muda a classificação
    assert analise.decidir((-0.9, -0.1), -0.5, limiar=0.6) == analise.INCONCLUSIVO


def test_quatro_categorias_sao_exclusivas_e_exaustivas():
    rng = np.random.default_rng(0)
    cats = set()
    for _ in range(2000):
        g = rng.normal(0, 0.6)
        meia = abs(rng.normal(0, 0.4)) + 1e-6
        v = analise.decidir((g - meia, g + meia), g)
        assert v in (analise.H1_SUSTENTADA, analise.DESFAVORAVEL, analise.H3_COMPATIVEL, analise.INCONCLUSIVO)
        cats.add(v)
    assert len(cats) == 4


# ---------- decodificador ----------
def test_blocos_sem_sobreposicao_com_gap():
    for tr, te in dec.divisoes_por_blocos(100, 5, gap=5):
        assert len(np.intersect1d(tr, te)) == 0
        viz = np.arange(te.min() - 5, te.max() + 6)
        assert len(np.intersect1d(tr, viz)) == 0


def test_validacao_aleatoria_infla_e_blocos_ficam_no_acaso():
    X, y = sintetico.serie_autocorrelacionada(seed=0)
    r = dec.comparar_validacoes(X, y, n_blocos=5, gap=60, lam=1.0)
    assert r["aleatoria"] > r["blocos"] + 0.15
    assert r["blocos"] < 1 / 3 + 0.20


def test_decodificador_aprende_sinal_real_e_gerador_correlaciona():
    rng = np.random.default_rng(0)
    y = np.tile([0, 1, 2], 100)
    X = rng.normal(size=(300, 30)) + np.eye(3)[y] @ rng.normal(size=(3, 30)) * 1.5
    assert dec.avaliar_classificacao(X, y, 5, 5)[1] > 0.8
    Xg, T = sintetico.padroes_temporais()
    assert dec.avaliar_geracao(Xg, T, 5, 5, lam=10.0) > 0.5


# ---------- esteira ----------
def test_esteira_conta_saida_invalida_como_erro_e_calcula_metricas():
    itens = list(range(200))
    rotulos = [i % 2 for i in itens]
    perfeita = esteira.CamadaTipada("tipada", lambda i: {0: 1.0, 1: 0.0} if i % 2 == 0 else {0: 0.0, 1: 1.0}, [0, 1])
    defeituosa = esteira.CamadaTipada("defeituosa", lambda i: {0: 0.7, 9: 0.3} if i % 4 == 0 else {0: 0.0, 1: 1.0} if i % 2 else {0: 1.0, 1: 0.0}, [0, 1])
    regra = esteira.CamadaRegraFixa("regra", lambda i: 0)
    r = esteira.executar_esteira(itens, rotulos, [perfeita, defeituosa, regra], [0, 1], n_boot=200)
    assert r["tipada"]["acuracia"] == 1.0 and r["tipada"]["ece"] == pytest.approx(0.0)
    assert r["tipada"]["taxa_invalida"] == 0.0
    assert r["defeituosa"]["taxa_invalida"] == pytest.approx(0.25)
    assert r["defeituosa"]["acuracia"] == pytest.approx(0.75)
    assert r["regra"]["acuracia"] == 0.5 and "brier" not in r["regra"]


def test_itr_com_tempo_de_decisao_por_camada():
    itens = list(range(100))
    rotulos = [i % 2 for i in itens]
    boa = esteira.CamadaTipada("boa", lambda i: {0: 0.9, 1: 0.1} if i % 2 == 0 else {0: 0.1, 1: 0.9}, [0, 1])
    regra = esteira.CamadaRegraFixa("regra", lambda i: i % 2)
    # mesmo desempenho, tempos diferentes: o ITR deve refletir a latência de cada camada
    r = esteira.executar_esteira(itens, rotulos, [boa, regra], [0, 1], n_boot=50, t_decisao_s={"boa": 2.0, "regra": 0.5})
    assert r["boa"]["acuracia"] == r["regra"]["acuracia"] == 1.0
    assert r["regra"]["itr_bits_min"] == pytest.approx(4 * r["boa"]["itr_bits_min"])
    assert r["boa"]["t_decisao_s"] == 2.0 and r["regra"]["t_decisao_s"] == 0.5
    # número único continua valendo para todas
    u = esteira.executar_esteira(itens, rotulos, [boa, regra], [0, 1], n_boot=50, t_decisao_s=1.0)
    assert u["boa"]["itr_bits_min"] == pytest.approx(u["regra"]["itr_bits_min"])
    # camada sem tempo no mapa: erro, e não tempo padrão silencioso
    with pytest.raises(ValueError, match="regra"):
        esteira.executar_esteira(itens, rotulos, [boa, regra], [0, 1], n_boot=50, t_decisao_s={"boa": 2.0})


def test_camada_organoide_alinha_probabilidades_ao_esquema():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(120, 8))
    y = np.tile([1, 2], 60)                      # a classe 0 do esquema NÃO está no treino
    m = dec.DecodificadorLinear(lam=1.0).fit(X + np.eye(2)[y - 1] @ rng.normal(size=(2, 8)) * 3, y)
    esquema = [0, 1, 2]
    cam = esteira.CamadaOrganoide("org", m, esquema=esquema)
    d = cam.decidir(X[0])
    assert d.probs.shape == (3,) and d.probs[0] == 0.0 and d.probs.sum() == pytest.approx(1.0)
    assert d.rotulo in (1, 2) and d.rotulo == esquema[int(np.argmax(d.probs))]
    itens = list(range(40))
    rot = [int(v) for v in np.tile([0, 1, 2], 14)[:40]]
    r = esteira.executar_esteira(itens, rot, [esteira.CamadaOrganoide("org", m, extrair=lambda i: X[i], esquema=esquema)],
                                 esquema, n_boot=50)
    assert np.isfinite(r["org"]["brier"]) and 0 <= r["org"]["ece"] <= 1
    # classe do decodificador fora do esquema: erro explícito
    with pytest.raises(ValueError, match="fora do esquema"):
        esteira.CamadaOrganoide("org", m, esquema=[0, 1]).decidir(X[0])
    # sem `esquema` e com classe faltando: a esteira recusa, em vez de desalinhar o Brier em silêncio
    with pytest.raises(ValueError, match="esquema="):
        esteira.executar_esteira(itens, rot, [esteira.CamadaOrganoide("org", m, extrair=lambda i: X[i])], esquema, n_boot=50)


def test_bootstrap_por_conglomerado_e_mais_largo():
    rng = np.random.default_rng(0)
    grupos = np.repeat(np.arange(6), 50)
    v = (rng.random(300) < (0.3 + 0.08 * grupos)).astype(float)  # organoides diferem entre si
    lo_i, hi_i = esteira.bootstrap_ic(v, None, 1000)
    lo_g, hi_g = esteira.bootstrap_ic(v, grupos, 1000)
    assert (hi_g - lo_g) > (hi_i - lo_i)


# ---------- bloqueio ----------
def _organoides(n, efeito_ampa=-0.3, efeito_nmda=-0.1, ruido=0.03, seed=0):
    rng = np.random.default_rng(seed)
    dados = []
    for o in range(n):
        base = 0.8 + rng.normal(0, 0.03)
        vals = {"basal": base, "veiculo": base + rng.normal(0, ruido), "AMPA": base + efeito_ampa + rng.normal(0, ruido),
                "NMDA": base + efeito_nmda + rng.normal(0, ruido), "lavagem1": base + rng.normal(0, ruido),
                "lavagem2": base + rng.normal(0, ruido), "TTX": 0.33}
        dados += [{"organoide": f"o{o}", "condicao": c, "valor": v} for c, v in vals.items()]
    return dados


def test_bloqueio_detecta_efeito_e_avisa_n_pequeno():
    r = bloqueio.analisar_bloqueio(_organoides(8), chance=1 / 3)
    assert r["AMPA"]["media_efeito"] < -0.2 and r["AMPA"]["ic95_bootstrap"][1] < 0
    assert r["AMPA"]["p_permutacao"] < 0.05
    assert r["fracao_recuperacao_lavagem"] == 1.0 and r["fracao_ttx_no_acaso"] == 1.0
    pequeno = bloqueio.analisar_bloqueio(_organoides(3), chance=1 / 3)
    assert pequeno["AMPA"]["ic95_bootstrap"] is None and any("n < 5" in a for a in pequeno["avisos"])


def test_bloqueio_sinaliza_ttx_e_lavagem_falhas():
    d = _organoides(6)
    for x in d:
        if x["organoide"] == "o0" and x["condicao"] in ("TTX", "lavagem1"):
            x["valor"] = 0.9 if x["condicao"] == "TTX" else 0.4
    r = bloqueio.analisar_bloqueio(d, chance=1 / 3)
    assert r["fracao_ttx_no_acaso"] < 1 and r["fracao_recuperacao_lavagem"] < 1
    assert len(r["avisos"]) >= 2


def _com_controles(n_trat=8, n_ctrl=8, efeito=-0.3, deriva=0.0, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for g, n, ef in (("tratado", n_trat, efeito), ("controle", n_ctrl, 0.0)):
        for o in range(n):
            base = 0.8 + rng.normal(0, 0.02)
            vals = {"basal": base, "veiculo": base + rng.normal(0, 0.02),
                    "AMPA": base + ef + deriva + rng.normal(0, 0.02)}
            out += [{"organoide": f"{g[0]}{o}", "condicao": c, "valor": v, "grupo": g} for c, v in vals.items()]
    return out


def test_bloqueio_efeito_liquido_desconta_a_deriva_dos_controles():
    com_deriva = bloqueio.analisar_bloqueio(_com_controles(efeito=0.0, deriva=-0.15), condicoes=("AMPA",))
    a = com_deriva["AMPA"]
    assert a["media_efeito"] < -0.1 and a["p_permutacao"] < 0.05                 # só tratados: parece efeito
    assert a["controle"]["media_deriva"] < -0.1                                  # mas os controles derivam igual
    liq = a["efeito_liquido"]
    assert abs(liq["diferenca_tratado_menos_controle"]) < 0.05
    lo, hi = liq["ic95_bootstrap"]
    assert lo <= 0 <= hi and liq["p_permutacao"] > 0.05
    real = bloqueio.analisar_bloqueio(_com_controles(efeito=-0.3, deriva=-0.15), condicoes=("AMPA",))["AMPA"]
    assert real["efeito_liquido"]["diferenca_tratado_menos_controle"] == pytest.approx(-0.3, abs=0.05)
    assert real["efeito_liquido"]["ic95_bootstrap"][1] < 0 and real["efeito_liquido"]["p_permutacao"] < 0.01
    assert com_deriva["n_organoides"] == 8 and com_deriva["n_controles"] == 8


def test_bloqueio_sem_controles_avisa_e_nao_cria_efeito_liquido():
    sem = bloqueio.analisar_bloqueio(_organoides(6), chance=1 / 3)
    assert sem["n_controles"] == 0 and "efeito_liquido" not in sem["AMPA"] and "controle" not in sem["AMPA"]
    assert any("sem organoides-controle" in a for a in sem["avisos"])
    com = bloqueio.analisar_bloqueio(_com_controles(), condicoes=("AMPA",))
    assert not any("sem organoides-controle" in a for a in com["avisos"])


def test_bloqueio_grupo_invalido_ou_organoide_em_dois_grupos():
    d = _com_controles(3, 3)
    with pytest.raises(ValueError, match="grupo"):
        bloqueio.analisar_bloqueio([{**d[0], "grupo": "placebo"}])
    d2 = [dict(x) for x in d]
    d2[-1]["organoide"] = d2[0]["organoide"]   # mesmo id nos dois grupos
    with pytest.raises(ValueError, match="dois grupos"):
        bloqueio.analisar_bloqueio(d2)


def test_bloqueio_permutacao_de_grupos_e_exata_quando_pequena():
    # 3 x 3: 20 divisões possíveis; separação total => p = 2/20
    t, c = [-1.0, -1.1, -0.9], [0.0, 0.1, -0.1]
    assert bloqueio._permutacao_grupos(t, c) == pytest.approx(2 / 20)


def test_bloqueio_permutacao_de_grupos_aproximada_quando_grande():
    rng = np.random.default_rng(0)
    t, c = rng.normal(-1.0, 0.1, 12), rng.normal(0.0, 0.1, 12)      # C(24, 12) > 20 000: simulação
    p = bloqueio._permutacao_grupos(t, c)
    assert 0 < p < 0.01
    assert bloqueio._permutacao_grupos(t, c) == p                  # reprodutível (semente fixa)
    assert bloqueio._permutacao_grupos(t, t.copy()) == pytest.approx(1.0)


def test_bloqueio_controles_sem_a_janela_avisam():
    d = [x for x in _com_controles(6, 6) if not (x["grupo"] == "controle" and x["condicao"] == "AMPA")]
    r = bloqueio.analisar_bloqueio(d, condicoes=("AMPA",))
    assert "efeito_liquido" not in r["AMPA"]
    assert any("nenhum controle" in a for a in r["avisos"])


def test_ordem_contrabalancada():
    o = bloqueio.ordem_contrabalancada([f"o{i}" for i in range(8)], seed=1)
    assert sum(v[0] == "AMPA" for v in o.values()) == 4


# ---------- SNN ----------
def test_snn_ttx_e_bloqueio_de_sodio_e_nao_de_ampa_nmda():
    pad = gerar_padroes(3, seed=0)

    def sim(**kw):
        rede = RedeSNN(seed=0)
        return int(rede.simular(pad[0], **kw).sum()), rede.vm_medio_exc

    base, vm_base = sim()
    ampa_nmda, vm_ampa_nmda = sim(bloqueio_ampa=1.0, bloqueio_nmda=1.0)
    ttx, vm_ttx = sim(bloqueio_na=1.0)
    parcial, _ = sim(bloqueio_na=0.5)
    assert base > 0 and ampa_nmda == 0 and ttx == 0              # ambos silenciam os spikes...
    assert 0 < parcial < base                                    # TTX parcial reduz sem abolir
    # ...mas por mecanismos diferentes: sem AMPA/NMDA a membrana fica no repouso; sob TTX, a entrada
    # sináptica continua despolarizando a célula (potenciais subliminares, sem spike)
    assert vm_ampa_nmda == pytest.approx(RedeSNN().p.v_rep, abs=1.5)
    assert vm_ttx > vm_ampa_nmda + 10
    with pytest.raises(ValueError, match="bloqueio_na"):
        RedeSNN(seed=0).simular(pad[0], bloqueio_na=1.2)


def test_snn_padrao_sem_bloqueio_na_e_inalterado():
    pad = gerar_padroes(3, seed=0)
    a = RedeSNN(seed=3).simular(pad[1], bloqueio_ampa=0.3)
    b = RedeSNN(seed=3).simular(pad[1], bloqueio_ampa=0.3, bloqueio_na=0.0)
    assert np.array_equal(a, b)

def test_snn_bloqueio_reduz_atividade_e_conjunto_e_decodificavel():
    rede = RedeSNN(seed=0)
    pad = gerar_padroes(3, seed=0)
    base = rede.simular(pad[0]).sum()
    ampa = rede.simular(pad[0], bloqueio_ampa=1.0).sum()
    assert base > 0
    assert ampa < base
    X, y = gerar_conjunto(rede, pad, n_por_classe=24, seed=1)
    assert X.shape == (72, rede.p.n_exc * 4)
    assert dec.avaliar_classificacao(X, y, 4, 3, lam=50.0)[1] > 1 / 3 + 0.2
