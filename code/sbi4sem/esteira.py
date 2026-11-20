"""Esteira de decisão (teste 3 da tarefa-padrão).

Itens passam por uma "esteira" e cada camada de decisão devolve, para cada item, um rótulo
(e, quando houver, probabilidades). Camadas comparadas no braço A:

  1. camada tipada e probabilística sem organoide (modelos do tipo "System One", como o Jev);
  2. regra fixa;
  3. o organoide como camada de decisão;
  4. o organoide sob bloqueio de AMPA e NMDA.

Este módulo NÃO chama nenhum serviço: `CamadaTipada` envolve qualquer função que devolva
probabilidades por rótulo. O adaptador do Jev deve ser escrito contra a documentação do
fabricante (não incluída aqui) e passado como `funcao`. Os números do fabricante não entram
como dado: latência e acurácia são medidas aqui, na mesma esteira e com os mesmos itens.

Métricas: acurácia (saída inválida conta como erro), IC por bootstrap (por conglomerado
quando `grupos` é dado: o ORGANOIDE, e não o item, é a unidade experimental), Brier, ECE,
taxa de saída inválida, latência (mediana e p95), curva risco-cobertura e ITR de Wolpaw
(com tempo de decisão por camada).

Calibração: `CamadaOrganoide` usa softmax sobre escores lineares do decodificador (não calibrados);
sua ECE e seu Brier não devem ser lidos como inferioridade frente a uma camada tipada calibrada.

Codificação da entrada: o item é o padrão de entrada definido pela esteira. Cada camada o recebe
na sua própria codificação (estimulação elétrica para o organoide; serialização no esquema tipado
para a camada tipada). A função de codificação de cada camada é parte do adaptador, deve carregar
a mesma informação do padrão e ser fixada e registrada no pré-registro, porque uma codificação mais
pobre ou mais rica para uma camada cria vantagem ou desvantagem artificial na comparação.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

import numpy as np


@dataclass
class Decisao:
    rotulo: Any
    probs: Optional[np.ndarray]  # na ordem do esquema; None se a camada não dá probabilidades
    latencia_ms: float
    valida: bool = True


class CamadaRegraFixa:
    """Regra determinística. Com `esquema`, rótulo fora dele é saída INVÁLIDA; exceção na regra
    também é registrada como inválida (mesmo critério de `CamadaTipada`)."""

    def __init__(self, nome: str, regra: Callable[[Any], Any], esquema: Optional[Sequence] = None):
        self.nome, self.regra = nome, regra
        self.esquema = None if esquema is None else list(esquema)

    def decidir(self, item) -> Decisao:
        t0 = time.perf_counter()
        try:
            r = self.regra(item)
            ok = self.esquema is None or r in self.esquema
        except Exception:
            r, ok = None, False
        return Decisao(r if ok else None, None, (time.perf_counter() - t0) * 1e3, ok)


class CamadaTipada:
    """Camada tipada e probabilística. `funcao(item)` devolve um mapa rótulo->prob. ou uma
    sequência de probabilidades na ordem de `esquema`. Saída fora do esquema, não finita,
    negativa ou que não soma 1 (tol. 1e-3) é registrada como INVÁLIDA."""

    def __init__(self, nome: str, funcao: Callable[[Any], Mapping | Sequence[float]], esquema: Sequence):
        self.nome, self.funcao, self.esquema = nome, funcao, list(esquema)

    def decidir(self, item) -> Decisao:
        t0 = time.perf_counter()
        try:
            bruto = self.funcao(item)
            if isinstance(bruto, Mapping):
                if not set(bruto) <= set(self.esquema):
                    raise ValueError("rótulo fora do esquema")
                p = np.array([float(bruto.get(k, 0.0)) for k in self.esquema])
            else:
                p = np.asarray(bruto, float)
                if p.shape != (len(self.esquema),):
                    raise ValueError("tamanho de saída incompatível com o esquema")
            if not np.all(np.isfinite(p)) or np.any(p < 0) or abs(p.sum() - 1) > 1e-3:
                raise ValueError("probabilidades inválidas")
            ok, rot = True, self.esquema[int(np.argmax(p))]
        except Exception:
            p, ok, rot = None, False, None
        return Decisao(rot, p, (time.perf_counter() - t0) * 1e3, ok)


class CamadaOrganoide:
    """Camada baseada em decodificador treinado sobre características de registros.

    `extrair(item)` devolve o vetor de características. Para registros reais, a latência
    da plataforma deve ser registrada à parte e passada em `latencia_externa_ms`.

    `esquema` (recomendado) é a lista de rótulos da esteira, na mesma ordem usada em
    `executar_esteira`. O decodificador devolve probabilidades na ordem de `classes_`, que só
    coincide com o esquema se todas as classes estiverem no treino e na mesma ordem; com
    `esquema`, as probabilidades são realinhadas (classe ausente no treino recebe 0) e o rótulo
    sai do esquema. Classe do decodificador fora do esquema levanta ValueError. Sem `esquema`,
    `executar_esteira` recusa a camada se o número de classes diferir do do esquema."""

    def __init__(self, nome: str, decodificador, extrair: Callable[[Any], Any] = lambda x: x,
                 latencia_externa_ms: Optional[Callable[[Any], float]] = None,
                 esquema: Optional[Sequence] = None):
        self.nome, self.dec, self.extrair, self.lat_ext = nome, decodificador, extrair, latencia_externa_ms
        self.esquema = None if esquema is None else list(esquema)

    def decidir(self, item) -> Decisao:
        t0 = time.perf_counter()
        x = np.asarray(self.extrair(item), float)[None, :]
        p = self.dec.predict_proba(x)[0]
        lat = (time.perf_counter() - t0) * 1e3
        if self.lat_ext is not None:
            lat = float(self.lat_ext(item))
        classes = list(self.dec.classes_)
        if self.esquema is None:
            return Decisao(classes[int(np.argmax(p))], p, lat)
        pos = {k: i for i, k in enumerate(self.esquema)}
        if not set(classes) <= set(pos):
            raise ValueError(f"classes do decodificador fora do esquema: {sorted(set(classes) - set(pos), key=str)}")
        alinhada = np.zeros(len(self.esquema))
        for c, pc in zip(classes, p):
            alinhada[pos[c]] = pc
        return Decisao(self.esquema[int(np.argmax(alinhada))], alinhada, lat)


def _ece(conf, acerto, n_bins=10):
    conf, acerto = np.asarray(conf), np.asarray(acerto, float)
    arestas = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    for lo, hi in zip(arestas[:-1], arestas[1:]):
        m = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs(acerto[m].mean() - conf[m].mean())
    return float(e)


def bootstrap_ic(valores, grupos=None, n_boot: int = 2000, seed: int = 0, nivel: float = 0.95,
                 min_grupos: int = 5):
    """IC percentil da média; reamostra por conglomerado se `grupos` for dado. Com menos de
    `min_grupos` conglomerados (o mesmo piso de `bloqueio`), devolve None: o IC seria subcoberto."""
    v = np.asarray(valores, float)
    rng = np.random.default_rng(seed)
    if grupos is None:
        medias = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n_boot)]
    else:
        g = np.asarray(grupos)
        ids = np.unique(g)
        if len(ids) < min_grupos:
            return None
        por = {k: v[g == k] for k in ids}
        medias = []
        for _ in range(n_boot):
            sel = rng.choice(ids, len(ids))
            medias.append(np.concatenate([por[k] for k in sel]).mean())
    a = (1 - nivel) / 2
    return float(np.quantile(medias, a)), float(np.quantile(medias, 1 - a))


def itr_wolpaw(acuracia: float, n_classes: int, t_decisao_s: float) -> float:
    """Taxa de transferência de informação (bits/min), fórmula de Wolpaw, usual em BCI.

    Supõe classes equiprováveis e erros distribuídos por igual entre as demais classes.
    Abaixo do acaso, devolve 0. `t_decisao_s` inclui o tempo de cada decisão."""
    P, N = float(acuracia), int(n_classes)
    if N < 2 or t_decisao_s <= 0:
        raise ValueError("n_classes >= 2 e t_decisao_s > 0")
    if P <= 1 / N:
        return 0.0
    bits = np.log2(N) + P * np.log2(P)
    if P < 1:
        bits += (1 - P) * np.log2((1 - P) / (N - 1))
    return float(bits * 60 / t_decisao_s)


def medir_reprodutibilidade(camada, itens, repeticoes: int = 5) -> dict:
    """Chama a camada `repeticoes` vezes por item. Uma camada probabilística (por exemplo,
    um serviço como o Jev) não é determinística no sentido estrito: com a versão do modelo
    fixada, mede-se a fração de itens com a mesma decisão em todas as chamadas e o desvio
    médio das probabilidades."""
    iguais, desvios = [], []
    for it in itens:
        ds = [camada.decidir(it) for _ in range(repeticoes)]
        iguais.append(len({(d.valida, d.rotulo) for d in ds}) == 1)
        ps = [d.probs for d in ds if d.valida and d.probs is not None]
        if len(ps) == repeticoes:
            desvios.append(float(np.mean(np.std(np.array(ps), axis=0))))
    return {"fracao_decisoes_identicas": float(np.mean(iguais)),
            "desvio_medio_probabilidades": float(np.mean(desvios)) if desvios else None}


def decisao_para_contrato(decisao: Decisao, item_id, camada: str, esquema, versao: str = "") -> dict:
    """Registro de saída no contrato JSON da esteira (ver docs/contrato_esteira.schema.json)."""
    return {
        "item_id": item_id, "camada": camada, "versao": versao,
        "valida": bool(decisao.valida),
        "rotulo": decisao.rotulo if decisao.valida else None,
        "probabilidades": (dict(zip([str(e) for e in esquema], [float(p) for p in decisao.probs]))
                           if decisao.valida and decisao.probs is not None else None),
        "latencia_ms": float(decisao.latencia_ms),
    }


def executar_esteira(itens, rotulos, camadas, esquema, grupos=None, n_boot: int = 2000, seed: int = 0,
                     t_decisao_s: float | Mapping[str, float] | None = None):
    """Passa os `itens` por cada camada e calcula as métricas comparativas.

    Com `t_decisao_s`, inclui o ITR (bits/min), comparável entre camadas e com o braço C.
    O tempo por decisão pode ser um número (o mesmo para todas as camadas) ou um mapa
    `{nome_da_camada: segundos}`. Como as camadas têm latências reais muito diferentes (por
    exemplo, regra fixa, serviço tipado e organoide), use o mapa para que o ITR reflita
    essa diferença; um valor único só é adequado se o ritmo da esteira for imposto de fora.
    Camada ausente do mapa levanta ValueError (não há tempo padrão silencioso)."""
    rotulos = list(rotulos)
    if isinstance(t_decisao_s, Mapping):
        faltam = [c.nome for c in camadas if c.nome not in t_decisao_s]
        if faltam:
            raise ValueError(f"t_decisao_s sem tempo para as camadas: {faltam}")
    resultados = {}
    for cam in camadas:
        dec = [cam.decidir(it) for it in itens]
        acerto = np.array([d.valida and d.rotulo == r for d, r in zip(dec, rotulos)], float)
        lat = np.array([d.latencia_ms for d in dec])
        res = {
            "n": len(dec),
            "acuracia": float(acerto.mean()),
            "ic95_acuracia": bootstrap_ic(acerto, grupos, n_boot, seed),
            "taxa_invalida": float(np.mean([not d.valida for d in dec])),
            "latencia_mediana_ms": float(np.median(lat)),
            "latencia_p95_ms": float(np.quantile(lat, 0.95)),
        }
        if t_decisao_s is not None:
            t_cam = t_decisao_s[cam.nome] if isinstance(t_decisao_s, Mapping) else t_decisao_s
            res["t_decisao_s"] = float(t_cam)
            res["itr_bits_min"] = itr_wolpaw(res["acuracia"], len(esquema), t_cam)
        com_p = [i for i, d in enumerate(dec) if d.valida and d.probs is not None]
        res["n_com_probabilidades"] = len(com_p)  # Brier, ECE e risco-cobertura usam só estes itens
        if com_p:
            P = np.array([dec[i].probs for i in com_p])
            if P.shape[1] != len(esquema):
                raise ValueError(f"camada '{cam.nome}': {P.shape[1]} probabilidades por item, mas o esquema tem "
                                 f"{len(esquema)} rótulos (para CamadaOrganoide, passe `esquema=`)")
            conf = P.max(1)
            ac = acerto[com_p]
            Y = np.array([[1.0 if esquema[j] == rotulos[i] else 0.0 for j in range(len(esquema))] for i in com_p])
            res["brier"] = float(np.mean(np.sum((P - Y) ** 2, axis=1)))
            res["ece"] = _ece(conf, ac)
            ordem = np.argsort(-conf)
            cumul = np.cumsum(ac[ordem]) / np.arange(1, len(ordem) + 1)
            ks = sorted({max(1, int(round(f * len(ordem)))) for f in (0.2, 0.4, 0.6, 0.8, 1.0)})
            res["risco_cobertura"] = [(k / len(ordem), float(cumul[k - 1])) for k in ks]
        resultados[cam.nome] = res
    return resultados
