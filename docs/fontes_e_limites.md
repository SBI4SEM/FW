# Fontes, grau de leitura e limites do material

Registro do que sustenta cada parte do framework e do **estado de cada afirmação**: confirmada no texto completo, sustentada só por resumo, hipótese, implementação sintética ou decisão pendente. Nenhum documento prevalece automaticamente: divergências geram correção ou decisão versionada (ver "Papel de cada documento" no README).

> **Status (texto idêntico em todo o repositório).** Protocolo em planejamento. Hipóteses mecanísticas não confirmadas. Código testado apenas com dados sintéticos, o que verifica a implementação, e não efeitos farmacológicos nem aprendizagem. Etapas experimentais condicionadas à habilitação de parceiros e às aprovações éticas. Não há resultados empíricos de estudantes nem de organoides.

## Grau de leitura das fontes

| Fonte | Usada para | Grau de leitura |
|---|---|---|
| Elliott et al. (2023) | Plataforma conectada com organoides de camundongo; estimulação elétrica sem farmacologia de receptores | Texto completo |
| Robbins et al. (2026) | Hipóteses AMPA/NMDA (não confirmadas); organoides de camundongo, segundo o comunicado da UCSC | **Só resumo** |
| Williams (TechRadar, 14/06/2025) | Preço de aluguel do CL1 (US$ 300 por semana) e de compra (US$ 35 mil); neurônios humanos | Texto completo (20/11/2026); **preço de imprensa**, ausente do site do fornecedor |
| Cortical Labs (site, 2026) | CL1 e Cortical Cloud: SDK em Python, circuito fechado | Páginas lidas em 20/11/2026; **sem preço, sem origem celular, sem farmacologia** |
| FinalSpark (site) | Neuroplatform: API em Python, estimulação e leitura, 4 organoides; "contact for pricing" | Páginas lidas em 20/11/2026; **sem preço, sem origem celular, sem ética de origem, sem farmacologia**; US$ 500 por mês é relato de imprensa de 2024, **não conferido** |
| Loeffler et al. (2026) | Decodificação em culturas neurais, citado pelo artigo para o decodificador e a validação por blocos; pré-publicação (bioRxiv) | **Só resumo** |
| Sono et al. (2026) | Aprendizagem supervisionada online de padrões temporais em circuito fechado | **Só resumo** |
| Deußer et al. (2026) | Avaliação independente do Jev; pré-publicação (arXiv 2609.37647) | **Só resumo**, sem revisão por pares |
| Schottlender et al. (2026) | Modelo ABNIA | Pré-publicação (arXiv, v1) |
| Cai et al. (2026), citado no artigo | Motiva o conceito de organoide como camada de decisão (Teste 3); **não valida** o protocolo educacional, a farmacologia nem os critérios operacionais | **Só resumo**; pré-publicação (bioRxiv, 15/09/2026), sem revisão por pares; referência conferida na página do bioRxiv |
| *Communications Biology* (2025), material suplementar | Concentrações de NBQX e AP5 relatadas em organoides humanos | **Só trecho de busca**; não prescreve doses |

## Repositórios públicos consultados (compilado `base.txt`)

| Repositório | Usado para | Observação |
|---|---|---|
| OrganoidIntelligence (lachlanchen) | Lógica de trilha em estágios (`trilha_em_estagios.md`) | Roteiro, não evidência experimental |
| MetaBCI (TBC-TJU; Mei et al., 2024, citado no artigo), via OrganoidIntelligence | Ferramenta **candidata** para o braço C (`braco_C_eeg.md`); adoção não confirmada | Licença GPL v2.0: não copiado; referência (Mei et al., 2024) conferida no Crossref e no PubMed |
| Organoid-Intelligence-Simulation (danielathome19) | Material da atividade de leitura crítica | CC0; modelo sem sinapses, notas com sobreatribuição |
| Lista sobre drones autônomos (experimental computing) | Afirmações a verificar na leitura crítica | Números de divulgação, **não verificados** |

## O Jev (TypeSafe AI)

- Apresentado pelo fabricante como modelo "System One": devolve decisão tipada com confiança, não texto.
- **Latência e ausência de erros de formato** vêm de relatos do fabricante, sem reprodução independente em larga escala. Não entram como dado do estudo.
- A avaliação independente localizada (Deußer et al., 2026) descreve bom desempenho em classificação, probabilidades bem calibradas com limiares binários a ajustar, e desempenho fraco em decisões sequenciais. Foi lida só no resumo.
- Outros relatos de terceiros (calibração em dados novos, robustez adversarial, ausência de justificativa em linguagem natural) foram vistos apenas em resumos de busca e **não são afirmados** aqui.
- O adaptador do Jev **não está** neste repositório: deve ser escrito contra a documentação do fabricante.

## O que este repositório não é

- Não é um resultado. **Não há dados empíricos** de estudantes nem de organoides.
- A rede simulada (`snn.py`) usa **parâmetros didáticos, não ajustados a organoides**. Seu comportamento não prevê o do tecido vivo.
- Os dados de `dados_sinteticos/` são **sintéticos**, gerados para testar o software.
- O tamanho amostral viável num piloto escolar tende a produzir resultado **inconclusivo**; o relato deve dizê-lo.
- O desenho **não tem braço sem enriquecimento**: não separa o efeito do SEM do de maturação e reteste.
- Não prevê adaptações para estudantes com dupla excepcionalidade.

## Decisões em aberto

- Instrumento final do desfecho primário e limiares (concordância, teto, efeito de interesse prático).
- Parceiro habilitado, substâncias, doses e tempos (cabem ao parceiro).
- Autoria e forma de citação do repositório.

## Pendências documentais

- **Bases da busca de 19/11/2026:** confirmadas pelos autores como **OpenAlex e Crossref** (restritas aos 12 meses anteriores). O artigo foi uniformizado nesse ponto; a menção a "OpenAlex e arXiv" no Relatorio.md refere-se ao teste de lacuna do relatório de debate, outra fonte. A confirmação foi verbal: os registros originais (consultas, filtros, contagens) continuam a incluir no diário de busca.
- **Diário de busca:** modelo em `docs/registro_de_busca.md`, a preencher dos registros originais. O artigo declara que o registro detalhado das consultas (termos, filtros, contagens e motivos de inclusão ou exclusão) **não acompanha esta versão** e será organizado como material suplementar (`docs/registro_de_busca.md`, a criar a partir dos registros originais).
- **Limiares do Teste 1** (veículo 20%, TTX 90%, lavagem 0,10 na escala da métrica): provisórios, a fixar no pré-registro.

## Referências conferidas

- CAI, Hongwei et al. Brain organoid computing for robotic decision-making. bioRxiv, preprint, 2026. DOI: 10.64898/2026.09.09.750426. Conferida na página do bioRxiv; lida só no resumo.
- MEI, Jie et al. MetaBCI: an open-source platform for brain–computer interfaces. Computers in Biology and Medicine, v. 168, art. 107806, 2024. DOI: 10.1016/j.compbiomed.2023.107806. Publicado online em 4 dez. 2023; PMID 38081116. Conferida no Crossref e no PubMed (resumo).

## Licença

Licença **MIT** (arquivo `LICENSE` na raiz), para código, documentos, modelos e dados sintéticos. O titular dos direitos está como "Autores do projeto SBI4SEM"; os autores podem substituí-lo por nomes ou instituição. A licença não se estende a serviços, modelos e documentação de terceiros (por exemplo, o Jev e as plataformas de biocomputação).
