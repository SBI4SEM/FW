# Instrumentos, rubrica e fidelidade de implementação

Seção 5.4 do artigo. Tudo aqui é **ponto de partida**: instrumentos e rubricas exigem tradução, adaptação, verificação de confiabilidade e revisão externa antes do uso.

## 1. Desfechos

| Nível | Medida | Observações |
|---|---|---|
| Primário | Variação pré→pós no escore total de teste de raciocínio científico independente de tema | Candidato: teste de Lawson (2000), pelo escore total, após tradução, adaptação transcultural e verificação de confiabilidade |
| Secundário 1 | Tarefa aberta em cenário novo para todos os braços | Planejar experimento, interpretar dados ruidosos e concluir declarando a incerteza |
| Secundário 2 (opcional) | Scientific Reasoning Scale (Drummond; Fischhoff, 2017), após adaptação | |
| Concorrente | Engajamento e interesse, por escala a definir | Separa o fascínio tecnológico do raciocínio |

Momentos: T0 (pré-teste), T1 (ao término do Tipo III) e T2 (seguimento, fora dos 12 meses).

## 2. Rubrica da tarefa aberta (esboço inspirado na RED, a adaptar)

A rubrica é inspirada na RED (Dasgupta; Anderson; Pelaez, 2014) e **precisa ser adaptada e validada**; as dimensões abaixo são proposta de partida deste estudo, não a RED original. Cada dimensão recebe 0 a 3.

| Dimensão | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Pergunta e hipótese | Ausente | Vaga | Testável, sem previsão | Testável, com previsão que pode falhar |
| Variáveis e controles | Não identifica | Identifica a variável-resposta | Identifica variável independente e um controle | Controles que isolam a explicação concorrente |
| Plano de coleta | Ausente | Genérico | Executável, sem replicação | Executável, com replicação ou unidade experimental correta |
| Dados ruidosos | Ignora a variação | Cita variação | Resume com medida de dispersão | Usa a variação para limitar a conclusão |
| Declaração de incerteza | Ausente | Genérica | Específica | Específica e propõe como reduzi-la |
| Conclusão | Excede os dados | Parcialmente proporcional | Proporcional | Proporcional e aponta alternativas |

**Procedimento:** dois avaliadores independentes, cegos ao braço e ao momento; materiais sem identificadores de tema; ordem das respostas aleatória. Concordância (kappa ponderado ou CCI): o **limiar é fixado no pré-registro**; discordâncias resolvidas por terceiro avaliador, também cego.

## 3. Roteiro de fidelidade

Registrado antes da coleta e preenchido a cada sessão (`templates/fidelidade_sessoes.csv`). Objetivo: mostrar que os braços recebem **a mesma estrutura, carga e atenção**, e não só o mesmo tema.

Por sessão, por braço:

- [ ] Duração real (min) e carga prevista cumprida
- [ ] Facilitador (mesmos nos três braços)
- [ ] Tipo do SEM (I, II ou III) e atividade
- [ ] Produto parcial gerado
- [ ] Dados reais usados no Tipo III e pergunta de resposta não predefinida
- [ ] Atividades de neuroética presentes (A: senciência; B e C: equivalente)
- [ ] Desvios do plano e motivo
- [ ] Contato com participantes de outro braço (`contatos_entre_bracos.csv`)

A revisão de fidelidade dos materiais dos braços B e C é feita por especialista externo, para conter a lealdade do pesquisador ao tema que concebeu.

## 4. Engajamento e interesse

Escala a definir (candidata a adaptação). Aplicada em T0 e T1; analisada como explicação concorrente do ganho em raciocínio.
