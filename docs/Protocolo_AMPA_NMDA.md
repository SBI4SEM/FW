# Protocolo-padrão: transmissão glutamatérgica (AMPA e NMDA) em organoides corticais conectados

**Versão 0.2 (rascunho para pré-registro).** Material complementar do artigo, seção 5.2.3. Esta versão segue o protocolo de trabalho dos autores (19/11/2026) e liga cada passo ao código de `code/sbi4sem/`.

> **Numeração.** O artigo chama os testes de (1), (2) e (3); o protocolo de trabalho os chamava de A, B e C. Aqui se usa 1, 2 e 3 para **não confundir com os braços A, B e C** do piloto.

## 0. Status e limites (leia primeiro)

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

- **Proposta de trabalho, sem validação experimental.** Não há dado eletrofisiológico neste repositório; o software foi testado só com dados sintéticos.
- O desenho parte de Robbins et al. (2026; ganho dependente de AMPA e NMDA, sem retenção após 45 min), Sono et al. (2026; decodificador linear que gera padrões temporais), Loeffler et al. (2026; controle de artefatos na decodificação) e Cai et al. (2026; organoide como camada de decisão; bioRxiv, sem revisão por pares; motiva o conceito, não valida este protocolo). **Robbins, Sono e Cai foram lidos só no resumo.**
- **Os estudantes nunca manipulam fármacos nem escolhem doses.** O parceiro executa a farmacologia; os estudantes planejam, analisam e interpretam.
- Concentrações, tempos de equilíbrio e de lavagem são **definidos e validados pelo parceiro**. Nenhum valor aqui é prescrição.

## 1. Plataformas: capacidades demonstradas e capacidades a contratar

| Plataforma | Capacidade demonstrada na fonte | Depende do parceiro | Etapa |
|---|---|---|---|
| CL-1 / CL API (Cortical Labs; Hogan et al., 2026) | Circuito fechado em Python, células humanas | Farmacologia, documentação de origem das células | Tipos II e III (programação e circuito fechado) |
| Plataforma de Elliott et al. (2023) | Estimulação elétrica e registro em MEA, organoides de camundongo | Farmacologia (ausente no artigo), circuito fechado | Teste 2 com estímulo; base do Teste 1 se houver farmacologia |
| Parceiro habilitado com farmacologia | A demonstrar | Bloqueadores, doses, documentação ética da origem (doador, comitê de origem, biossegurança) | Teste 1 (estágio 3 da trilha) |

A plataforma de cada etapa é definida com o parceiro e registrada no pré-registro.

### 1.1 O que a plataforma de Elliott et al. (2023) faz e não faz

Fonte: Elliott et al. (2023), *eNeuro*, DOI 10.1523/ENEURO.0308-23.2023 (texto completo conferido pelos autores em 20/11/2026).

- Organoides corticais de **camundongo** (células-tronco embrionárias), em MEA de alta densidade (MaxOne; só **1.024 eletrodos** lidos por vez; dados em HDF5). A taxa de amostragem não é informada no artigo.
- Estudantes projetam estimulação por uma API mínima (`stim`, `delay`, `next`; valores sugeridos: 150 mV e 200 µs por fase) e analisam *spikes* classificados (Kilosort 2, curadoria no Phy). Curso: 5 min de linha de base, 5 min de estimulação, 15 min de pós, com um organoide-teste e um de controle por grupo.
- **Não há farmacologia de receptores glutamatérgicos**, nem circuito fechado descrito. Os únicos fármacos do artigo foram aplicados pelo laboratório, na linha de microscopia.
- **Consequência:** o Teste 1 exige que o parceiro aplique bloqueadores, capacidade a solicitar e documentar (`governanca_e_viabilidade.md`), e documentação ética da origem do tecido (hiPSC humana: consentimento do doador, comitê de origem e biossegurança de nível 2; ver §1.2). Sem isso, vale a trilha em estágios (`trilha_em_estagios.md`).

### 1.2 Decisão sobre a origem do tecido

O braço A usa **hiPSC humana**, em nuvem (Cortical Cloud/CL1 ou FinalSpark). A plataforma de Elliott et al. (2023), de camundongo, é precedente educacional e fonte das hipóteses, não a plataforma do braço A. A escolha pesou o **preço do essencial na nuvem** (só a nuvem humana tem tarifa divulgada, cerca de US$ 300 por semana no CL1) e a **oportunidade conceitual** (testar em tecido humano hipóteses geradas em camundongo é pergunta aberta, como o Tipo III exige, e abre a neuroética de tecido humano). Fatos, fontes, ressalvas e condições de reversão: [`origem_do_tecido.md`](origem_do_tecido.md).

## 2. Hipóteses fisiológicas (pré-registráveis)

| # | Hipótese | Base |
|---|---|---|
| F1 | O bloqueio de AMPA (NBQX ou CNQX) reduz a taxa de disparo e a taxa de surtos de rede mais do que o bloqueio de NMDA (AP5) | AMPA medeia a transmissão excitatória rápida; NMDA é lento e dependente de voltagem |
| F2 | O bloqueio de NMDA encurta a duração dos surtos e os *spikes* tardios dentro deles, com menor efeito no disparo inicial | Cinética lenta do NMDA |
| F3 | O bloqueio conjunto abole os surtos; o TTX (controle positivo final) abole todos os *spikes* | Controle de método |
| F4 | A mudança de resposta evocada após estimulação tetânica depende de NMDA (some com AP5) e não persiste 45 min depois | Robbins et al. (2026), lido só no resumo |
| F5 | Todos os efeitos são reversíveis na lavagem | Controle de método |

F1, F2 e F4 são **hipóteses mecanísticas plausíveis, não achados**. Vêm de trabalhos em organoides de camundongo (Robbins et al., 2026); testá-las em hiPSC humana é extensão translacional (§1.2).

## 3. Teste 1: farmacologia AMPA e NMDA

**Unidade experimental: o organoide**, e não o neurônio, o eletrodo ou a janela (evitar pseudorreplicação). Análise por estatística-resumo por organoide (`bloqueio.analisar_bloqueio`) ou por modelo misto com o organoide como efeito aleatório.

### 3.1 Sequência por organoide

Cada janela usa o mesmo conjunto de eletrodos e as mesmas unidades classificadas, ordenadas em conjunto.

1. **Linha de base B0:** 15 min espontâneos + sonda de estimulação (§3.2).
2. **Veículo:** após equilíbrio de pelo menos 5 min (prática relatada em organoides), 10 min espontâneos + sonda.
3. **Bloqueador 1** (AMPA ou NMDA, ordem **contrabalançada** entre organoides; `bloqueio.ordem_contrabalancada`) + sonda. Lavagem + recuperação + sonda.
4. **Bloqueador 2** + sonda. Lavagem + recuperação + sonda.
5. **Bloqueio conjunto** (AMPA+NMDA) + sonda. Lavagem.
6. **Terminal e opcional: TTX** (controle positivo), ao fim, porque é difícil de reverter.

**Organoides-controle** recebem apenas o veículo, com os mesmos tempos (como no eNeuro: um teste, um controle). Nos dados, `grupo = "controle"` e `condicao` rotula a janela correspondente (o que o tratado equivalente receberia naquele instante).

**Concentrações:** não há faixa consensual. Um estudo em organoides humanos (*Communications Biology*, 2025, material suplementar, visto só em trecho de busca) relatou 40 µM de NBQX e AP5 em registro agudo e 20 µM em exposição de 2 h. O parceiro define e valida as doses.

### 3.2 Sonda de estimulação padrão (valores iniciais a pilotar)

- Pulso único bifásico (150 mV, 200 µs por fase), 1 Hz, 60 repetições, em até 3 locais.
- Estimulação tetânica (teste de F4), só na janela de bloqueador e no controle: trem de 100 Hz por 1 s, repetido 3 vezes com 20 s de intervalo. Sonda de pulso único antes, 5 min depois e 45 min depois.

### 3.3 Métricas padronizadas

- Taxa de disparo por unidade; taxa, duração e *spikes* por surto de rede (limiar de detecção de surto fixado no pré-registro).
- Probabilidade e latência da resposta evocada em janela de 0 a 50 ms (PSTH); STTC entre pares.
- Retenção de unidades entre janelas e proporção de eletrodos com artefato.
- Acurácia do decodificador do Teste 2, treinado no basal e aplicado às demais condições.

### 3.4 Critérios de qualificação (o "teste" propriamente dito)

Implementados em `bloqueio.qualificar_organoide` (casos em `dados_sinteticos/qualificacao_organoides.json`). Um organoide só entra na análise se:

1. tiver pelo menos **10 cruzamentos de limiar (5 × RMS)** em unidades-alvo, como no eNeuro;
2. o **veículo não mudar** a taxa de disparo além de uma margem: |taxa no veículo − taxa em B0| / taxa em B0 ≤ 20% (`variacao_relativa`), na taxa média das unidades-alvo;
3. a **lavagem recuperar** a atividade (grandeza e escala da comparação, absoluta ou relativa, fixadas no pré-registro);
4. no terminal, o **TTX reduzir os *spikes*** em pelo menos 90%: 1 − spikes sob TTX / spikes em B0 (`reducao_relativa`).

**Os valores 10, 20% e 90% são provisórios** (`bloqueio.LIMIARES_PROVISORIOS`), não validados experimentalmente; as definições finais e suas justificativas são fixadas no pré-registro antes da coleta.

**Regra para dados ausentes:** (1), (2) ou (3) não medidos **reprovam** o organoide; nunca há aprovação por omissão. O TTX é terminal e opcional: se não for aplicado, o critério (4) fica **"não avaliado"** e assim é relatado; o pré-registro decide se ele é obrigatório (`ttx_obrigatorio=True`).

Falha em (2) ou (3) **invalida o organoide** e é relatada.

**Dois critérios de TTX distintos.** O critério (4) é de **atividade** (redução de *spikes*). A análise do decodificador usa outro, de **desempenho**: acurácia sob TTX no nível do acaso, com margem provisória de 0,05 (`analisar_bloqueio`). Um não substitui o outro.

### 3.5 Análise

Efeito por organoide = valor da condição − valor do veículo; média, IC de 95% por bootstrap entre organoides (só com n ≥ 5; abaixo disso, descritivo) e permutação por troca de sinais (exata até 15 organoides). Relatam-se os organoides individualmente.

**Controles de veículo e deriva.** Com organoides-controle (`grupo = "controle"`), `analisar_bloqueio` calcula também a deriva da mesma janela nos controles e o **efeito líquido** (média dos tratados − média dos controles), com IC bootstrap (cada grupo reamostrado separadamente, n ≥ 5 em cada) e permutação dos rótulos de grupo. É o que separa a deriva lenta do efeito farmacológico: na bateria, `controles_so_deriva_n6` mostra tratados que sozinhos parecem ter efeito e, descontados os controles, não têm. Sem controles, o resultado traz um aviso de que a deriva não foi separada.

## 4. Teste 2: decodificador linear que gera padrões temporais

Inspirado em Sono et al. (2026), mas **fora do circuito fechado**, com análise offline em *notebook*.

- **Entrada:** 3 padrões temporais de estimulação (por exemplo, ritmos distintos, como o de *Clapping Music* usado no eNeuro), apresentados em ordem aleatória por blocos.
- **Estado:** contagens de *spikes* em caixas de 10 ms, por unidade, de 0 a 500 ms (`snn.gerar_conjunto(..., dur_ms=500, n_bins=50)` reproduz esse formato no silício).
- **Decodificador:** regressão de cume (*ridge*) linear (`DecodificadorLinear`, `GeradorDePadroes`). Duas tarefas: **classificar** o padrão e **gerar** um sinal-alvo (senoide e sinal quase periódico) como combinação linear dos estados; métrica **NRMSE** em dados retidos (`decodificador.nrmse`, `avaliar_geracao(..., metrica="nrmse")`).
- **Validação:** divisão por **blocos temporais** e por tentativas, **nunca aleatória por amostra**, para evitar vazamento temporal (Loeffler et al., 2026). O `gap` entre treino e teste é pelo menos o tempo de decaimento da autocorrelação, estimado no treino. A padronização é ajustada só no treino.
- **Linhas de base obrigatórias:**
  - (a) rótulos embaralhados, por **deslocamento circular**, que preserva a autocorrelação (`decodificador.acaso_por_permutacao`);
  - (b) decodificador alimentado só pelo artefato de estimulação ou pela entrada;
  - (c) rede pulsada simulada (braço B; `snn.py`);
  - (d) o mesmo decodificador após o bloqueio de AMPA e de NMDA (Teste 1).
- **Predição diferencial a testar:** o bloqueio de AMPA degrada mais a classificação de padrões rápidos; o de NMDA, mais os padrões que exigem integração em intervalos longos. É hipótese, não resultado.
- **Leitura honesta:** quem aprende é o decodificador. Só se atribui contribuição ao organoide se ele superar (a), (b) e (c).

## 5. Teste 3: organoide como camada de decisão numa esteira de ferramentas

Interface por contrato JSON, agnóstica à ferramenta (`docs/contrato_esteira.schema.json`; `esteira.decisao_para_contrato`):

`regra fixa ou Jev → vetor de escores → codificador de estimulação → organoide → decodificador linear → decisão (aceitar/rejeitar) → registro`

### 5.1 Camadas

- **Camada de decisão tipada (Jev, da TypeSafe AI).** Segundo fontes públicas (relatos do fabricante, artigos e imprensa técnica; a avaliação independente localizada, Deußer et al., 2026, é pré-publicação lida só no resumo), o Jev é um modelo "System One": recebe texto ou dados estruturados e perguntas tipadas e devolve, em uma única passagem, uma escolha entre opções nomeadas (distribuição de probabilidade), um escore em escala ordenada ou uma probabilidade booleana, sem texto livre. **Não é determinístico no sentido estrito:** fixa-se a versão do modelo e mede-se a reprodutibilidade entre chamadas (`esteira.medir_reprodutibilidade`). Dois papéis:
  1. **gerador dos escores** que alimentam o codificador de estimulação (saída tipada e numérica, que casa com a entrada do organoide);
  2. **decisor concorrente sem organoide**, o controle mais exigente: se o Jev sozinho decide tão bem quanto a esteira com organoide, o tecido não acrescenta nada.
- **Regra fixa ou solucionador determinístico:** linha de base totalmente reprodutível, que separa o efeito da camada probabilística do efeito do organoide.
- **Ferramenta generativa:** só como *proponente de candidatos* e como explicador do resultado, **nunca como juiz**. Fixar versão do modelo, temperatura e *prompt*; registrar cada chamada; congelar cada candidato antes do teste. **Nenhum dado de estudante vai ao serviço externo.**

### 5.2 Tarefa e controles

- **Tarefa mínima:** decisão binária sobre vetores sintéticos com ruído (por exemplo, aceitar se um escore composto passar de um limiar). Escopo de prova de conceito.
- **Controles de contribuição:** (a) decisão aleatória; (a') decisão só pelo Jev e só pela regra fixa, sem organoide; (b) decodificador linear sobre a entrada, sem organoide; (c) rede pulsada simulada; (d) organoide sob bloqueio de AMPA e NMDA (controle de lesão). **Se (d) ou (b) igualarem o organoide íntegro, a decisão não vem do tecido.**

### 5.3 Métricas (`esteira.executar_esteira`)

Acurácia (saída inválida conta como erro) com IC por bootstrap **por organoide**; Brier e ECE (calibração); taxa de saída inválida; latência; curva risco-cobertura; **ITR em bits/min** (fórmula de Wolpaw, usual em BCI, `itr_wolpaw`), que torna a esteira comparável ao braço C. **Conformidade de esquema não é acerto:** a correção semântica se avalia à parte.

**Limite:** a decisão está no decodificador. "Camada de decisão" descreve a arquitetura, não prova inteligência do tecido.

## 6. Como isto se encaixa nos braços

- **Braço A (SBI):** executa os Testes 1, 2 e 3 (o Teste 1 exige parceiro que aplique bloqueadores).
- **Braço B (silício):** mesma tarefa, com sinapses AMPA e NMDA simuladas e "bloqueio" por redução da condutância (`snn.py`). O contraste é limpo e reprodutível por semente, o que serve a H2. O TTX é modelado como bloqueio de canais de Na⁺ dependentes de voltagem (`bloqueio_na`: sem spikes, sinapses intactas), e **não** como bloqueio total de AMPA+NMDA: ambos silenciam os spikes, mas por mecanismos diferentes (`vm_medio_exc` os distingue: repouso sem AMPA e NMDA; despolarizada, sem spikes, sob TTX). É um modelo didático, sem canais de Na⁺ explícitos.
- **Braço C (EEG aberto):** não há manipulação de AMPA ou NMDA. Equivalente: o Teste 2 em registros públicos (`braco_C_eeg.md`). A assimetria já declarada se alarga e deve ser registrada. Para não agravar a "lealdade do pesquisador" (Tabela 5 do artigo), a tarefa-padrão do braço C (conjunto, divisão por sessão ou bloco, métricas e plano de análise) deve ser escrita com a mesma granularidade da do A **antes da revisão externa dos materiais** (meses 3 e 4).

## 7. A pergunta própria de cada grupo

Cada grupo registra, **antes de ver os resultados**, ao menos uma pergunta dentro do núcleo comum (por exemplo, janelas temporais, decodificador ou critério de comparação da esteira), com a decisão de análise que a responde (`templates/pergunta_do_grupo.md`).

## 8. Limites e riscos

- A plataforma do eNeuro usa células de camundongo e uma MEA específica; a Cortical Labs (CL API) usa células humanas. São parceiros e regimes éticos diferentes (o braço A usa hiPSC humana: consentimento do doador e comitê de origem, ainda não documentados; ver `origem_do_tecido.md`).
- Poucos organoides e 1.024 eletrodos por vez limitam a potência; o resultado é de piloto.
- Fármacos de pesquisa são manuseados só pela equipe do parceiro; submeter ao CEP.
- Os ganhos de Robbins et al. não persistiram em 45 min: **não equiparar adaptação da cultura à aprendizagem do estudante.**

## 9. Lista de verificação antes da coleta

- [ ] Parceiro habilitado, com documentação de linhagem, consentimento do doador, comitê de origem e biossegurança de nível 2, por escrito
- [ ] Preços de acesso (valores de imprensa em `origem_do_tecido.md`) confirmados com o fornecedor
- [ ] Substâncias, doses, tempos de equilíbrio e de lavagem documentados pelo parceiro
- [ ] Ordem contrabalançada gerada e arquivada; organoides-controle só com veículo definidos, com as mesmas janelas, e a análise do efeito líquido (tratados − controles) registrada
- [ ] Limiares de qualificação, de surto e de veículo registrados
- [ ] Caixas, janelas, `gap` e linhas de base do Teste 2 registrados
- [ ] Versão do Jev, esquema, limiar de confiança e número de repetições para a reprodutibilidade registrados
- [ ] Nenhum dado de estudante trafega para as plataformas
- [ ] Perguntas dos grupos registradas
