# Dicionário de dados dos modelos de planilha

Todos os arquivos são CSV em UTF-8, vírgula como separador, ponto como separador decimal, `NA` para ausente. **Nenhum nome real**: use apenas `id_anonimo` (chave guardada em separado pela escola).

## dados_estudantes.csv
| Coluna | Descrição |
|---|---|
| id_anonimo | Código sem relação com nome ou matrícula |
| escola, serie, estrato | `estrato` = escola × série (usado na randomização e na ANCOVA) |
| braco | A (SBI), B (IA inspirada no cérebro, silício) ou C (BCI com EEG aberto) |
| preferencia_tema | Preferência de tema declarada no T0 (moderadora, não critério de alocação) |
| t0_raciocinio, t1_raciocinio, t2_raciocinio | Escore total do teste de raciocínio científico |
| t0_engajamento, t1_engajamento | Escala de engajamento e interesse |
| data_t0, data_t1 | AAAA-MM-DD |
| motivo_sem_t1 | Se não há T1: o motivo (atrito, ausência, retirada) |

Entrada de `sbi4sem.analise`: `braco`, `estrato`, `t0` (= `t0_raciocinio`), `t1` (= `t1_raciocinio`); `t1 = None` onde ausente.

## fluxo_participantes.csv
Etapas do fluxo CONSORT: elegíveis, consentimento, randomizados, T0, T1, T2, por braço, com motivo das perdas.

## bloqueio_organoides.csv
Uma linha por organoide e condição. `condicao` ∈ `basal`, `veiculo`, `AMPA`, `NMDA`, `AMPA+NMDA`, `lavagem1`, `lavagem2`, `lavagem3`, `TTX` (terminal e opcional). `grupo` ∈ `tratado` (padrão) ou `controle`: organoides-controle recebem só veículo, nos mesmos tempos; neles, `condicao` rotula a JANELA correspondente (o que o tratado equivalente receberia naquele instante), e o `valor` é o medido sob veículo. A comparação tratados × controles (efeito líquido, que separa a deriva do efeito do fármaco) é feita por `analisar_bloqueio`. `valor` = desfecho (por exemplo, acurácia do decodificador); `metrica` diz qual. `ordem_bloqueio` = `AMPA>NMDA` ou `NMDA>AMPA`. Entrada de `sbi4sem.bloqueio.analisar_bloqueio`: `organoide`, `condicao`, `valor` e, se houver controles, `grupo`.

## esteira_itens.csv
Uma linha por item e camada. `probabilidades_json` = lista de probabilidades na ordem do esquema, ou vazio para a regra fixa. `valida` = 0/1 (saída inválida conta como erro). `latencia_ms` medida na esteira. `versao_modelo` e `data_acesso` são obrigatórios para a camada tipada.

## fidelidade_sessoes.csv, contatos_entre_bracos.csv, desvios_do_protocolo.csv
Registros de processo que sustentam as contramedidas de `docs/ameacas_validade.md`.
