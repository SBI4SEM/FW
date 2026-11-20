# Ameaças à validade: registro operacional

Tabela 5 do artigo, transformada em registro de monitoramento. Preencha uma linha por ocorrência.

| Ameaça | Contramedida | Indicador a monitorar | Onde registrar |
|---|---|---|---|
| Novidade e atenção (efeito Hawthorne) | Comparadores igualmente de fronteira, com a mesma atenção e documentação | Horas de atenção e visitas externas por braço | `fidelidade_sessoes.csv` |
| Alinhamento entre tema e teste | Desfecho independente de tema, com conteúdo novo; materiais sem identificadores de tema; avaliadores cegos | Itens com vocabulário de um tema; quebra do cegamento | Revisão externa do instrumento; relato de cegamento |
| Lealdade do pesquisador | Materiais dos braços B e C revisados por especialista externo; roteiro de fidelidade registrado antes | Parecer da revisão; desvios de fidelidade por braço | `fidelidade_sessoes.csv` |
| Assimetria de manipulação (braço C) | Plano de análise escrito antes de abrir os dados, no Tipo III do braço C | Data do plano × data de acesso aos dados | `desvios_do_protocolo.csv` |
| Efeito de teto | Se muitos escores em T0 estiverem próximos do máximo (limiar no pré-registro), a tarefa aberta passa a primária | `analise.proporcao_teto` | Relatório de T0 |
| Atrito diferencial | Tipo III voluntário; intenção de tratar; fluxo de participantes | `analise.fluxo` por braço | `fluxo_participantes.csv` |
| Contaminação entre braços | Turnos ou espaços distintos; registro de contatos; nenhum Tipo I aberto à escola antes do T1 | Contatos registrados | `contatos_entre_bracos.csv` |
| Dependência de plataforma | Registro da carga recebida; análise por protocolo como sensibilidade; sem substituição silenciosa do tecido vivo por simulação | Interrupções, versões e carga por sessão | `desvios_do_protocolo.csv` |

## Ameaças específicas da tarefa-padrão (acrescentadas neste framework)

| Ameaça | Contramedida |
|---|---|
| Vazamento temporal na validação do decodificador | Blocos contíguos com `gap`; padronização só no treino; nunca validação aleatória |
| Pseudorreplicação (janelas tratadas como independentes) | O organoide é a unidade; bootstrap por conglomerado; resultados por organoide |
| Deriva do basal confundida com efeito do bloqueador | Veículo e lavagem; critério de estabilidade do basal; ordem contrabalançada |
| Artefato não dependente de disparos | Controle com TTX ao final |
| Confiança da camada tipada tomada como acerto | ECE, Brier e curva risco-cobertura medidos na própria esteira |
| Números do fabricante tratados como dados | Medir na esteira; relatar números do fabricante à parte e identificados |
| Saídas inválidas omitidas | Saída inválida conta como erro e é relatada como taxa |
