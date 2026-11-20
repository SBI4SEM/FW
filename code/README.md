# Pacote `sbi4sem`

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

Ferramentas do piloto. Dependências: `numpy` e `scipy` (testes: `pytest`). Python 3.10 ou superior.

```bash
pip install -r requirements.txt
python -m pytest
```

## Módulos

| Módulo | Função | Artigo |
|---|---|---|
| `amostra` | Estudantes por braço; reproduz a Tabela 4 (`tabela4()`) | 5.5 |
| `randomizacao` | Sequência estratificada em blocos permutados, carimbo SHA-256, CLI | 5.3 |
| `analise` | ANCOVA (T1 ~ braço + T0 + estratos), g de Hedges com IC, regra de decisão (H1 / desfavorável à SBI / H3 / inconclusivo), fluxo e atrito, efeito de teto. **Núcleo parcial** (ver abaixo) | 5.1, 5.5, 5.6 |
| `decodificador` | Decodificador linear e gerador de padrões, validação por blocos temporais com `gap`, NRMSE, acaso por permutação circular, demonstração de vazamento | Teste 2 |
| `bloqueio` | Critérios de qualificação de organoides; análise por organoide do bloqueio de AMPA, NMDA e conjunto (efeitos, bootstrap, permutação, verificações de lavagem e TTX); com organoides-controle só com veículo (`grupo = "controle"`), deriva da janela e efeito líquido tratados − controles | Teste 1 |
| `esteira` | Camadas de decisão (tipada, regra fixa, organoide), contrato JSON, acurácia com bootstrap por conglomerado, Brier, ECE, saída inválida, latência, risco-cobertura, ITR de Wolpaw (tempo de decisão por camada), reprodutibilidade entre chamadas; `CamadaOrganoide(esquema=...)` alinha as probabilidades ao esquema | Teste 3 |
| `snn` | Rede LIF com AMPA, NMDA e GABA para o braço B (**didática**); TTX modelado como bloqueio de canais de Na⁺ (`bloqueio_na`), distinto do bloqueio de AMPA+NMDA | Braço B |
| `sintetico`, `bateria` | Geradores de dados sintéticos e da bateria JSON | testes |

## Escopo: núcleo parcial

O pacote implementa a análise do **desfecho primário** (seção 5.5) e as ferramentas dos Testes 1 a 3. **Não** implementa, e o pré-registro deve especificar antes de codificar: a imputação para a análise por intenção de tratar (`analise.ancova` recusa `t1` ausente; só há `completos()`, que é sensibilidade, e `fluxo()`); a análise de H2 (rubrica RED na tarefa aberta; contraste A–B contra A–C); a moderação pela preferência de tema; e a análise por protocolo como sensibilidade completa.

## Exemplos

```python
from sbi4sem import analise
r = analise.analisar_piloto(dados)           # dados: dicts com braco, estrato, t0, t1
res, veredito = r["primario_A_vs_BC"]
print(res.g_hedges, res.ic_g, veredito)
```

```python
from sbi4sem import esteira
camada = esteira.CamadaTipada("jev", minha_funcao, esquema=["a", "b", "c"])   # minha_funcao: adaptador do fabricante
```

`python exemplos/demo_completo.py` executa o fluxo inteiro. Em `CamadaTipada`, mapas rótulo→probabilidade com **chaves do mesmo tipo do esquema** (um JSON converte chaves inteiras em texto: converta de volta ou passe uma lista).

`python exemplos/benchmark_carga.py --saida resultado.json` mede o tempo de execução das rotinas, da suíte de testes e da demonstração (estudo observacional da seção 4.4 do artigo). Os tempos dependem do equipamento; o JSON registra o ambiente.

## Testes (103)

| Arquivo | O que cobre |
|---|---|
| `tests/test_framework.py` | Núcleo: Tabela 4, randomização, ANCOVA e decisão (inclusive efeito negativo e as quatro categorias), vazamento, esteira (ITR por camada; alinhamento das classes do organoide ao esquema), bloqueio (efeito líquido contra controles de veículo), SNN (TTX como bloqueio de Na⁺, e não de AMPA+NMDA) |
| `tests/test_bateria_sintetica.py` | Integridade e regeneração da bateria JSON; 12 cenários de estudantes (efeito nulo, conhecido, negativo, atrito, teto, estratos); simulações (cobertura do IC, erro tipo I, poder da regra); randomização armazenada; séries com e sem sinal; 10 cenários de bloqueio (efeito, n pequeno e grande, falha de TTX, falha de lavagem, condição ausente; 3 com controles de veículo e deriva); 4 camadas da esteira (calibrada, superconfiante, subconfiante, com 5 tipos de saída inválida); contagens da rede simulada; qualificação de organoides, bloqueio conjunto, NRMSE, permutação circular, ITR (inclusive por camada), reprodutibilidade e contrato JSON (v2) |

Cobertura de linhas medida com `coverage`: **99%** (as linhas não cobertas são os blocos `if __name__ == "__main__"`).

Os testes verificam **o software**, e não a ciência: uma propriedade verificada em dados sintéticos não valida nada sobre organoides ou estudantes.

## Regenerar a bateria

```bash
python exemplos/gerar_dados_sinteticos.py --saida ../dados_sinteticos
```

## Licença

MIT (arquivo `LICENSE` na raiz do repositório).
