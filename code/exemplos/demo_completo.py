"""Demonstração de ponta a ponta, com DADOS SINTÉTICOS e rede simulada (didática).

Executa: Tabela 4, randomização, ANCOVA de um piloto fictício, vazamento na validação,
tarefa-padrão no silício (bloqueio de AMPA/NMDA com controles de veículo, TTX como bloqueio de
Na+, decodificador e esteira de decisão). Leva cerca de um minuto.

    cd FW/code && python exemplos/demo_completo.py

Os números impressos NÃO são resultados do estudo: só mostram que o fluxo funciona.
Na camada tipada, a função `camada_tipada_ficticia` é um SUBSTITUTO sem relação com o Jev:
troque-a por um adaptador escrito contra a documentação do fabricante.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sbi4sem import amostra, analise, bloqueio, decodificador as dec, esteira, randomizacao, sintetico
from sbi4sem.snn import RedeSNN, gerar_padroes, gerar_conjunto

K = 3
ESQUEMA = list(range(K))


def secao(t):
    print(f"\n=== {t} ===")


secao("Tabela 4 (estudantes por braço)")
for linha in amostra.tabela4():
    print(linha)

secao("Randomização estratificada (semente de exemplo)")
seq = randomizacao.gerar_sequencia({"EscolaX-1": 12, "EscolaX-2": 12}, seed=2026)
print("carimbo:", randomizacao.carimbo(seq)[:16], "...  primeiros do estrato 1:", seq["EscolaX-1"][:6])

secao("ANCOVA em piloto fictício (15 por braço, efeito verdadeiro = 0)")
r = analise.analisar_piloto(sintetico.estudantes(15, efeito_A=0.0, seed=5))
for nome, (res, veredito) in r.items():
    print(f"{nome}: g = {res.g_hedges:+.2f} IC95% [{res.ic_g[0]:+.2f}; {res.ic_g[1]:+.2f}] -> {veredito}")

secao("Vazamento: validação aleatória x por blocos (rótulos sem relação com o sinal)")
X, y = sintetico.serie_autocorrelacionada()
print(dec.comparar_validacoes(X, y, n_blocos=5, gap=60), f"(acaso = {1/3:.2f})")

secao("Tarefa-padrão no silício (rede LIF com AMPA/NMDA; 6 'organoides' tratados + 5 controles de veículo = sementes)")
padroes = gerar_padroes(K, seed=0)
N_POR_CLASSE, GRAU = 12, 0.5
# Sequência do protocolo: ... -> AMPA+NMDA -> lavagem3 -> TTX (terminal). Valores: (bloqueio_ampa, bloqueio_nmda, bloqueio_na).
# TTX bloqueia canais de Na+ dependentes de voltagem (nenhum spike, sinapses intactas); NÃO é bloqueio de AMPA+NMDA.
cond_bloqueio = {
    "basal": (0, 0, 0), "veiculo": (0, 0, 0), "AMPA": (GRAU, 0, 0), "lavagem1": (0, 0, 0),
    "NMDA": (0, GRAU, 0), "lavagem2": (0, 0, 0), "AMPA+NMDA": (GRAU, GRAU, 0), "lavagem3": (0, 0, 0),
    "TTX": (0, 0, 1.0),
}
# Controles recebem só veículo; `condicao` rotula a janela correspondente (aqui a rede é estacionária: deriva ~ 0).
JANELAS_CONTROLE = ("basal", "veiculo", "AMPA", "NMDA", "AMPA+NMDA")
dados_bloqueio, itens_por_org = [], {}
for o in range(6):
    rede = RedeSNN(seed=100 + o)
    Xtr, ytr = gerar_conjunto(rede, padroes, N_POR_CLASSE, seed=o)
    modelo = dec.DecodificadorLinear(lam=50.0).fit(Xtr, ytr)
    sessoes = {}
    for i, (cond, (ba, bn, bna)) in enumerate(cond_bloqueio.items()):
        Xc, yc = gerar_conjunto(rede, padroes, N_POR_CLASSE, bloqueio_ampa=ba, bloqueio_nmda=bn, bloqueio_na=bna, seed=1000 + 10 * o + i)
        sessoes[cond] = (Xc, yc)
        dados_bloqueio.append({"organoide": f"o{o}", "grupo": "tratado", "condicao": cond, "valor": float(np.mean(modelo.predict(Xc) == yc))})
    itens_por_org[o] = (modelo, sessoes, rede)
for o in range(5):
    rede = RedeSNN(seed=500 + o)
    Xtr, ytr = gerar_conjunto(rede, padroes, N_POR_CLASSE, seed=50 + o)
    modelo = dec.DecodificadorLinear(lam=50.0).fit(Xtr, ytr)
    for i, cond in enumerate(JANELAS_CONTROLE):
        Xc, yc = gerar_conjunto(rede, padroes, N_POR_CLASSE, seed=2000 + 10 * o + i)  # só veículo: sem bloqueio
        dados_bloqueio.append({"organoide": f"c{o}", "grupo": "controle", "condicao": cond, "valor": float(np.mean(modelo.predict(Xc) == yc))})

res = bloqueio.analisar_bloqueio(dados_bloqueio, chance=1 / K)
for c in ("AMPA", "NMDA", "AMPA+NMDA"):
    b, liq = res[c], res[c]["efeito_liquido"]
    ic = "n/d" if liq["ic95_bootstrap"] is None else f"[{liq['ic95_bootstrap'][0]:+.2f}; {liq['ic95_bootstrap'][1]:+.2f}]"
    print(f"{c:9s}: só tratados {b['media_efeito']:+.2f} | deriva dos controles {b['controle']['media_deriva']:+.2f} | "
          f"efeito líquido {liq['diferenca_tratado_menos_controle']:+.2f}, IC95% bootstrap {ic}, p permutação = {liq['p_permutacao']:.3f}")
print("recuperação na lavagem:", res["fracao_recuperacao_lavagem"], "| TTX no acaso:", res["fracao_ttx_no_acaso"])
for a in res["avisos"]:
    print("AVISO:", a)

print("TTX x bloqueio total de AMPA+NMDA (mesma rede): ambos silenciam os spikes, por mecanismos diferentes")
_rede = RedeSNN(seed=100)
for nome, kw in (("basal", {}), ("AMPA+NMDA total", dict(bloqueio_ampa=1.0, bloqueio_nmda=1.0)), ("TTX (canais de Na+)", dict(bloqueio_na=1.0))):
    n_spk = int(_rede.simular(padroes[0], **kw).sum())
    print(f"   {nome:20s} spikes = {n_spk:4d} | potencial de membrana médio = {_rede.vm_medio_exc:6.1f} mV")

secao("Esteira de decisão: camada tipada x regra fixa x organoide x organoide bloqueado")


def camada_tipada_ficticia(item):  # SUBSTITUTO: probabilidades pela proximidade ao padrão de entrada
    d = np.array([np.linalg.norm(item["entrada"] - p) for p in padroes])
    s = np.exp(-d / 20.0)
    return s / s.sum()


def regra_fixa(item):  # regra arbitrária de exemplo: grupo de neurônios com mais disparos
    return int(np.argmax([g.sum() for g in np.array_split(item["resposta"][: 80], K)]))


def montar(condicao):
    itens, rot, grupos = [], [], []
    for o, (_, sess, _) in itens_por_org.items():
        Xc, yc = sess[condicao]
        for x, c in zip(Xc, yc):
            itens.append({"entrada": padroes[c], "resposta": x, "org": o}); rot.append(int(c)); grupos.append(o)
    return itens, rot, grupos


for cond in ("basal", "AMPA+NMDA"):
    itens, rot, grupos = montar(cond)
    por_org = {o: itens_por_org[o][0] for o in itens_por_org}

    class CamadaOrg(esteira.CamadaOrganoide):
        def decidir(self, item):
            self.dec = por_org[item["org"]]
            return super().decidir(item)

    camadas = [
        esteira.CamadaTipada("tipada(fictícia)", camada_tipada_ficticia, ESQUEMA),
        esteira.CamadaRegraFixa("regra fixa", regra_fixa),
        CamadaOrg("organoide", por_org[0], extrair=lambda it: it["resposta"], esquema=ESQUEMA),
    ]
    out = esteira.executar_esteira(itens, rot, camadas, ESQUEMA, grupos=grupos, n_boot=500)
    print(f"-- itens na condição: {cond}")
    for nome, m in out.items():
        extra = f", ECE {m['ece']:.2f}" if "ece" in m else ""
        print(f"   {nome:17s} acurácia {m['acuracia']:.2f} IC95% [{m['ic95_acuracia'][0]:.2f}; {m['ic95_acuracia'][1]:.2f}]"
              f", inválidas {m['taxa_invalida']:.0%}, latência mediana {m['latencia_mediana_ms']:.3f} ms{extra}")
print("\n(Dados sintéticos: nada acima é resultado empírico.)")
