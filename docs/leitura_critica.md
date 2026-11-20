# Atividade de leitura crítica: evidência, interpretação e promessa

Atividade para os Tipos I e II (todos os braços), ligada à neuroética do artigo (seção 5.7): **distinguir evidência de interpretação** e reconhecer a carga normativa de termos como "aprendizado", "inteligência" e "senciência" aplicados a tecido in vitro.

O material vem de repositórios públicos do GitHub sobre *organoid intelligence*. **As afirmações abaixo não foram verificadas por este projeto**: verificá-las é a tarefa.

## Parte 1: rastrear afirmações até a fonte primária

Para cada afirmação, os estudantes preenchem: fonte primária localizada, o que ela de fato mede, número e unidade corretos, e classificação (**evidência**, **interpretação** ou **promessa**).

| Afirmação encontrada | Onde apareceu | Pergunta de verificação |
|---|---|---|
| "Eficiência energética de até 100.000 vezes a do silício" | README de lista de recursos sobre drones autônomos | De onde vem o número? É medida ou projeção? O que se compara com o quê? |
| "800 mil neurônios aprenderam Pong em 5 minutos" (DishBrain) | Mesmo README | O artigo original (Kagan et al., 2022) fala em **neurônios** ou em **células** (incluindo glia)? O que "aprender" significa ali? |
| "Acesso remoto a organoides humanos a partir de US$ 1 mil por mês" | Mesmo README, sobre uma plataforma comercial | O preço está na página do fabricante? Em que data? O que inclui? |
| "Robô controlado por organoide desviou de obstáculos" | Mesmo README, link para imprensa | Há artigo revisado por pares? Quem decide: o tecido ou o decodificador? |
| "A simulação reproduz plasticidade neural e tomada de decisão" | Notas de um repositório de simulação com Brian2 | Ver Parte 2 |

Resposta de referência para o professor, só no item do DishBrain: o artigo usa cerca de 800 mil **células** (total cultivado, incluindo glia), como registra o próprio artigo deste estudo; trocar por "neurônios" é um deslize comum de divulgação.

## Parte 2: o que uma simulação mostra e o que não mostra

Um repositório público ("Organoid-Intelligence-Simulation", licença CC0) chama de "organoide" um grupo de 1.000 neurônios integra-e-dispara no Brian2, com uma única equação, cuja constante de tempo muda conforme a saída de uma rede neural artificial. As notas do projeto associam esse comportamento a plasticidade neural, oscilações, processamento sensorial e tomada de decisão.

Perguntas para o grupo:

1. Há sinapses no modelo? Os neurônios interagem entre si?
2. O que muda é um parâmetro definido de fora. Isso é "aprendizado" do modelo ou do programador?
3. Que observação, no modelo, permitiria falsificar a afirmação de "plasticidade"?
4. Compare com `sbi4sem/snn.py` (sinapses AMPA, NMDA e GABA, sem aprendizagem): o que **ele** também não mostra?

**Objetivo:** reconhecer a sobreatribuição, inclusive no material deste próprio projeto, sem concluir que simulações são inúteis. Simulações servem para praticar desenho e análise (estágio 0 da `trilha_em_estagios.md`), não para provar propriedades do tecido.

## Parte 3: a mesma lente sobre o Jev

O fabricante do Jev o apresenta como modelo que "não alucina". Pergunta: o que o formato tipado de fato garante (saída dentro do esquema) e o que não garante (decisão correta, calibração em dados novos, reprodutibilidade entre chamadas)? A esteira do Teste 3 mede essas três coisas.

## Registro

Cada grupo entrega a tabela da Parte 1 preenchida e uma resposta curta às Partes 2 e 3. A avaliação é formativa e não entra nos desfechos do piloto.
