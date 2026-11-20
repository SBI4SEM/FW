"""Testes que consomem a bateria de dados sintéticos (FW/dados_sinteticos/*.json),
simulações estatísticas e casos-limite. Nada aqui usa dados reais."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sbi4sem import amostra, analise, bateria, bloqueio, decodificador as dec, esteira, randomizacao, sintetico

PASTA = Path(__file__).resolve().parents[2] / "dados_sinteticos"


def carrega(nome):
    with open(PASTA / nome, encoding="utf-8") as f:
        return json.load(f)


def por_id(nome):
    return {c["id"]: c for c in carrega(nome)["dados"]}


# =========================================================== integridade e reprodutibilidade
def test_manifesto_confere_com_os_arquivos():
    man = carrega("manifesto.json")["dados"]
    assert {m["arquivo"] for m in man} == {p.name for p in PASTA.glob("*.json")} - {"manifesto.json"}
    for m in man:
        b = (PASTA / m["arquivo"]).read_bytes()
        assert len(b) == m["bytes"] and hashlib.sha256(b).hexdigest() == m["sha256"], m["arquivo"]


@pytest.mark.parametrize("nome", sorted(p.name for p in PASTA.glob("*.json")))
def test_todo_arquivo_declara_ser_sintetico(nome):
    doc = carrega(nome)
    assert doc["meta"]["sintetico"] is True
    assert "SINTÉTICOS" in doc["meta"]["aviso"] and "não constituem evidência" in doc["meta"]["aviso"]
    assert doc["meta"]["versao_bateria"] == bateria.VERSAO_BATERIA and "dados" in doc


def test_regeneracao_reproduz_os_arquivos_byte_a_byte(tmp_path):
    novos = bateria.gerar_todos(str(tmp_path))
    for nome, m in novos.items():
        if nome in bateria.ARQUIVOS_PLATAFORMA_DEPENDENTES:
            continue
        assert (tmp_path / nome).read_bytes() == (PASTA / nome).read_bytes(), nome


def test_limpa_converte_tipos_numpy():
    out = bateria._limpa({"a": np.float64(1.23456789), "b": np.array([1, 2]), "c": (np.int64(3),)})
    assert out == {"a": 1.234568, "b": [1, 2], "c": [3]}
    json.dumps(out)


# =========================================================== estudantes
CEN = por_id("estudantes_cenarios.json")


def _res(cid, **kw):
    dados = analise.completos(CEN[cid]["estudantes"])
    return analise.analisar_piloto(dados, **kw)


def _se(r):
    return (r.ic_diferenca[1] - r.ic_diferenca[0]) / (2 * 1.96)


@pytest.mark.parametrize("cid", [c for c in CEN if c not in ("atrito_diferencial_n40", "teto_t0")])
def test_estimativa_proxima_do_efeito_verdadeiro(cid):
    prim = _res(cid)["primario_A_vs_BC"][0]
    assert abs(prim.diferenca_ajustada - CEN[cid]["efeito_verdadeiro_pontos"]) <= 4 * _se(prim)
    n_braco = CEN[cid]["parametros"]["n_por_braco"]
    assert prim.n == 3 * n_braco and prim.n_tratado == n_braco and prim.n_controle == 2 * n_braco


def test_veredictos_esperados_por_cenario():
    v = lambda cid: _res(cid)["primario_A_vs_BC"][1]
    assert v("nulo_n15") != "H1 sustentada"
    assert v("nulo_n200").startswith("H3")
    assert v("efeito_10_n200") == "H1 sustentada"
    assert v("efeito_negativo_n200") == analise.DESFAVORAVEL          # efeito negativo claro não é "inconclusivo"
    assert v("efeito_10_n200") != analise.DESFAVORAVEL and v("nulo_n200") != analise.DESFAVORAVEL
    assert _res("efeito_negativo_n200")["primario_A_vs_BC"][0].ic_diferenca[1] < 0
    assert _res("efeito_06_n60")["primario_A_vs_BC"][0].diferenca_ajustada > 0


def test_piloto_pequeno_tende_a_inconclusivo():
    assert _res("nulo_n15")["primario_A_vs_BC"][1] == "inconclusivo"
    assert _res("efeito_03_n15")["primario_A_vs_BC"][1] == "inconclusivo"


def test_covariavel_forte_reduz_incerteza():
    baixa = _res("correlacao_baixa_n60")["primario_A_vs_BC"][0]
    alta = _res("correlacao_alta_n60")["primario_A_vs_BC"][0]
    assert _se(alta) < _se(baixa)


def test_estratos_alteram_apenas_os_graus_de_liberdade():
    um = _res("um_estrato_n30")["primario_A_vs_BC"][0]
    cinco = _res("cinco_estratos_n30")["primario_A_vs_BC"][0]
    assert um.gl_residual == 90 - 3 and cinco.gl_residual == 90 - 3 - 4


def test_atrito_e_casos_completos():
    est = CEN["atrito_diferencial_n40"]["estudantes"]
    f = analise.fluxo(est)
    assert all(f[b]["randomizados"] == 40 for b in "ABC")
    assert f["A"]["atrito"] > f["B"]["atrito"] and f["A"]["atrito"] > f["C"]["atrito"]
    assert len(analise.completos(est)) == sum(v["com_t1"] for v in f.values())
    assert _res("atrito_diferencial_n40")["primario_A_vs_BC"][0].n == len(analise.completos(est))
    with pytest.raises(ValueError, match="completos"):  # t1 = None não pode ir direto à ANCOVA (nada de NaN silencioso)
        analise.analisar_piloto(est)


def test_efeito_de_teto():
    teto = [e["t0"] for e in CEN["teto_t0"]["estudantes"]]
    normal = [e["t0"] for e in CEN["nulo_n200"]["estudantes"]]
    assert analise.proporcao_teto(teto, 100) > 0.4
    assert analise.proporcao_teto(normal, 100) < 0.05
    assert max(teto) <= 100 and analise.proporcao_teto([None, 100.0], 100) == 1.0


# =========================================================== simulações estatísticas
def _replicas(n_por_braco, efeito, n_rep, seed0):
    cobre = h1 = 0
    for k in range(n_rep):
        d = sintetico.estudantes(n_por_braco, efeito_A=efeito, seed=seed0 + k)
        r, v = analise.analisar_piloto(d)["primario_A_vs_BC"]
        # O efeito verdadeiro está em pontos de T1 (DP residual 10): comparação em pontos.
        cobre += r.ic_diferenca[0] <= efeito <= r.ic_diferenca[1]
        h1 += v == "H1 sustentada"
    return cobre / n_rep, h1 / n_rep


def test_cobertura_do_ic_e_erro_tipo_i_da_regra():
    cobertura, h1_nulo = _replicas(40, 0.0, 300, 1000)
    assert 0.90 <= cobertura <= 0.99
    assert h1_nulo < 0.06  # a regra exige IC fora de zero E estimativa >= limiar


def test_poder_da_regra_com_efeito_moderado():
    _, h1 = _replicas(60, 6.0, 200, 5000)
    assert h1 > 0.8


# =========================================================== randomização
def test_sequencias_armazenadas_reproduzem_e_balanceiam():
    for c in carrega("randomizacao_casos.json")["dados"]:
        seq = randomizacao.gerar_sequencia(c["estratos"], c["semente"])
        assert seq == c["sequencia"] and randomizacao.carimbo(seq) == c["carimbo_sha256"], c["id"]
        for est, n in c["estratos"].items():
            assert len(seq[est]) == n
            cont = [seq[est].count(b) for b in "ABC"]
            assert max(cont) - min(cont) <= 3


def test_carimbo_detecta_troca_de_uma_alocacao():
    seq = randomizacao.gerar_sequencia({"E": 30}, 1)
    adulterada = {"E": list(seq["E"])}
    adulterada["E"][0] = "A" if adulterada["E"][0] != "A" else "B"
    assert randomizacao.carimbo(seq) != randomizacao.carimbo(adulterada)


def test_randomizacao_rejeita_bloco_invalido_e_cli_grava_csv(tmp_path, capsys):
    with pytest.raises(ValueError):
        randomizacao.gerar_sequencia({"E": 10}, 1, tamanhos_bloco=(4,))
    out = tmp_path / "seq.csv"
    randomizacao.main(["--estratos", "A-1:6,B-2:9", "--seed", "3", "--saida", str(out)])
    linhas = out.read_text(encoding="utf-8").strip().splitlines()
    assert linhas[0] == "estrato,ordem_inclusao,braco" and len(linhas) == 1 + 15
    assert "carimbo SHA-256" in capsys.readouterr().out


# =========================================================== séries, decodificador e gerador
SER = por_id("series_vazamento.json")


def test_sem_sinal_validacao_aleatoria_infla_e_blocos_ficam_no_acaso():
    s = SER["sem_sinal"]
    r = dec.comparar_validacoes(np.array(s["X"]), np.array(s["y"]), 5, 40)
    assert r["aleatoria"] > r["blocos"] + 0.15 and r["blocos"] < 1 / 3 + 0.20


def test_com_sinal_blocos_detectam_o_sinal():
    s = SER["com_sinal"]
    _, acc = dec.avaliar_classificacao(np.array(s["X"]), np.array(s["y"]), 5, 40, lam=10.0)
    assert acc > 0.6


def test_gerador_de_padroes_na_bateria():
    p = carrega("padroes_temporais.json")["dados"]
    assert dec.avaliar_geracao(np.array(p["X"]), np.array(p["T"]), 5, 5, lam=10.0) > 0.5


def test_divisoes_rejeitam_parametros_invalidos():
    with pytest.raises(ValueError):
        list(dec.divisoes_por_blocos(10, 1))
    with pytest.raises(ValueError):
        list(dec.divisoes_por_blocos(3, 5))


def test_proba_soma_um_e_classes_preservadas():
    X, y = sintetico.padroes_temporais(n=60, n_carac=8)[0], np.tile(["a", "b", "c"], 20)
    m = dec.DecodificadorLinear().fit(X, y)
    p = m.predict_proba(X)
    assert np.allclose(p.sum(1), 1) and set(m.predict(X)) <= {"a", "b", "c"}


# =========================================================== bloqueio
BLQ = por_id("bloqueio_cenarios.json")


def _bl(cid, **kw):
    c = BLQ[cid]
    return bloqueio.analisar_bloqueio(c["linhas"], chance=c["chance"], **kw)


def test_bloqueio_efeito_forte_e_ausente():
    f = _bl("efeito_ampa_forte_n8")
    assert f["AMPA"]["ic95_bootstrap"][1] < 0 and f["AMPA"]["p_permutacao"] < 0.05
    assert f["NMDA"]["media_efeito"] < 0 and f["AMPA"]["media_efeito"] < f["NMDA"]["media_efeito"]
    assert f["fracao_recuperacao_lavagem"] == 1 and f["fracao_ttx_no_acaso"] == 1
    n = _bl("sem_efeito_n8")
    assert abs(n["AMPA"]["media_efeito"]) < 0.05 and n["AMPA"]["p_permutacao"] > 0.05
    lo, hi = n["AMPA"]["ic95_bootstrap"]
    assert lo <= 0 <= hi


def test_bloqueio_n_pequeno_e_n_grande():
    p = _bl("n3_descritivo")
    assert p["AMPA"]["ic95_bootstrap"] is None and p["AMPA"]["n"] == 3
    assert p["AMPA"]["p_permutacao"] >= 1 / 8 - 1e-9  # com n = 3 o menor p exato possível é 2/8
    g = _bl("n20_permutacao_aproximada")
    assert g["AMPA"]["n"] == 20 and g["AMPA"]["p_permutacao"] < 0.05


def test_bloqueio_sinaliza_falhas_de_controle():
    t = _bl("ttx_falha_em_o0")
    assert t["fracao_ttx_no_acaso"] == pytest.approx(5 / 6) and any("TTX" in a for a in t["avisos"])
    l = _bl("lavagem_falha_em_o0")
    assert l["fracao_recuperacao_lavagem"] < 1 and any("lavagem" in a for a in l["avisos"])


def test_bloqueio_condicao_ausente_e_sem_chance():
    c = _bl("condicao_ausente")
    assert c["NMDA"]["n"] == 5 and c["AMPA"]["n"] == 6
    sem = bloqueio.analisar_bloqueio(BLQ["efeito_ampa_forte_n8"]["linhas"])  # sem `chance`
    assert "fracao_ttx_no_acaso" not in sem
    vazio = bloqueio.analisar_bloqueio(BLQ["efeito_ampa_forte_n8"]["linhas"], condicoes=("AMPA", "DROGA_X"))
    assert any("DROGA_X" in a for a in vazio["avisos"])


def test_bloqueio_controles_de_veiculo_separam_deriva_de_efeito():
    real = _bl("controles_efeito_real_n6")
    assert real["n_organoides"] == 6 and real["n_controles"] == 6 and not any("sem organoides-controle" in a for a in real["avisos"])
    liq = real["AMPA"]["efeito_liquido"]
    assert liq["diferenca_tratado_menos_controle"] == pytest.approx(-0.30, abs=0.06)
    assert liq["ic95_bootstrap"][1] < 0 and liq["p_permutacao"] < 0.05
    # só deriva: os tratados SOZINHOS parecem ter efeito; descontados os controles, não
    d = _bl("controles_so_deriva_n6")
    assert d["AMPA+NMDA"]["media_efeito"] < -0.1 and d["AMPA+NMDA"]["p_permutacao"] < 0.05
    liq = d["AMPA+NMDA"]["efeito_liquido"]
    assert abs(liq["diferenca_tratado_menos_controle"]) < 0.08 and liq["ic95_bootstrap"][0] <= 0 <= liq["ic95_bootstrap"][1]
    assert d["fracao_recuperacao_lavagem_controle"] < 1 and any("controles de veículo" in a for a in d["avisos"])


def test_bloqueio_poucos_controles_nao_calcula_ic_liquido():
    c = _bl("controles_n3_descritivo")
    assert c["n_controles"] == 3
    assert c["AMPA"]["efeito_liquido"]["ic95_bootstrap"] is None and c["AMPA"]["efeito_liquido"]["p_permutacao"] > 0
    assert any("efeito líquido" in a for a in c["avisos"])


def test_cenarios_sem_controle_continuam_sem_grupo_e_avisam():
    assert all("grupo" not in l for l in BLQ["efeito_ampa_forte_n8"]["linhas"])
    assert any("sem organoides-controle" in a for a in _bl("efeito_ampa_forte_n8")["avisos"])


def test_ordem_contrabalancada_armazenada():
    for cid, c in BLQ.items():
        n = len(c["ordem"])
        ampa_primeiro = sum(v[0] == "AMPA" for v in c["ordem"].values())
        assert ampa_primeiro in (n // 2, n - n // 2), cid
        assert all(sorted(v) == ["AMPA", "NMDA"] for v in c["ordem"].values())


def test_permutacao_exata_valor_conhecido():
    # n = 2, efeitos (+1, +1): 4 sinais, só 2 dão |média| = 1 → p = 2/4
    assert bloqueio._permutacao_sinais([1.0, 1.0]) == pytest.approx(0.5)
    assert bloqueio._permutacao_sinais([0.0, 0.0, 0.0]) == pytest.approx(1.0)


# =========================================================== esteira
EST = carrega("esteira_itens.json")["dados"]
ESQ, ROT = EST["esquema"], EST["rotulos"]


def _camada(nome):
    saidas = EST["camadas"][nome]["saidas"]
    return esteira.CamadaTipada(nome, lambda item: saidas[item["id"]], ESQ)


def _rodar(*nomes):
    return esteira.executar_esteira(EST["itens"], ROT, [_camada(n) for n in nomes], ESQ,
                                    grupos=[i["organoide"] for i in EST["itens"]], n_boot=300)


def test_calibracao_das_camadas():
    r = _rodar("calibrada", "superconfiante", "subconfiante")
    assert r["calibrada"]["ece"] < 0.10
    assert r["superconfiante"]["ece"] > 0.25 and r["subconfiante"]["ece"] > 0.25
    assert r["calibrada"]["brier"] < r["superconfiante"]["brier"]
    assert r["subconfiante"]["acuracia"] > r["calibrada"]["acuracia"] > r["superconfiante"]["acuracia"]
    for m in r.values():
        lo, hi = m["ic95_acuracia"]
        assert lo <= m["acuracia"] <= hi and m["latencia_p95_ms"] >= m["latencia_mediana_ms"] >= 0


def test_saidas_invalidas_sao_contadas_como_erro():
    c = EST["camadas"]["com_saidas_invalidas"]
    m = _rodar("com_saidas_invalidas")["com_saidas_invalidas"]
    assert m["taxa_invalida"] == pytest.approx(0.25) and m["acuracia"] <= 0.75
    # cada tipo de defeito, isolado, é detectado
    cam = esteira.CamadaTipada("x", lambda i: i, ESQ)
    vistos = set()
    for saida, tipo in zip(c["saidas"], c["tipos_de_defeito"]):
        if tipo:
            assert cam.decidir(saida).valida is False, tipo
            vistos.add(tipo)
    assert len(vistos) == 5


def test_camada_que_levanta_excecao_ou_so_invalida():
    def explode(_):
        raise RuntimeError("falha de rede")
    r = esteira.executar_esteira([1, 2, 3], [0, 1, 2], [esteira.CamadaTipada("e", explode, [0, 1, 2])], [0, 1, 2], n_boot=50)["e"]
    assert r["acuracia"] == 0 and r["taxa_invalida"] == 1 and "brier" not in r and "ece" not in r


def test_mapa_de_probabilidades_aceito_e_regra_fixa_sem_probabilidades():
    cam = esteira.CamadaTipada("m", lambda i: {0: 0.2, 2: 0.8}, [0, 1, 2])
    d = cam.decidir(None)
    assert d.valida and d.rotulo == 2 and d.probs.tolist() == [0.2, 0.0, 0.8]
    r = esteira.executar_esteira(list(range(10)), [0] * 10, [esteira.CamadaRegraFixa("r", lambda i: 0)], [0, 1], n_boot=50)["r"]
    assert r["acuracia"] == 1 and "ece" not in r


def test_risco_cobertura_e_confianca_informativa():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 400)
    # confiança alta apenas nos itens acertados -> acurácia seletiva cai com a cobertura
    certo = rng.random(400) < 0.7
    saidas = []
    for yi, ok in zip(y, certo):
        esc = yi if ok else 1 - yi
        conf = 0.9 if ok else 0.55
        p = [1 - conf, 1 - conf]; p[esc] = conf
        saidas.append(p)
    cam = esteira.CamadaTipada("c", lambda i: saidas[i], [0, 1])
    rc = esteira.executar_esteira(list(range(400)), y, [cam], [0, 1], n_boot=50)["c"]["risco_cobertura"]
    assert rc[0][1] > rc[-1][1] and rc[-1][0] == 1.0


def test_organoide_como_camada_usa_latencia_externa_quando_dada():
    X, y = sintetico.padroes_temporais(n=90, n_carac=6)[0], np.tile([0, 1, 2], 30)
    m = dec.DecodificadorLinear().fit(X, y)
    cam = esteira.CamadaOrganoide("org", m, latencia_externa_ms=lambda it: 42.0)
    assert cam.decidir(X[0]).latencia_ms == 42.0 and cam.decidir(X[0]).valida


# =========================================================== amostra
def test_amostra_monotonia_e_validacao():
    assert amostra.n_por_braco(0.3) > amostra.n_por_braco(0.5) > amostra.n_por_braco(0.8)
    assert amostra.n_por_braco(0.5, potencia=0.9) > amostra.n_por_braco(0.5, potencia=0.8)
    assert amostra.n_por_braco(0.5, alpha=0.01) > amostra.n_por_braco(0.5, alpha=0.05)
    assert amostra.n_por_braco(0.5, r=0.8) < amostra.n_por_braco(0.5, r=0.2)
    for kw in ({"d": 0}, {"d": -1}, {"d": 0.5, "r": 1.0}, {"d": 0.5, "r": -0.1}):
        with pytest.raises(ValueError):
            amostra.n_por_braco(**kw)


def test_ancova_amostra_insuficiente_levanta_erro():
    with pytest.raises(ValueError):
        analise.ancova([1.0, 2.0, 3.0], [1.0, 2.0, 2.5], [0, 1, 1])


# =========================================================== SNN (dados armazenados)
SNN = carrega("snn_contagens.json")["dados"]


def test_snn_formato_e_efeito_dos_bloqueadores_nos_dados():
    n_feat = SNN["n_exc"] * SNN["n_bins"]
    for o in SNN["organoides"]:
        s = o["sessoes"]
        assert set(s) == {"basal", "AMPA", "NMDA", "AMPA+NMDA"}
        for c, v in s.items():
            X = np.array(v["X"]); y = np.array(v["y"])
            assert X.shape == (24, n_feat) and set(y.tolist()) == {0, 1, 2} and X.min() >= 0
        tot = {c: np.array(v["X"]).sum() for c, v in s.items()}
        assert tot["basal"] > tot["AMPA"] and tot["basal"] > tot["AMPA+NMDA"]
        assert tot["AMPA+NMDA"] <= tot["AMPA"]
        _, acc = dec.avaliar_classificacao(np.array(s["basal"]["X"]), np.array(s["basal"]["y"]), 4, 2, lam=50.0)
        assert acc > 1 / 3 + 0.2


# =========================================================== modelos de planilha
TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def _cabecalho(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8").splitlines()[0].split(",")


def test_templates_tem_as_colunas_que_os_modulos_esperam():
    assert {"braco", "estrato", "t0_raciocinio", "t1_raciocinio"} <= set(_cabecalho("dados_estudantes.csv"))
    assert {"organoide", "condicao", "valor"} <= set(_cabecalho("bloqueio_organoides.csv"))
    assert {"rotulo_verdadeiro", "rotulo_previsto", "valida", "latencia_ms", "versao_modelo"} <= set(_cabecalho("esteira_itens.csv"))
    cod = (TEMPLATES / "CODEBOOK.md").read_text(encoding="utf-8")
    for nome in TEMPLATES.glob("*.csv"):
        assert nome.name in cod, f"{nome.name} sem entrada no dicionário de dados"


def test_condicoes_do_codebook_sao_as_do_codigo():
    cod = (TEMPLATES / "CODEBOOK.md").read_text(encoding="utf-8")
    for c in bloqueio.CONDICOES:
        assert f"`{c}`" in cod


# =========================================================== v2: protocolo da raiz e inspiração MetaBCI
def test_qualificacao_dos_organoides_confere_com_os_casos():
    for c in carrega("qualificacao_organoides.json")["dados"]:
        r = bloqueio.qualificar_organoide(**c["entradas"])
        assert r["qualificado"] is c["qualificado_esperado"], c["id"]
        assert (len(r["motivos"]) == 0) is c["qualificado_esperado"]
    inval = bloqueio.qualificar_organoide(40, 0.5, False)
    assert sum("invalida" in m for m in inval["motivos"]) == 2


def test_bloqueio_conjunto_e_terceira_lavagem():
    f = _bl("efeito_ampa_forte_n8")
    assert f["AMPA+NMDA"]["media_efeito"] < f["AMPA"]["media_efeito"] < 0
    linhas = BLQ["efeito_ampa_forte_n8"]["linhas"]
    assert {l["condicao"] for l in linhas} == set(bloqueio.CONDICOES)


def test_nrmse_valores_de_referencia_e_geracao():
    alvo = np.sin(np.linspace(0, 6, 100))
    assert dec.nrmse(alvo, alvo) == 0
    assert dec.nrmse(np.full(100, alvo.mean()), alvo) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        dec.nrmse([1, 2], [3, 3])
    p = carrega("padroes_temporais.json")["dados"]
    assert dec.avaliar_geracao(np.array(p["X"]), np.array(p["T"]), 5, 5, lam=10.0, metrica="nrmse") < 0.9


def test_acaso_por_permutacao_circular():
    s0, s1 = SER["sem_sinal"], SER["com_sinal"]
    _, nul0, p0 = dec.acaso_por_permutacao(np.array(s0["X"]), np.array(s0["y"]), n_perm=30, gap=40)
    _, _, p1 = dec.acaso_por_permutacao(np.array(s1["X"]), np.array(s1["y"]), n_perm=30, gap=40, lam=10.0)
    assert p0 > 0.05 and p1 < 0.05 and len(nul0) == 30


def test_itr_de_wolpaw():
    assert esteira.itr_wolpaw(1.0, 2, 1.0) == pytest.approx(60.0)
    assert esteira.itr_wolpaw(0.5, 2, 1.0) == 0.0 and esteira.itr_wolpaw(0.2, 4, 1.0) == 0.0
    P, N, T = 0.9, 4, 2.0
    esperado = (np.log2(N) + P * np.log2(P) + (1 - P) * np.log2((1 - P) / (N - 1))) * 60 / T
    assert esteira.itr_wolpaw(P, N, T) == pytest.approx(esperado)
    with pytest.raises(ValueError):
        esteira.itr_wolpaw(0.9, 1, 1.0)
    r = _rodar("calibrada")  # sem t_decisao_s não há ITR
    assert "itr_bits_min" not in r["calibrada"]
    r = esteira.executar_esteira(EST["itens"], ROT, [_camada("calibrada")], ESQ, n_boot=50, t_decisao_s=2.0)
    assert r["calibrada"]["itr_bits_min"] > 0


def test_reprodutibilidade_entre_chamadas():
    det = _camada("calibrada")
    r = esteira.medir_reprodutibilidade(det, EST["itens"][:20], repeticoes=3)
    assert r["fracao_decisoes_identicas"] == 1.0 and r["desvio_medio_probabilidades"] == pytest.approx(0, abs=1e-12)
    rng = np.random.default_rng(0)

    def ruidosa(_):
        p = rng.dirichlet([1, 1, 1])
        return p
    r2 = esteira.medir_reprodutibilidade(esteira.CamadaTipada("r", ruidosa, ESQ), EST["itens"][:20], repeticoes=3)
    assert r2["fracao_decisoes_identicas"] < 0.8 and r2["desvio_medio_probabilidades"] > 0


def test_contrato_json_da_esteira():
    esquema_json = json.loads((PASTA.parent / "docs" / "contrato_esteira.schema.json").read_text(encoding="utf-8"))
    saida = esquema_json["$defs"]["saida"]
    cam = _camada("com_saidas_invalidas")
    for item in EST["itens"][:20]:
        reg = esteira.decisao_para_contrato(cam.decidir(item), item["id"], cam.nome, ESQ, "v-teste")
        assert set(reg) == set(saida["properties"]) and set(saida["required"]) <= set(reg)
        json.dumps(reg)
        if not reg["valida"]:
            assert reg["rotulo"] is None and reg["probabilidades"] is None
        else:
            assert sum(reg["probabilidades"].values()) == pytest.approx(1.0)


# =========================================================== v3: critérios explícitos e dados ausentes
def test_ausencia_de_medida_nunca_aprova_em_silencio():
    r = bloqueio.qualificar_organoide(40, 0.05, True, None)
    assert r["qualificado"] and r["criterios"]["ttx"] == "nao_avaliado" and r["avisos"]
    assert not bloqueio.qualificar_organoide(40, 0.05, True, None, ttx_obrigatorio=True)["qualificado"]
    for kw in ({"cruzamentos_limiar": None}, {"variacao_veiculo": None}, {"recuperou_lavagem": None}):
        base = dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=0.95)
        base.update(kw)
        assert not bloqueio.qualificar_organoide(**base)["qualificado"], kw
    assert bloqueio.qualificar_organoide(40, None, None)["invalidado"] is True
    assert bloqueio.qualificar_organoide(5, 0.0, True)["invalidado"] is False  # atividade baixa exclui, não invalida


def test_formulas_de_variacao_e_reducao():
    assert bloqueio.variacao_relativa(12.0, 10.0) == pytest.approx(0.2)
    assert bloqueio.reducao_relativa(1000, 50) == pytest.approx(0.95)
    for f, args in ((bloqueio.variacao_relativa, (1.0, 0.0)), (bloqueio.reducao_relativa, (0, 1)),
                    (bloqueio.variacao_relativa, (None, 1.0))):
        with pytest.raises(ValueError):
            f(*args)
    assert bloqueio.qualificar_organoide.__defaults__ is not None
    assert bloqueio.LIMIARES_PROVISORIOS["margem_veiculo"] == 0.20 and bloqueio.LIMIARES_PROVISORIOS["min_reducao_ttx"] == 0.90


def test_lavagem_absoluta_x_relativa():
    linhas = [{"organoide": "o0", "condicao": c, "valor": v} for c, v in
              (("basal", 0.50), ("veiculo", 0.50), ("AMPA", 0.30), ("lavagem1", 0.44))]
    # diferença de 0,06: passa na tolerância absoluta de 0,10, mas é 12% do basal (falha em 10% relativo)
    assert bloqueio.analisar_bloqueio(linhas, condicoes=("AMPA",))["fracao_recuperacao_lavagem"] == 1.0
    assert bloqueio.analisar_bloqueio(linhas, condicoes=("AMPA",), escala_lavagem="relativa")["fracao_recuperacao_lavagem"] == 0.0
    with pytest.raises(ValueError):
        bloqueio.analisar_bloqueio(linhas, escala_lavagem="percentual")
