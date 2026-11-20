# Modelo de pré-registro do piloto

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

Preencha e registre em plataforma pública **antes da randomização**. Guarde o carimbo (hash) deste documento. Itens entre colchetes são decisões a tomar; os valores de partida vêm do artigo e devem ser confirmados.

## 1. Identificação
- Título, equipe, instituições, datas, número do CEP/CONEP: [ ]
- Versão do protocolo e data de congelamento: [ ]

## 2. Pergunta e hipóteses (artigo, seção 5.1)
- **Pergunta:** em estudantes de ensino médio com indicadores de alto potencial, um enriquecimento SEM (Tipos I a III) centrado em SBI produz maior ganho de raciocínio científico do que um enriquecimento de mesma carga horária e estrutura centrado em outro tema de fronteira?
- **H1 (primária):** o ganho pré→pós é maior no braço SBI do que nos comparadores agrupados.
- **H2 (secundária, exploratória):** a vantagem da SBI, se existir, concentra-se no raciocínio sob variabilidade e incerteza, frente ao comparador em silício.
- **H3:** não há diferença apreciável entre os temas.

## 3. Critério de decisão
- **Escala da decisão:** g de Hedges calculado sobre a diferença ajustada pela ANCOVA (contraste A contra B+C), com IC de 95% (`analise.ancova`).
- Menor efeito de interesse prático: g = [0,30 como valor de partida; a confirmar e justificar]
- **H1 sustentada** se o limite inferior do IC de 95% de g ficar acima de zero **e** a estimativa de g alcançar o limiar.
- **H3 compatível** se o IC de 95% de g estiver inteiramente entre −limiar e +limiar.
- **Desfavorável à SBI** se o limite superior do IC de 95% de g ficar abaixo de zero **e** a estimativa de g chegar a −limiar (simétrica de H1). Um efeito negativo claro não é "inconclusivo".
- A diferença bruta em pontos do teste **nunca** é comparada diretamente com o limiar padronizado.
- **Planejamento × decisão:** o d = 0,30 da Tabela 4 (`amostra.py`) é parâmetro de **planejamento amostral**; a regra de decisão usa g. Se os valores forem iguais, isso é uma escolha a justificar, não uma identidade.
- Caso contrário: inconclusivo (o desfecho mais provável num piloto), inclusive quando o IC exclui zero, mas a estimativa não alcança o limiar. As quatro categorias são avaliadas nesta ordem: H1, desfavorável, H3, inconclusivo. Implementação: `sbi4sem.analise.decidir`.

## 4. Desenho, participantes e alocação (seção 5.3)
- Piloto randomizado de grupos paralelos; braços A (SBI), B (IA inspirada no cérebro, silício), C (BCI com EEG aberto); razão 1:1:1.
- Critérios de inclusão, mais de um indicador de alto potencial, sem ponto de corte único: [ ]
- Estratos (escola × série): [ ]
- Sequência: gerada e guardada por pessoa externa ao ensino; **carimbo SHA-256 registrado aqui:** [ ]
- Cegamento: avaliadores cegos ao braço e ao momento.
- Análise por intenção de tratar; contaminação e atrito registrados.

## 5. Desfechos e instrumentos (seção 5.4)
- **Primário:** variação pré→pós no escore total de teste de raciocínio científico independente de tema [candidato: teste de Lawson, após tradução, adaptação transcultural e verificação de confiabilidade]; escala e escore máximo: [ ]
- **Secundário 1:** tarefa aberta em cenário novo, com rubrica adaptada; limiar de concordância entre avaliadores: [ ]
- **Secundário 2 (opcional):** Scientific Reasoning Scale, após adaptação: [ ]
- **Engajamento e interesse** (explicação concorrente): escala [ ]
- Momentos: T0, T1 (fim do Tipo III), T2 (seguimento, fora dos 12 meses).

## 6. Efeito de teto
- Margem relativa ao máximo e proporção em T0 que aciona a troca do desfecho primário para a tarefa aberta: [ ] (usar `analise.proporcao_teto`).

## 7. Análise (seção 5.5)
- ANCOVA do escore em T1, com T0 e estratos como covariáveis; A contra B+C agrupados; A–B e A–C exploratórios (`analise.analisar_piloto`).
- Relato: diferenças ajustadas e g de Hedges com IC de 95%; p não é regra de decisão.
- Dados faltantes: ITT com [método de imputação pré-especificado]; casos completos como sensibilidade (`analise.completos`).
- **Escopo do pacote de código.** `analise.py` implementa só o desfecho primário (ANCOVA, g de Hedges, regra de decisão, fluxo e atrito, casos completos). **Ainda não estão codificados e devem ser especificados aqui:** (a) a imputação para a análise por intenção de tratar; (b) a análise de H2 (rubrica RED na tarefa aberta e contraste A–B contra A–C); (c) a moderação pela preferência de tema; (d) a análise por protocolo como sensibilidade completa.
- Tamanho amostral: por viabilidade e precisão, não por potência. Valores de referência: `amostra.tabela4()`. Correlação pré-pós suposta (0,6): [substituir pelo dado do piloto].

## 8. Tarefa-padrão do braço A (ver `Protocolo_AMPA_NMDA.md`)
- Condições, ordem contrabalançada, critérios de qualidade (tolerância de lavagem, margem de TTX): [ ]
- Janelas temporais, `gap`, características, `lam` do decodificador: [ ]
- Camadas da esteira, regra fixa, versão do modelo da camada tipada, limiar de confiança: [ ]
- Hipótese H-T1 (direção e magnitude, com a fonte): [ ]
- Organoides-controle só com veículo: número, janelas pareadas aos tratados e comparação tratados × controles (efeito líquido; `bloqueio.analisar_bloqueio` com `grupo`): [ ]
- Origem do tecido: hiPSC humana (`origem_do_tecido.md`); consentimento do doador, comitê de origem e biossegurança, por escrito: [ ]

### 8.1 Critérios de qualificação do Teste 1 (fixar todos)

| Critério | Medida e fórmula | Limiar provisório | Limiar final | Se ausente |
|---|---|---|---|---|
| (i) Atividade | Cruzamentos de limiar (5 × RMS) em unidades-alvo | ≥ 10 | [ ] | Reprova |
| (ii) Veículo | \|taxa no veículo − taxa em B0\| / taxa em B0 | ≤ 20% | [ ] | Reprova e invalida |
| (iii) Lavagem | \|lavagem − basal\|, absoluta na unidade da métrica ou relativa: [escolher] | 0,10 absoluta | [ ] | Reprova e invalida |
| (iv) TTX, atividade | 1 − spikes sob TTX / spikes em B0 | ≥ 90% | [ ] | "Não avaliado"; obrigatório? [sim/não] |
| TTX, desempenho | Acurácia do decodificador sob TTX ≤ acaso + margem | margem 0,05 | [ ] | Não avaliado |

## 9. Ameaças e contramedidas
Ver `ameacas_validade.md`; registrar as contramedidas adotadas e os limiares.

## 10. Ética e governança
Ver `governanca_e_viabilidade.md`. CEP/CONEP, TCLE, TALE, LGPD, parceiro habilitado, com consentimento do doador, comitê de origem e biossegurança de nível 2 (tecido de hiPSC humana).

## 11. Relato
CONSORT para pilotos (Eldridge et al., 2016); lista de desvios; dados e código arquivados.
