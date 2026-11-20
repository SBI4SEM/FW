# Trilha em estágios do braço A

O roteiro do projeto OrganoidIntelligence propõe começar por artigos e *spikes* de MEA simulados, provar o software de circuito fechado e só então passar a plataformas remotas de *wetware*. Este framework adota a mesma lógica para o braço A: cada estágio tem **critério de entrada**, e o software de um estágio é reaproveitado no seguinte.

A trilha também organiza o **plano B** do artigo (seção 5.7): se um estágio não for alcançado até o fim do mês 4, a mudança é registrada como **emenda antes da randomização**, sem substituição silenciosa do tecido vivo por simulação.

| Estágio | O que roda | Critério de entrada | Testes possíveis |
|---|---|---|---|
| 0. Simulação | Rede LIF com AMPA e NMDA (`snn.py`) e bateria sintética | Nenhum (já disponível) | Treino de análise para todos; é o braço B, e **não** conta como braço A |
| 1. Registros públicos | Registros públicos de culturas neuronais | Licença aberta e anonimização conferidas por escrito (disponibilidade não verificada) | Teste 2 sem intervenção |
| 2. Plataforma remota com estimulação | Plataforma remota com neurônios humanos (do tipo Cortical Cloud ou FinalSpark): estimulação, registro e API em Python, sem farmacologia de receptores documentada | Parceiro habilitado (linhagem, ética de origem, biossegurança) e contrato | Teste 2 com estímulo ao vivo; Teste 3 sem o organoide bloqueado |
| 3. Farmacologia via parceiro | Bloqueio de AMPA e NMDA aplicado pela equipe do parceiro | Estágio 2 + documentação ética da origem do tecido (consentimento do doador, comitê de origem, biossegurança de nível 2) + doses documentadas | Testes 1, 2 e 3 completos |

## Regras

- O braço A do piloto, como desenhado, **exige o estágio 3**. Os estágios 1 e 2 são versões reduzidas e, se usados, mudam o que a comparação isola; isso vai para o relato.
- Cada passagem de estágio é registrada em `templates/desvios_do_protocolo.csv` com data e responsável.
- O estágio 0 nunca substitui o tecido vivo no braço A: dissolveria o contraste A–B.
