"""Bateria de dados SINTÉTICOS (JSON) para testar o software do framework.

Cada arquivo tem o formato  {"meta": {...}, "dados": ...}  com `meta.sintetico = true`.
Nenhum arquivo representa estudantes ou organoides reais; os cenários existem para
exercitar o código em situações conhecidas (efeito nulo, efeito conhecido, amostra de
piloto, atrito, teto, vazamento temporal, falhas de controle, saídas inválidas etc.).

Geração determinística por semente (ponto flutuante arredondado a 6 casas):

    python exemplos/gerar_dados_sinteticos.py --saida ../dados_sinteticos

O `manifesto.json` guarda SHA-256 e tamanho de cada arquivo. Os arquivos da rede
simulada (`snn_contagens.json`) dependem de aritmética de ponto flutuante e podem
diferir em outras plataformas; por isso o teste de regeneração os exclui.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from . import __version__, bloqueio, randomizacao, sintetico
from .snn import RedeSNN, gerar_conjunto, gerar_padroes

VERSAO_BATERIA = "4"
AVISO = ("DADOS SINTÉTICOS gerados por simulação para testar software. Não são dados de "
         "estudantes nem de organoides e não constituem evidência sobre nenhum dos dois.")
ARQUIVOS_PLATAFORMA_DEPENDENTES = {"snn_contagens.json"}


def _limpa(o, nd=6):
    if isinstance(o, dict):
        return {str(k): _limpa(v, nd) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpa(v, nd) for v in o]
    if isinstance(o, np.ndarray):
        return _limpa(o.tolist(), nd)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return round(float(o), nd)
    return o


def _meta(descricao, **extra):
    return {"sintetico": True, "aviso": AVISO, "descricao": descricao,
            "versao_bateria": VERSAO_BATERIA, "versao_pacote": __version__, **extra}


def _grava(pasta, nome, meta, dados, compacto=False):
    caminho = os.path.join(pasta, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"meta": _limpa(meta), "dados": _limpa(dados)}, f, ensure_ascii=False,
                  indent=None if compacto else 1, separators=(",", ":") if compacto else (",", ": "))
        f.write("\n")


# ------------------------------------------------------------------ estudantes
def _estudantes_cenarios():
    espec = [
        ("nulo_n15", "Sem efeito, tamanho de piloto (15 por braço).", dict(n_por_braco=15, efeito_A=0.0, seed=11)),
        ("nulo_n200", "Sem efeito, amostra grande (200 por braço): IC estreito em torno de zero.", dict(n_por_braco=200, efeito_A=0.0, seed=12)),
        ("efeito_03_n15", "Efeito verdadeiro de 3 pontos (d = 0,3), piloto de 15 por braço.", dict(n_por_braco=15, efeito_A=3.0, seed=13)),
        ("efeito_06_n60", "Efeito verdadeiro de 6 pontos (d = 0,6), 60 por braço.", dict(n_por_braco=60, efeito_A=6.0, seed=14)),
        ("efeito_10_n200", "Efeito verdadeiro de 10 pontos (d = 1,0), 200 por braço.", dict(n_por_braco=200, efeito_A=10.0, seed=15)),
        ("efeito_negativo_n200", "Efeito verdadeiro de -6 pontos no braço A, 200 por braço.", dict(n_por_braco=200, efeito_A=-6.0, seed=16)),
        ("correlacao_baixa_n60", "Correlação pré-pós baixa (0,2): a covariável ajuda pouco.", dict(n_por_braco=60, efeito_A=0.0, r_pre_pos=0.2, seed=17)),
        ("correlacao_alta_n60", "Correlação pré-pós alta (0,9).", dict(n_por_braco=60, efeito_A=0.0, r_pre_pos=0.9, seed=18)),
        ("um_estrato_n30", "Um único estrato (escola x série).", dict(n_por_braco=30, efeito_A=0.0, estratos=("U-1",), seed=19)),
        ("cinco_estratos_n30", "Cinco estratos.", dict(n_por_braco=30, efeito_A=0.0, estratos=tuple(f"E{i}-1" for i in range(5)), seed=20)),
    ]
    saida = []
    for id_, desc, p in espec:
        est = sintetico.estudantes(**p)
        saida.append({"id": id_, "descricao": desc,
                      "parametros": {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.items()},
                      "efeito_verdadeiro_pontos": p["efeito_A"], "dp_escore": 10.0, "estudantes": est})
    # atrito diferencial: 30% dos randomizados do braço A sem T1; 10% nos demais
    rng = np.random.default_rng(21)
    est = sintetico.estudantes(n_por_braco=40, efeito_A=3.0, seed=21)
    for e in est:
        if rng.random() < (0.30 if e["braco"] == "A" else 0.10):
            e["t1"] = None
    saida.append({"id": "atrito_diferencial_n40", "descricao": "Atrito diferencial: ~30% sem T1 no braço A e ~10% nos demais (t1 = null).",
                  "parametros": {"n_por_braco": 40, "efeito_A": 3.0, "seed": 21}, "efeito_verdadeiro_pontos": 3.0,
                  "dp_escore": 10.0, "estudantes": est})
    # efeito de teto: escores de 0 a 100, média 90 em T0, truncados em 100
    rng = np.random.default_rng(22)
    teto = []
    for b in "ABC":
        for i in range(40):
            t0 = float(np.clip(rng.normal(90, 8), 0, 100))
            t1 = float(np.clip(90 + 0.6 * (t0 - 90) + rng.normal(0, 7), 0, 100))
            teto.append({"braco": b, "estrato": f"E{i % 2}-1", "t0": t0, "t1": t1})
    saida.append({"id": "teto_t0", "descricao": "Efeito de teto: T0 com média 90 em escala de 0 a 100, truncado no máximo.",
                  "parametros": {"maximo": 100, "seed": 22}, "efeito_verdadeiro_pontos": 0.0, "dp_escore": 8.0, "estudantes": teto})
    return saida


# ------------------------------------------------------------------ randomização
def _randomizacao_casos():
    config = [
        ("dois_estratos", {"EscolaX-1": 30, "EscolaX-2": 30}, 2026),
        ("seis_estratos", {f"E{i}-{s}": 18 for i in range(1, 4) for s in (1, 2)}, 7),
        ("estrato_pequeno", {"Pequena-1": 5}, 99),
        ("estrato_grande", {"Grande-1": 300}, 5),
    ]
    out = []
    for id_, est, seed in config:
        seq = randomizacao.gerar_sequencia(est, seed)
        out.append({"id": id_, "estratos": est, "semente": seed, "sequencia": seq, "carimbo_sha256": randomizacao.carimbo(seq)})
    return out


# ------------------------------------------------------------------ séries (vazamento) e padrões
def _series():
    def serie(seed, sinal):
        X, y = sintetico.serie_autocorrelacionada(n=300, n_carac=30, seed=seed)
        if sinal:
            rng = np.random.default_rng(seed + 1000)
            X = X + sinal * np.eye(3)[y] @ rng.normal(size=(3, 30))
        return {"X": X, "y": y}
    return [
        {"id": "sem_sinal", "descricao": "Características = ruído AR(1) (rho = 0,97), independente dos rótulos (que persistem 40 amostras). Acurácia real = acaso (0,33).", "n_classes": 3, "sinal": 0.0, **serie(30, 0.0)},
        {"id": "com_sinal", "descricao": "Mesmo ruído AR(1) mais um sinal linear dependente da classe (amplitude 1,2).", "n_classes": 3, "sinal": 1.2, **serie(31, 1.2)},
    ]


def _padroes():
    X, T = sintetico.padroes_temporais(n=240, n_carac=30, L=16, seed=40)
    return {"X": X, "T": T, "L": 16}


# ------------------------------------------------------------------ bloqueio
def _bloqueio_cenarios():
    def janela(cond, par):
        """Posição temporal da condição na sessão (1 = veículo), dada a ordem AMPA/NMDA do organoide."""
        return {"veiculo": 1, par[0]: 2, "lavagem1": 3, par[1]: 4, "lavagem2": 5, "AMPA+NMDA": 6, "lavagem3": 7}.get(cond, 0)

    def tabela(n, efeito_ampa, efeito_nmda, seed, ruido=0.03, ttx=0.33, falha_ttx=(), falha_lavagem=(), sem_nmda=(),
               n_controle=0, deriva=0.0):
        """`n_controle` organoides recebem só veículo em todas as janelas (grupo "controle"). `deriva` é a
        mudança lenta e cumulativa por janela (somada a tratados e controles), que o efeito líquido separa."""
        rng = np.random.default_rng(seed)
        ordem = bloqueio.ordem_contrabalancada([f"o{i}" for i in range(n)], seed=seed)
        linhas = []

        def com_deriva(v, par):
            if deriva:
                for c in v:
                    if c != "TTX":
                        v[c] += deriva * max(0, janela(c, par) - 1)
            return v

        for i in range(n):
            o = f"o{i}"
            base = 0.8 + rng.normal(0, 0.03)
            v = {"basal": base, "veiculo": base + rng.normal(0, ruido),
                 "AMPA": base + efeito_ampa + rng.normal(0, ruido), "NMDA": base + efeito_nmda + rng.normal(0, ruido),
                 "AMPA+NMDA": base + efeito_ampa + efeito_nmda + rng.normal(0, ruido),
                 "lavagem1": base + rng.normal(0, ruido), "lavagem2": base + rng.normal(0, ruido),
                 "lavagem3": base + rng.normal(0, ruido), "TTX": ttx}
            v = com_deriva(v, ordem[o])
            if o in falha_ttx:
                v["TTX"] = 0.8
            if o in falha_lavagem:
                v["lavagem1"] = base - 0.3
            for c, val in v.items():
                if c == "NMDA" and o in sem_nmda:
                    continue
                linha = {"organoide": o, "condicao": c, "valor": float(np.clip(val, 0, 1))}
                if n_controle:
                    linha["grupo"] = "tratado"
                linhas.append(linha)
        if n_controle:
            ordem_c = bloqueio.ordem_contrabalancada([f"c{j}" for j in range(n_controle)], seed=seed + 1)
            ordem = {**ordem, **ordem_c}
            for j in range(n_controle):
                o = f"c{j}"
                base = 0.8 + rng.normal(0, 0.03)
                v = {"basal": base, "veiculo": base + rng.normal(0, ruido)}
                for c in ("AMPA", "NMDA", "AMPA+NMDA", "lavagem1", "lavagem2", "lavagem3"):
                    v[c] = base + rng.normal(0, ruido)   # só veículo: `condicao` rotula a janela
                v = com_deriva(v, ordem[o])
                linhas += [{"organoide": o, "condicao": c, "valor": float(np.clip(val, 0, 1)), "grupo": "controle"}
                           for c, val in v.items()]
        return {"linhas": linhas, "ordem": {o: list(v) for o, v in ordem.items()}}
    espec = [
        ("efeito_ampa_forte_n8", "AMPA reduz a acurácia em 0,30; NMDA em 0,10; 8 organoides.", tabela(8, -0.30, -0.10, 50), 1 / 3),
        ("sem_efeito_n8", "Nenhum bloqueador altera o desempenho; 8 organoides.", tabela(8, 0.0, 0.0, 51), 1 / 3),
        ("n3_descritivo", "Apenas 3 organoides: IC não deve ser calculado.", tabela(3, -0.30, -0.10, 52), 1 / 3),
        ("n20_permutacao_aproximada", "20 organoides (n > 15): teste de permutação por simulação.", tabela(20, -0.20, -0.05, 53), 1 / 3),
        ("ttx_falha_em_o0", "TTX não leva o organoide o0 ao acaso (suspeita de artefato).", tabela(6, -0.30, -0.10, 54, falha_ttx=("o0",)), 1 / 3),
        ("lavagem_falha_em_o0", "Sem recuperação na lavagem 1 do organoide o0 (deriva ou dano).", tabela(6, -0.30, -0.10, 55, falha_lavagem=("o0",)), 1 / 3),
        ("condicao_ausente", "O organoide o1 não tem a condição NMDA.", tabela(6, -0.30, -0.10, 56, sem_nmda=("o1",)), 1 / 3),
        ("controles_efeito_real_n6", "6 tratados (AMPA -0,30; NMDA -0,10) e 6 controles só com veículo, sem deriva: o efeito líquido recupera o efeito do fármaco.",
         tabela(6, -0.30, -0.10, 57, n_controle=6), 1 / 3),
        ("controles_so_deriva_n6", "6 tratados SEM efeito do fármaco e 6 controles, com deriva de -0,03 por janela: sozinhos, os tratados parecem ter efeito; o efeito líquido é ~0.",
         tabela(6, 0.0, 0.0, 58, n_controle=6, deriva=-0.03), 1 / 3),
        ("controles_n3_descritivo", "6 tratados e só 3 controles: o IC do efeito líquido não deve ser calculado.",
         tabela(6, -0.30, -0.10, 59, n_controle=3), 1 / 3),
    ]
    return [{"id": i, "descricao": d, "chance": c, **t} for i, d, t, c in espec]


def _qualificacao_casos():
    """Casos para os critérios de qualificação (§3.4 de Protocolo_AMPA_NMDA.md), com o veredito esperado."""
    casos = [
        ("qualificado", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=0.97), True),
        ("pouca_atividade", dict(cruzamentos_limiar=6, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=0.97), False),
        ("veiculo_alterou", dict(cruzamentos_limiar=40, variacao_veiculo=-0.35, recuperou_lavagem=True, reducao_ttx=0.97), False),
        ("sem_lavagem", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=False, reducao_ttx=0.97), False),
        ("ttx_fraco", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=0.60), False),
        ("sem_ttx_aplicado", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=None), True),
        ("ttx_ausente_obrigatorio", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=True, reducao_ttx=None, ttx_obrigatorio=True), False),
        ("lavagem_nao_avaliada", dict(cruzamentos_limiar=40, variacao_veiculo=0.05, recuperou_lavagem=None, reducao_ttx=0.97), False),
        ("veiculo_nao_medido", dict(cruzamentos_limiar=40, variacao_veiculo=None, recuperou_lavagem=True, reducao_ttx=0.97), False),
        ("limiares_exatos", dict(cruzamentos_limiar=10, variacao_veiculo=0.20, recuperou_lavagem=True, reducao_ttx=0.90), True),
    ]
    return [{"id": i, "entradas": e, "qualificado_esperado": q} for i, e, q in casos]


# ------------------------------------------------------------------ esteira
def _esteira_itens():
    rng = np.random.default_rng(60)
    n, K = 300, 3
    rotulos = rng.integers(0, K, n)
    grupos = np.repeat(np.arange(6), n // 6)
    itens = [{"id": i, "organoide": int(g)} for i, g in enumerate(grupos)]

    def saida_probs(acc, conf):
        """Distribuição que aponta ao rótulo certo com prob. `acc` e tem confiança `conf` no escolhido."""
        r = []
        for y in rotulos:
            escolhido = y if rng.random() < acc else int((y + 1 + rng.integers(0, K - 1)) % K)
            p = np.full(K, (1 - conf) / (K - 1)); p[escolhido] = conf
            r.append(p.tolist())
        return r

    camadas = {
        "calibrada": {"descricao": "Acurácia ~0,80 com confiança 0,80.", "saidas": saida_probs(0.80, 0.80)},
        "superconfiante": {"descricao": "Acurácia ~0,60 com confiança 0,97 (superconfiante).", "saidas": saida_probs(0.60, 0.97)},
        "subconfiante": {"descricao": "Acurácia ~0,90 com confiança 0,50.", "saidas": saida_probs(0.90, 0.50)},
    }
    # com defeitos: 25% inválidas, de cinco tipos (i % 20 < 5 → 25%)
    base = saida_probs(0.85, 0.85)
    defeitos = ["rotulo_fora_do_esquema", "tamanho_errado", "soma_diferente_de_1", "negativa", "nula"]
    saidas, tipos = [], []
    for i, p in enumerate(base):
        if i % 20 < 5:
            t = defeitos[i % 20]
            tipos.append(t)
            saidas.append({"rotulo_fora_do_esquema": {"0": 0.5, "9": 0.5}, "tamanho_errado": [0.5, 0.5],
                           "soma_diferente_de_1": [0.5, 0.5, 0.5], "negativa": [1.2, -0.2, 0.0], "nula": None}[t])
        else:
            tipos.append(None)
            saidas.append(p)
    camadas["com_saidas_invalidas"] = {"descricao": "Acurácia ~0,85 nas válidas; 25% de saídas inválidas de 5 tipos.", "saidas": saidas, "tipos_de_defeito": tipos}
    return {"esquema": list(range(K)), "rotulos": rotulos, "itens": itens, "camadas": camadas}


# ------------------------------------------------------------------ rede simulada
def _snn_contagens():
    padroes = gerar_padroes(3, seed=0)
    cond = {"basal": (0.0, 0.0), "AMPA": (0.5, 0.0), "NMDA": (0.0, 0.5), "AMPA+NMDA": (0.5, 0.5)}
    organoides = []
    for o in range(2):
        rede = RedeSNN(seed=200 + o)
        sess = {}
        for i, (c, (ba, bn)) in enumerate(cond.items()):
            X, y = gerar_conjunto(rede, padroes, n_por_classe=8, bloqueio_ampa=ba, bloqueio_nmda=bn, n_bins=2, seed=300 + 10 * o + i)
            sess[c] = {"bloqueio_ampa": ba, "bloqueio_nmda": bn, "X": X.astype(int), "y": y}
        organoides.append({"organoide": f"sim{o}", "sessoes": sess})
    return {"padroes_entrada_hz": padroes, "n_exc": 80, "n_bins": 2, "organoides": organoides}


# ------------------------------------------------------------------ geração
def gerar_todos(pasta: str) -> dict:
    os.makedirs(pasta, exist_ok=True)
    jobs = [
        ("estudantes_cenarios.json", "Cenários de piloto (braço, estrato, T0, T1) com efeito verdadeiro conhecido, atrito e teto.", _estudantes_cenarios, False),
        ("randomizacao_casos.json", "Sequências de alocação estratificada com semente e carimbo SHA-256.", _randomizacao_casos, False),
        ("series_vazamento.json", "Séries autocorrelacionadas com e sem sinal, para demonstrar vazamento na validação aleatória.", _series, True),
        ("padroes_temporais.json", "Características e padrões-alvo para o gerador linear de padrões temporais.", _padroes, True),
        ("bloqueio_cenarios.json", "Tabelas por organoide e condição (basal, veículo, AMPA, NMDA, lavagens, TTX), com falhas de controle e organoides-controle só com veículo (grupo \"controle\") e deriva.", _bloqueio_cenarios, False),
        ("qualificacao_organoides.json", "Casos para os critérios de qualificação de organoides (atividade, veículo, lavagem, TTX).", _qualificacao_casos, False),
        ("esteira_itens.json", "Saídas de camadas de decisão tipadas (calibrada, superconfiante, subconfiante, com saídas inválidas).", _esteira_itens, True),
        ("snn_contagens.json", "Contagens de disparos da rede LIF AMPA/NMDA (2 organoides simulados, 4 condições).", _snn_contagens, True),
    ]
    manifesto = []
    for nome, desc, fn, compacto in jobs:
        _grava(pasta, nome, _meta(desc), fn(), compacto)
        with open(os.path.join(pasta, nome), "rb") as f:
            b = f.read()
        manifesto.append({"arquivo": nome, "descricao": desc, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                          "depende_de_plataforma": nome in ARQUIVOS_PLATAFORMA_DEPENDENTES})
    _grava(pasta, "manifesto.json", _meta("Índice e somas de verificação da bateria sintética."), manifesto)
    return {m["arquivo"]: m for m in manifesto}
