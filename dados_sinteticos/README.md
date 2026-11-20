# Bateria de dados sintéticos

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

> **São dados sintéticos.** Foram gerados por simulação para testar o software. Não são dados de estudantes nem de organoides e **não constituem evidência** sobre nenhum dos dois. Cada arquivo repete esse aviso em `meta.aviso`.

Formato de todos os arquivos: `{"meta": {...}, "dados": ...}`. Floats arredondados a 6 casas. `manifesto.json` lista o tamanho e o SHA-256 de cada arquivo. Gerados por `code/exemplos/gerar_dados_sinteticos.py` (sementes fixas), e o teste de regeneração confere os bytes.

| Arquivo | Conteúdo | Usado para testar |
|---|---|---|
| `estudantes_cenarios.json` | 12 cenários de piloto, com `braco`, `estrato`, `t0`, `t1` e o efeito verdadeiro conhecido: efeito nulo (n = 15 e 200), pequeno (d ≈ 0,3), moderado, grande e negativo; correlação pré-pós baixa e alta; 1 e 5 estratos; atrito diferencial (`t1 = null`); efeito de teto | ANCOVA, regra de decisão, fluxo e atrito, teto |
| `randomizacao_casos.json` | 4 configurações de estratos, com semente, sequência e carimbo SHA-256 | Reprodutibilidade e balanço da alocação |
| `series_vazamento.json` | Duas séries autocorrelacionadas (300 × 30): sem sinal (acurácia real = acaso) e com sinal | Vazamento na validação aleatória × blocos temporais |
| `padroes_temporais.json` | Características e padrões-alvo (240 × 30 → 240 × 16) | Gerador linear de padrões |
| `bloqueio_cenarios.json` | 10 tabelas por organoide e condição (basal, veículo, AMPA, NMDA, AMPA+NMDA, três lavagens, TTX): efeito forte, sem efeito, n = 3, n = 20, falha de TTX, falha de lavagem, condição ausente e 3 com organoides-controle só com veículo (`grupo = "controle"`): efeito real, só deriva (os tratados parecem ter efeito; o efeito líquido é ~0) e poucos controles; ordem contrabalançada | Análise do bloqueio |
| `qualificacao_organoides.json` | 10 casos para os critérios de qualificação (atividade, veículo, lavagem, TTX), com o veredito esperado | `bloqueio.qualificar_organoide` |
| `esteira_itens.json` | 300 itens com saídas de 4 camadas tipadas: calibrada, superconfiante, subconfiante e com 25% de saídas inválidas (5 tipos de defeito) | Esteira: acurácia, ECE, Brier, saídas inválidas |
| `snn_contagens.json` | Contagens de disparos de 2 organoides simulados em 4 condições (basal, AMPA, NMDA, AMPA+NMDA), 24 tentativas por sessão | Decodificação e efeito dos bloqueadores no silício |

## Como ler

```python
import json
with open("estudantes_cenarios.json", encoding="utf-8") as f:
    cenarios = {c["id"]: c for c in json.load(f)["dados"]}
dados = [e for e in cenarios["efeito_06_n60"]["estudantes"]]
```

## Limitações

- `snn_contagens.json` depende da aritmética de ponto flutuante da plataforma; a regeneração em outra máquina pode diferir nele (os demais arquivos são reproduzidos byte a byte nos testes).
- Os cenários têm efeitos, correlações e níveis de ruído **escolhidos pelos autores**; não representam a distribuição esperada em escolas.
- Chaves de mapa em JSON são sempre texto: em `esteira_itens.json`, os defeitos do tipo "rótulo fora do esquema" usam chaves como `"0"` e `"9"`.
