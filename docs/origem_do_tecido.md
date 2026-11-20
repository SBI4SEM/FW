# Decisão: origem do tecido do braço A (hiPSC humana)

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

**Decisão (20/11/2026).** O braço A usa **neurônios derivados de hiPSC humana**, em plataforma de nuvem (candidatas: Cortical Cloud/CL1 e FinalSpark Neuroplatform). A plataforma de camundongo (Elliott et al., 2023; Braingeneers) fica como **precedente educacional e fonte das hipóteses**, e não como plataforma do braço A. No artigo: seção 5.2.3 (parágrafo "Origem do tecido"); no `Resumo.docx`: seção 4.2.

A escolha foi feita com **dois fatos**, definidos pelos autores: (1) a diferença de preço para realizar o essencial do experimento na nuvem e (2) a oportunidade conceitual de cada origem.

## Fato 1: preço do essencial na nuvem

"Essencial" = estimulação, registro e programação em Python em circuito fechado (Testes 2 e 3). A farmacologia de receptores (Teste 1) não consta da oferta de nenhuma das três plataformas lidas e continua **capacidade a contratar**, com preço desconhecido em qualquer origem.

| | Humana: Cortical Cloud (CL1) | Humana: FinalSpark | Camundongo: Braingeneers (Elliott et al., 2023) |
|---|---|---|---|
| Preço divulgado | US$ 300 por semana por unidade (TechRadar, 14/06/2025); compra de US$ 35 mil. As páginas do fornecedor não trazem preço | "Contact for pricing" no site; relatos de imprensa de 2024 falam em cerca de US$ 500 por usuário por mês (**não conferido na fonte**) | Nenhum preço de acesso. Só o chip de MEA de alta densidade (cerca de US$ 200 por chip, além de equipamento caro) |
| Oferta do essencial | SDK em Python e Jupyter, circuito fechado, estimulação e leitura | API em Python, estimulação e leitura em tempo real, 4 organoides (compartilhados ou dedicados) | Demonstrada em dois cursos universitários, com API mínima e sessões ao vivo; sem oferta pública a escolas externas |
| Custo no Tipo III (2 meses, cerca de 9 semanas) | **cerca de US$ 2,7 mil** por unidade (9 × 300) | cerca de US$ 1 mil por usuário, se valer o relato de imprensa | **indeterminado** (depende de parceria) |

**Leitura.** Só a nuvem humana tem preço divulgado e de ordem de grandeza compatível com um piloto escolar. A de camundongo não é orçável com o que é público.

**Ressalvas.** Os preços vêm de imprensa (o "$" não traz código de moeda; presume-se dólar americano) e têm 5 a 17 meses; confirmar com os fornecedores antes de contratar. Não há desconto acadêmico nem prazo de entrada documentados. As páginas lidas em 20/11/2026 foram: corticallabs.com (inicial, /cl1, /cloud, /purchase), finalspark.com/neuroplatform e a matéria da TechRadar. A página da Braingeneers não pôde ser lida (certificado expirado).

## Fato 2: oportunidade conceitual

- **Pergunta autêntica (Tipo III).** As hipóteses F1 a F5 vêm de trabalhos em organoides **de camundongo** (Robbins et al., 2026, organoides corticais de camundongo, segundo o comunicado da UCSC; artigo lido só no resumo). Testá-las em neurônios humanos deixa de ser réplica e vira pergunta translacional em aberto, como o Tipo III exige. *A busca de 20/11/2026 não confirmou o papel de AMPA e NMDA nesse artigo: conferir no texto completo.*
- **Fronteira da SBI.** As nuvens comerciais de SBI (CL1, FinalSpark) usam neurônios humanos; é o objeto de que fala o resto do artigo (CL API, circuito fechado).
- **Neuroética.** Tecido humano dá substância ao debate pedagógico sobre consentimento do doador, proveniência e senciência (seção 5.7 do artigo).
- **O que se perde.** A continuidade direta com a única evidência educacional (Elliott, camundongo) e com o desenho de Robbins. Sem um braço de camundongo, um resultado diferente do da literatura não separa espécie de plataforma ou de protocolo.

## Consequências

- **Ética.** Sai a CEUA (Lei nº 11.794/2008), que caberia a organoides de camundongo. Ficam: consentimento do doador, aprovação do comitê de origem e biossegurança de nível 2, **a documentar por escrito pelo parceiro**; e a submissão do estudo com os estudantes ao CEP/CONEP. Nas páginas lidas, nenhuma das duas plataformas humanas traz essa documentação. Ela é condição de habilitação do parceiro (`governanca_e_viabilidade.md`).
- **Plano B.** Sem parceiro humano habilitado até o fim do mês 4, vale a trilha em estágios (`trilha_em_estagios.md`): o braço A não usa tecido vivo, e a emenda é registrada antes da randomização.
- **Código.** Nenhuma mudança funcional: a análise do bloqueio, o decodificador e a esteira são independentes da espécie.

## O que reverteria a decisão

1. Preço confirmado acima do orçamento do piloto, ou plataforma humana sem acesso a escolas.
2. Nenhum parceiro humano documentar origem e consentimento até o mês 4, e um parceiro de camundongo oferecer acesso com preço e farmacologia.

Qualquer reversão é registrada em `templates/desvios_do_protocolo.csv` e no pré-registro, antes da randomização.
