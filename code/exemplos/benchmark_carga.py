"""Benchmark observacional de carga computacional (seção 4.4 do artigo).

Mede o tempo de execução de rotinas do pacote sbi4sem e de dois processos completos
(a suíte de testes e a demonstração), sobre dados sintéticos. É um estudo observacional:
registra medidas de execução, sem intervir em pessoas, tecidos ou dados reais. Os tempos
dependem do equipamento; o JSON de saída registra o ambiente em que foram tomados.

    python exemplos/benchmark_carga.py --saida resultado.json
    python exemplos/benchmark_carga.py --sem-processos

Requer numpy e scipy (requirements.txt). A suíte roda com PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
para medir apenas os testes do projeto, sem plugins externos do pytest.
"""
import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version

import numpy as np

CODIGO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, CODIGO)

from sbi4sem import analise, bloqueio, esteira, sintetico  # noqa: E402
from sbi4sem.snn import RedeSNN, gerar_conjunto, gerar_padroes  # noqa: E402


def medir(fn, repeticoes):
    """Mediana, mínimo e máximo de `repeticoes` execuções de `fn`."""
    tempos = []
    for _ in range(repeticoes):
        t0 = time.perf_counter()
        fn()
        tempos.append(time.perf_counter() - t0)
    return {"mediana_s": round(statistics.median(tempos), 4), "min_s": round(min(tempos), 4),
            "max_s": round(max(tempos), 4), "repeticoes": repeticoes}


def processo(comando, env):
    """Tempo de parede de um processo completo, com código de saída e última linha impressa."""
    t0 = time.perf_counter()
    r = subprocess.run(comando, cwd=CODIGO, env=env, capture_output=True, text=True)
    linhas = r.stdout.strip().splitlines()
    return {"tempo_parede_s": round(time.perf_counter() - t0, 2), "codigo_saida": r.returncode,
            "ultima_linha": linhas[-1] if linhas else ""}


def modelo_cpu():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("model name"):
                    return linha.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconhecido"


def versao(pacote):
    try:
        return version(pacote)
    except PackageNotFoundError:
        return "não instalado"


def rotinas():
    m = {}
    rede = RedeSNN(seed=0)
    padroes = gerar_padroes(3, seed=0)
    m["snn_uma_tentativa"] = medir(lambda: rede.simular(padroes[0]), 5)
    m["snn_sessao_36_tentativas"] = medir(lambda: gerar_conjunto(rede, padroes, 12), 3)
    estudantes = sintetico.estudantes(200, efeito_A=0.3, seed=1)  # 600 estudantes, 3 braços
    m["ancova_600_estudantes"] = medir(lambda: analise.analisar_piloto(estudantes), 5)
    rng = np.random.default_rng(0)
    linhas = []
    for grupo, n in (("tratado", 6), ("controle", 5)):
        for o in range(n):
            for c in bloqueio.CONDICOES:
                linhas.append({"organoide": f"{grupo[0]}{o}", "grupo": grupo, "condicao": c,
                               "valor": float(0.8 + rng.normal(0, 0.03))})
    m["bloqueio_11_organoides"] = medir(lambda: bloqueio.analisar_bloqueio(linhas, chance=1 / 3), 5)
    e15 = list(rng.normal(0, 1, 15))
    m["permutacao_sinais_n15_exata"] = medir(lambda: bloqueio._permutacao_sinais(e15), 5)
    t8, c8 = list(rng.normal(0, 1, 8)), list(rng.normal(0, 1, 8))
    m["permutacao_grupos_16_exata"] = medir(lambda: bloqueio._permutacao_grupos(t8, c8), 3)
    t12, c12 = list(rng.normal(0, 1, 12)), list(rng.normal(0, 1, 12))
    m["permutacao_grupos_24_simulada"] = medir(lambda: bloqueio._permutacao_grupos(t12, c12), 3)
    rotulos = rng.integers(0, 3, 300).tolist()
    itens = [{"id": i, "org": i % 6} for i in range(300)]
    camadas = [esteira.CamadaTipada("tipada", lambda it: [0.6, 0.2, 0.2], [0, 1, 2]),
               esteira.CamadaRegraFixa("regra", lambda it: it["id"] % 3)]
    m["esteira_300_itens_2_camadas"] = medir(
        lambda: esteira.executar_esteira(itens, rotulos, camadas, [0, 1, 2],
                                         grupos=[i["org"] for i in itens], n_boot=2000), 3)
    return m


def main():
    ap = argparse.ArgumentParser(description="Benchmark observacional de carga computacional do sbi4sem.")
    ap.add_argument("--saida", help="arquivo JSON de saída (sem a opção, imprime na tela)")
    ap.add_argument("--sem-processos", action="store_true",
                    help="mede só as rotinas; não roda a suíte de testes nem a demonstração")
    a = ap.parse_args()
    res = {"ambiente": {"cpu": modelo_cpu(), "nucleos_logicos": os.cpu_count(),
                        "python": platform.python_version(), "numpy": versao("numpy"),
                        "scipy": versao("scipy"), "sistema": platform.platform()},
           "medidas": rotinas()}
    if not a.sem_processos:
        env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        res["medidas"]["suite_testes_processo"] = processo(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], env)
        res["medidas"]["demo_completo_processo"] = processo(
            [sys.executable, os.path.join("exemplos", "demo_completo.py")], env)
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if a.saida:
        with open(a.saida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
        print(f"resultado gravado em {a.saida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
