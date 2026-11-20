# Delineamento, alocação e cronograma

Resumo operacional da seção 5.3 e 5.4 do artigo.

## Braços (mesma estrutura, carga horária, facilitadores e produto final)

| Braço | Tema | O que a comparação com a SBI isola |
|---|---|---|
| A: SBI | Biocomputação neuronal in vitro em nuvem | (referência) |
| B: IA inspirada no cérebro | Simulação de redes pulsadas em silício, mesmo repertório de Python e dados | Papel do substrato vivo e da variabilidade biológica |
| C: BCI com EEG aberto | Interface cérebro-computador e análise de EEG público (anonimizado, licença aberta) | Efeito de sinal neural real e ruidoso; a diferença para a SBI fica no tecido cultivado e na manipulação ao vivo |

Critério de autenticidade comum: o Tipo III apoia-se em dados reais e em perguntas de resposta não predefinida. Sem equivalência de carga, facilitadores e produto, compara-se pedagogia, e não tema.

## Alocação

1. Inclui-se o estudante após consentimento, assentimento e pré-teste (T0).
2. A pessoa externa ao ensino gera a sequência por estrato (escola × série), em blocos permutados de 3 ou 6, razão 1:1:1:

```bash
python -m sbi4sem.randomizacao --estratos "EscolaX-1:30,EscolaX-2:30" --saida sequencia.csv
```

3. A **semente fica com a pessoa externa**. Ao pesquisador vão o **carimbo SHA-256** (para o pré-registro) e, a cada inclusão, o braço (`alocar`).
4. A randomização suspende a correspondência entre interesse e tema que o SEM preconiza (custo deliberado); a preferência de tema é registrada e examinada como moderadora (campo `preferencia_tema`).
5. Os Tipos II e III seguem voluntários dentro de cada braço; análise por intenção de tratar. O pacote `sbi4sem` ainda não implementa a imputação para ITT, a análise de H2, a moderação pela preferência de tema nem a análise por protocolo completa: serão especificadas e codificadas no pré-registro (`preregistro_modelo.md`, seção 7).

## Cronograma de 12 meses

| Meses | Atividades |
|---|---|
| 1–2 | Busca sistemática registrada em bases de educação; material-base; **pedidos de documentação aos parceiros já no mês 1**; **submissão ao CEP no mês 2**, com TCLE, TALE e instrumentos preliminares |
| 3–4 | Parcerias; materiais dos comparadores com revisão externa; adaptação dos instrumentos; pré-registro; a adaptação final dos instrumentos e a definição do parceiro tramitam como **emenda** ao protocolo submetido |
| 5 | Consentimento e assentimento, T0, randomização, início do Tipo I |
| 5–10 | Tipos I, II e III (dois meses cada); T1 ao término do Tipo III |
| 11–12 | Análise pré-registrada, com correção cega ao braço; redação |

Condições cujo descumprimento inviabiliza o cronograma: aprovação do CEP até o fim do mês 4; ao menos um parceiro habilitado, com documentação por escrito, até o fim do mês 4; plataformas contratadas a partir do mês 5. Se a aprovação não vier a tempo, as etapas seguintes são deslocadas, e não executadas em versão reduzida.

## Contaminação entre braços

Turnos ou espaços distintos, registro de contatos (`templates/contatos_entre_bracos.csv`) e nenhum Tipo I aberto à escola, em qualquer tema, antes do T1.
