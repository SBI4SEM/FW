# Braço C: decodificação em EEG público

Guia do equivalente ao Teste 2 no braço C (BCI com EEG aberto). Inspirado no MetaBCI (Mei et al., 2024), plataforma aberta em Python para BCI não invasiva, cujas informações abaixo vêm do README do projeto.

> **Status do MetaBCI e dos conjuntos:** ferramenta e conjuntos **candidatos**, não adotados. Os dados do braço C serão selecionados entre conjuntos públicos de EEG; a anonimização, a licença e a compatibilidade dos termos de uso serão verificadas e documentadas antes do uso. A inclusão de um conjunto num carregador de software não comprova, sozinha, licença compatível.

## 1. Por que o MetaBCI serve de referência

O MetaBCI tem três partes: `brainda` (importar conjuntos de dados, pré-processar EEG e decodificar), `brainflow` (processamento online) e `brainstim` (desenho de paradigmas). Ele estende a API do MOABB e reúne carregadores de conjuntos públicos e algoritmos de decodificação. No braço C, interessa só o `brainda`, **offline**: os estudantes não coletam EEG (nenhum dado neural é coletado dos estudantes).

## 2. Conjuntos públicos candidatos (suportados pelo MetaBCI)

| Paradigma | Conjuntos |
|---|---|
| Imagética motora (MI) | AlexMI, BNCI2014001, BNCI2014004, PhysionetMI, PhysionetME, Cho2017, MunichMI, Schirrmeister2017, Weibo2014, Zhou2016 |
| SSVEP | Nakanishi2015, Wang2016, BETA |

**A licença de cada conjunto deve ser conferida por escrito antes do uso** (requisito do protocolo: registros públicos, anonimizados e de licença aberta). Estar num carregador não garante licença compatível.

Sugestão didática: um conjunto **SSVEP** dá o paralelo mais direto com o Teste 2, pois o sinal responde a padrões temporais de estimulação (frequências), como os ritmos aplicados ao organoide.

## 3. Algoritmos disponíveis e o que usar

- Decomposição: SPoC, CSP, MultiCSP, FBCSP; CCA e variantes, TRCA, TDCA, DSP.
- Variedades: geometria riemanniana e métodos de alinhamento.
- Aprendizado profundo: ShallowConvNet, EEGNet, ConvCA, GuneyNet.
- Transferência: MEKT, LST.

**Para a comparação entre braços, o decodificador principal é o mesmo: linear (ridge)**, em `sbi4sem.decodificador`. Algoritmos específicos (por exemplo, TRCA para SSVEP ou CSP para MI) entram como pergunta própria do grupo, nunca no lugar do decodificador comum. Sem isso, compara-se algoritmo, e não tema.

## 4. Cuidados de validação

- A função `generate_kfold_indices` do MetaBCI usa **k-fold estratificado com embaralhamento**. Para tentativas de EEG de uma mesma sessão, isso pode vazar deriva lenta entre treino e teste. No protocolo, a divisão é **por sessão ou bloco** (o MetaBCI tem `EnhancedLeaveOneGroupOut`, com o grupo = sessão ou bloco) ou por blocos temporais com `gap` (`sbi4sem.decodificador.divisoes_por_blocos`).
- Acaso estimado por permutação que preserve a estrutura temporal (`acaso_por_permutacao`).
- Métrica comum à esteira: **ITR em bits/min** (fórmula de Wolpaw; o MetaBCI calcula ITR teórico e prático em `brainda.utils.performance`; o FW usa `esteira.itr_wolpaw`).

## 5. Licença e dependência

O MetaBCI é distribuído sob **GNU GPL v2.0**. Este repositório é MIT e **não copia código do MetaBCI**: quem quiser usá-lo instala o pacote à parte (`pip install metabci[brainda]`), carrega os dados no próprio *notebook* e passa matrizes `X`, `y` ao `sbi4sem`.

## 6. Assimetria registrada

No braço C não há manipulação de AMPA e NMDA nem intervenção ao vivo: o estudante analisa registros já coletados. Por isso, o Tipo III do braço C inclui **plano de análise escrito antes de abrir os dados**, e a assimetria restante é registrada (`ameacas_validade.md`).

## Referência

MEI, Jie et al. MetaBCI: an open-source platform for brain–computer interfaces. *Computers in Biology and Medicine*, v. 168, art. 107806, 2024. DOI: 10.1016/j.compbiomed.2023.107806. Publicado online em 4 dez. 2023; PMID 38081116. Metadados conferidos no Crossref e no PubMed.
