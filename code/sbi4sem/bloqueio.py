"""Análise do bloqueio sequencial de AMPA e NMDA (teste 1 da tarefa-padrão).

Unidade experimental: o ORGANOIDE. Cada organoide percorre as condições
  basal -> veículo -> (AMPA | NMDA) -> lavagem1 -> (NMDA | AMPA) -> lavagem2
        -> AMPA+NMDA -> lavagem3 -> TTX (terminal e opcional)
com a ordem AMPA/NMDA contrabalançada entre organoides. Organoides-controle recebem só o
veículo, nos mesmos tempos, para separar a deriva temporal do efeito farmacológico.

Aplicar os bloqueadores exige parceiro habilitado e a documentação ética da ORIGEM do tecido.
O tecido adotado é hiPSC humana (decisão em docs/origem_do_tecido.md): consentimento do doador,
aprovação do comitê de origem e biossegurança de nível 2. A CEUA só caberia a organoides de
camundongo (plataforma de Elliott et al., 2023), opção descartada. A submissão do estudo com os
estudantes ao CEP/CONEP é independente disso. Doses e tempos são definidos pelo parceiro e
registrados antes da coleta. Este módulo só analisa os dados.

Abordagem por estatística-resumo: um valor por organoide e condição (média das janelas),
o que respeita a unidade experimental; um modelo misto com o organoide como efeito
aleatório é a alternativa quando se quer usar as janelas.

Para cada condição calcula-se, por organoide, o efeito = valor(condição) - valor(referência,
por padrão o veículo), e então: média, IC percentil por bootstrap entre organoides (apenas
com n >= 5; abaixo disso devolve None) e teste de permutação por troca de sinais (exato,
n <= 15). Verificações: recuperação na lavagem (|lavagem - basal| <= tolerância, absoluta ou relativa) e
controle com TTX (valor no nível do acaso ou abaixo). Com poucos organoides, os resultados
são descritivos.

Controles de veículo. Registros com `grupo = "controle"` (o padrão é `"tratado"`) são os
organoides que receberam só veículo. Neles, `condicao` rotula a JANELA (o instante em que o
organoide tratado equivalente receberia aquela condição) e `valor` é o medido sob veículo. Para
cada condição, o efeito por organoide nos controles é a DERIVA daquela janela em relação à
referência; o efeito líquido é a média dos tratados menos a média dos controles, com IC
bootstrap (cada grupo reamostrado separadamente, n >= 5 em cada um) e teste de permutação
dos rótulos de grupo (exato se couber em 20 000 combinações). Sem controles, a deriva lenta
não é separada do efeito farmacológico, e o resultado traz um aviso.
"""
from __future__ import annotations

import itertools
import math
import random
from collections import defaultdict

import numpy as np

CONDICOES = ("basal", "veiculo", "AMPA", "NMDA", "AMPA+NMDA", "lavagem1", "lavagem2", "lavagem3", "TTX")
LAVAGENS = ("lavagem1", "lavagem2", "lavagem3")
GRUPOS = ("tratado", "controle")


# Limiares PROVISÓRIOS (valores de partida, não validados experimentalmente). As definições
# finais, com justificativa, são fixadas no pré-registro antes da coleta.
LIMIARES_PROVISORIOS = {
    "min_cruzamentos": 10,      # cruzamentos de limiar (5 x RMS) em unidades-alvo, como no eNeuro
    "margem_veiculo": 0.20,     # |variação relativa da taxa de disparo| veículo x basal
    "min_reducao_ttx": 0.90,    # redução relativa de spikes com TTX x basal
    "tol_lavagem": 0.10,        # |lavagem - basal| na ESCALA DA MÉTRICA analisada (ver analisar_bloqueio)
    "margem_ttx_acaso": 0.05,   # acurácia do decodificador sob TTX <= acaso + margem
}


def variacao_relativa(valor: float, referencia: float) -> float:
    """(valor - referência) / referência. Para o veículo: taxa de disparo média das unidades-alvo
    na janela de veículo em relação à linha de base B0 do mesmo organoide."""
    if referencia is None or valor is None:
        raise ValueError("valor ou referência ausente")
    if referencia <= 0:
        raise ValueError("referência deve ser positiva")
    return (valor - referencia) / referencia


def reducao_relativa(antes: float, depois: float) -> float:
    """1 - depois/antes. Para o TTX: contagem de spikes sob TTX em relação à linha de base."""
    if antes is None or depois is None or antes <= 0:
        raise ValueError("contagens ausentes ou linha de base nula")
    return 1 - depois / antes


def qualificar_organoide(cruzamentos_limiar: int | None, variacao_veiculo: float | None,
                         recuperou_lavagem: bool | None, reducao_ttx: float | None = None,
                         ttx_obrigatorio: bool = False,
                         min_cruzamentos: int = LIMIARES_PROVISORIOS["min_cruzamentos"],
                         margem_veiculo: float = LIMIARES_PROVISORIOS["margem_veiculo"],
                         min_reducao_ttx: float = LIMIARES_PROVISORIOS["min_reducao_ttx"]) -> dict:
    """Critérios de qualificação do protocolo (Protocolo_AMPA_NMDA.md, §3.4), com limiares PROVISÓRIOS:

    (i)   atividade: pelo menos `min_cruzamentos` cruzamentos de limiar (5 x RMS);
    (ii)  veículo: |variacao_relativa(taxa no veículo, taxa em B0)| <= `margem_veiculo`;
    (iii) lavagem: a atividade volta ao basal (critério fixado no pré-registro);
    (iv)  TTX: reducao_relativa(spikes em B0, spikes sob TTX) >= `min_reducao_ttx`.

    Regra para dados ausentes: (i), (ii) e (iii) ausentes FALHAM (não há aprovação por
    omissão). (iv) ausente fica "nao_avaliado" e é relatado; se `ttx_obrigatorio`, falha.
    Falha em (ii) ou (iii) INVALIDA o organoide e deve ser relatada.
    """
    crit, motivos, avisos = {}, [], []

    def falha(nome, motivo):
        crit[nome] = "falha"; motivos.append(motivo)

    if cruzamentos_limiar is None:
        falha("atividade", "atividade não medida (i)")
    elif cruzamentos_limiar < min_cruzamentos:
        falha("atividade", "atividade insuficiente (i)")
    else:
        crit["atividade"] = "ok"
    if variacao_veiculo is None:
        falha("veiculo", "veículo não medido (ii): invalida")
    elif abs(variacao_veiculo) > margem_veiculo:
        falha("veiculo", "veículo alterou a atividade (ii): invalida")
    else:
        crit["veiculo"] = "ok"
    if recuperou_lavagem is None:
        falha("lavagem", "lavagem não avaliada (iii): invalida")
    elif not recuperou_lavagem:
        falha("lavagem", "sem recuperação na lavagem (iii): invalida")
    else:
        crit["lavagem"] = "ok"
    if reducao_ttx is None:
        if ttx_obrigatorio:
            falha("ttx", "TTX obrigatório e não aplicado (iv)")
        else:
            crit["ttx"] = "nao_avaliado"
            avisos.append("TTX não aplicado: critério (iv) não avaliado, e não aprovado")
    elif reducao_ttx < min_reducao_ttx:
        falha("ttx", "TTX não reduziu os spikes o suficiente (iv)")
    else:
        crit["ttx"] = "ok"
    return {"qualificado": not motivos, "invalidado": any("invalida" in m for m in motivos),
            "criterios": crit, "motivos": motivos, "avisos": avisos, "limiares_provisorios": True}


def ordem_contrabalancada(ids, seed: int = 0) -> dict:
    """Metade dos organoides recebe AMPA primeiro; a outra metade, NMDA primeiro."""
    ids = list(ids)
    rng = random.Random(seed)
    rng.shuffle(ids)
    return {o: ("AMPA", "NMDA") if i % 2 == 0 else ("NMDA", "AMPA") for i, o in enumerate(ids)}


def _permutacao_sinais(efeitos):
    e = np.asarray(efeitos, float)
    n = len(e)
    obs = abs(e.mean())
    if n > 15:
        rng = np.random.default_rng(0)
        sims = [abs((e * rng.choice([-1, 1], n)).mean()) for _ in range(20000)]
        return float((np.sum(np.array(sims) >= obs - 1e-12) + 1) / (len(sims) + 1))
    cont = tot = 0
    for s in itertools.product((-1, 1), repeat=n):
        tot += 1
        if abs((e * np.array(s)).mean()) >= obs - 1e-12:
            cont += 1
    return cont / tot


def _ic_boot(efeitos, n_boot=5000, seed=0):
    e = np.asarray(efeitos, float)
    rng = np.random.default_rng(seed)
    m = [e[rng.integers(0, len(e), len(e))].mean() for _ in range(n_boot)]
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def _permutacao_grupos(tratados, controles, max_exato: int = 20000, n_sim: int = 20000, seed: int = 0):
    """Teste de permutação dos rótulos de grupo para a diferença de médias (bilateral)."""
    t, c = np.asarray(tratados, float), np.asarray(controles, float)
    todos = np.concatenate([t, c])
    nt, n = len(t), len(t) + len(c)
    obs = abs(t.mean() - c.mean())
    if math.comb(n, nt) <= max_exato:
        cont = tot = 0
        for idx in itertools.combinations(range(n), nt):
            mask = np.zeros(n, bool)
            mask[list(idx)] = True
            tot += 1
            if abs(todos[mask].mean() - todos[~mask].mean()) >= obs - 1e-12:
                cont += 1
        return cont / tot
    rng = np.random.default_rng(seed)
    cont = 0
    for _ in range(n_sim):
        perm = rng.permutation(todos)
        if abs(perm[:nt].mean() - perm[nt:].mean()) >= obs - 1e-12:
            cont += 1
    return (cont + 1) / (n_sim + 1)


def _ic_boot_diferenca(tratados, controles, n_boot=5000, seed=0):
    t, c = np.asarray(tratados, float), np.asarray(controles, float)
    rng = np.random.default_rng(seed)
    d = [t[rng.integers(0, len(t), len(t))].mean() - c[rng.integers(0, len(c), len(c))].mean() for _ in range(n_boot)]
    return float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))


def _agrupar(dados):
    """{grupo: {organoide: {condicao: valor}}}; um organoide pertence a um só grupo."""
    por = {g: defaultdict(dict) for g in GRUPOS}
    grupo_de = {}
    for d in dados:
        g = d.get("grupo") or "tratado"
        if g not in GRUPOS:
            raise ValueError(f"grupo deve ser um de {GRUPOS}, e não {g!r}")
        o = d["organoide"]
        if grupo_de.setdefault(o, g) != g:
            raise ValueError(f"o organoide {o!r} aparece em dois grupos")
        por[g][o][d["condicao"]] = float(d["valor"])
    return por


def analisar_bloqueio(dados, referencia="veiculo", condicoes=("AMPA", "NMDA", "AMPA+NMDA"),
                      chance: float | None = None, tol_lavagem: float = LIMIARES_PROVISORIOS["tol_lavagem"],
                      margem_ttx: float = LIMIARES_PROVISORIOS["margem_ttx_acaso"], escala_lavagem: str = "absoluta"):
    """`dados`: dicts com organoide, condicao, valor (ex.: acurácia do decodificador) e, opcionalmente,
    grupo ("tratado", o padrão, ou "controle": organoides que receberam só veículo).

    Para cada condição, o resultado traz os efeitos por organoide TRATADO (condição - referência).
    Havendo controles, traz também `controle` (a deriva da mesma janela nos organoides só com veículo)
    e `efeito_liquido` (média dos tratados menos média dos controles, com IC bootstrap e permutação
    dos rótulos de grupo). Sem controles, `avisos` registra que a deriva não foi separada.
    `n_organoides` conta os tratados; `n_controles`, os controles.

    Lavagem: com escala_lavagem="absoluta", recupera se |lavagem - basal| <= tol_lavagem NA
    UNIDADE de `valor` (0,10 = 10 pontos percentuais de acurácia, e não 10%); com "relativa",
    se |lavagem - basal| / basal <= tol_lavagem. Aplicada aos controles, mostra quanto da "falta de
    recuperação" é deriva e não efeito do fármaco (`fracao_recuperacao_lavagem_controle`).
    TTX aqui é um critério de DESEMPENHO (acurácia sob TTX <= acaso + margem), distinto do
    critério de ATIVIDADE de `qualificar_organoide` (redução de spikes >= 90%)."""
    if escala_lavagem not in ("absoluta", "relativa"):
        raise ValueError("escala_lavagem deve ser 'absoluta' ou 'relativa'")
    grupos = _agrupar(dados)
    por, ctrl = grupos["tratado"], grupos["controle"]
    res = {"n_organoides": len(por), "n_controles": len(ctrl), "avisos": []}
    if not ctrl:
        res["avisos"].append("sem organoides-controle de veículo (grupo='controle'): a deriva temporal "
                             "não é separada do efeito farmacológico")
    for cond in condicoes:
        ef = {o: v[cond] - v[referencia] for o, v in por.items() if cond in v and referencia in v}
        e = list(ef.values())
        if not e:
            res["avisos"].append(f"sem dados para {cond}")
            continue
        res[cond] = {
            "n": len(e), "media_efeito": float(np.mean(e)),
            "ic95_bootstrap": _ic_boot(e) if len(e) >= 5 else None,
            "p_permutacao": _permutacao_sinais(e),
            "efeitos_por_organoide": ef,
        }
        if len(e) < 5:
            res["avisos"].append(f"{cond}: n < 5, IC não calculado; resultado apenas descritivo")
        if ctrl:
            efc = {o: v[cond] - v[referencia] for o, v in ctrl.items() if cond in v and referencia in v}
            ec = list(efc.values())
            if not ec:
                res["avisos"].append(f"{cond}: nenhum controle de veículo com a janela e a referência")
                continue
            res[cond]["controle"] = {"n": len(ec), "media_deriva": float(np.mean(ec)), "efeitos_por_organoide": efc}
            ok_ic = len(e) >= 5 and len(ec) >= 5
            res[cond]["efeito_liquido"] = {
                "diferenca_tratado_menos_controle": float(np.mean(e) - np.mean(ec)),
                "ic95_bootstrap": _ic_boot_diferenca(e, ec) if ok_ic else None,
                "p_permutacao": _permutacao_grupos(e, ec),
            }
            if not ok_ic:
                res["avisos"].append(f"{cond}: n < 5 em tratados ou controles, IC do efeito líquido não calculado")

    def recuperou(lav, base):
        dif = abs(lav - base)
        return dif <= tol_lavagem if escala_lavagem == "absoluta" else dif / abs(base) <= tol_lavagem
    rec = [recuperou(v[l], v["basal"]) for v in por.values() for l in LAVAGENS if l in v and "basal" in v]
    if rec:
        res["fracao_recuperacao_lavagem"] = float(np.mean(rec))
        if np.mean(rec) < 1:
            res["avisos"].append("há organoides sem recuperação na lavagem: efeitos podem ser irreversíveis ou haver deriva")
    rec_c = [recuperou(v[l], v["basal"]) for v in ctrl.values() for l in LAVAGENS if l in v and "basal" in v]
    if rec_c:
        res["fracao_recuperacao_lavagem_controle"] = float(np.mean(rec_c))
        if np.mean(rec_c) < 1:
            res["avisos"].append("controles de veículo também não voltam ao basal nas janelas de lavagem: deriva temporal provável")
    if chance is not None:
        t = [v["TTX"] <= chance + margem_ttx for v in por.values() if "TTX" in v]
        if t:
            res["fracao_ttx_no_acaso"] = float(np.mean(t))
            if np.mean(t) < 1:
                res["avisos"].append("TTX não levou o desempenho ao nível do acaso em todos: suspeita de artefato")
    return res
