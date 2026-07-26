# Relatório Técnico Detalhado — Evolução do Projeto

**Nome atual do projeto/produto**: **Ferramenta de Projeção de Orçamento 2026** (CFC).

**Escopo**: reconstrução completa e minuciosa de tudo o que foi feito neste projeto, desde o
estado inicial (app Streamlit com dados de teste, substituindo macros VBA) até o estado atual
(a Ferramenta de Projeção de Orçamento 2026 — projeção de fechamento de despesa e receita,
alimentada por dados reais da API aberta do CFC). Este documento complementa o `Orcamento2026.md`
(referência viva e concisa do projeto) com o racional completo de cada decisão e cada mudança de
arquivo.

---

## 1. Estado inicial do projeto (antes de qualquer mudança)

### 1.1 O que existia

Um app Streamlit (`orcamento_2026_app/orcamento_app/`) que **substituía as macros VBA** da
planilha `Proposta_Orçamentária_2026.xlsb` por telas equivalentes — lançamento manual de
diárias/passagens e despesas gerais, mais telas de consulta (Projeção, Resumo, Memória de
Cálculo, PCA).

```
Home.py                          tela inicial + navegação
pages/
  projecao.py                    Projeção Orçamento 2026 (tabela dinâmica multi-ano)
  resumo.py                      Resumo por Coordenadoria + exportação PDF
  memoria.py                     Memória de Cálculo de diárias + exportação PDF
  pca.py                         PCA 2026 + exportação Excel
core/
  config.py                      caminhos dos arquivos (BASES_XLSX, ORCAMENTO_HISTORICO_XLSX, ORCAMENTO_2026_DB)
  loaders.py                     leitura das abas fixas de bases.xlsx (com cache por mtime)
  db.py                          schema e CRUD do SQLite orcamento2026.db
  calculos.py                    réplica das regras de cálculo das macros VBA
  agregacao.py                   monta a Projeção (histórico + vivo) e o Resumo
  formatos.py                    formatação BR (moeda, número, data)
  tabela_html.py                 tabelas HTML com colapso via JS (pivot Projeto>SubProjeto>Conta)
  dialogs.py                     modais de lançamento (Diárias / Despesas Gerais)
  forms_diarias.py               formulário de Diárias e Passagens
  forms_despesas.py              formulário de Despesas Gerais (Contratação/Renovação/etc.)
  exportar.py                    gerar_pdf_memoria / gerar_pdf_resumo / gerar_excel_pca
data/
  bases.xlsx                     abas fixas: Datas, PlanoDeContas, Projetos, SubProjetos,
                                  PCA2025, ListaContratos, ParametrosDiaria, Diario
  orcamento_historico.xlsx       orçamento fixo de anos < 2026 (aba "Orcamento")
  orcamento2026.db                SQLite "vivo" (tabelas orcamento_2026, lancamentos_meta, pca_2026)
  exportados/                    PDFs/Excel já gerados pelo app (amostras de teste)
```

### 1.2 Qualidade e natureza dos dados iniciais

Investigação (via 2 agentes de exploração em paralelo, leitura direta com pandas/sqlite3) revelou
que **praticamente todo o conteúdo de dados era fictício**:

| Fonte | Conteúdo real? |
|---|---|
| `Projetos`, `SubProjetos`, `PCA2025`, `ListaContratos`, `Diario` (bases.xlsx) | **100% teste** — 1 projeto fictício "5008 - PROJETO TESTE" / subprojeto "110 - UO TESTE", 1 contrato-fantasma (segurança predial/brigada de incêndio) repetido nas 3 abas |
| `orcamento_historico.xlsx` | **100% teste** — 3 linhas (2023/2024/2025), mesmo projeto/conta fictícios |
| `PlanoDeContas` (222 contas) | Real, mas cobre **só** despesa (`6.3 Execução da Despesa`, MCASP/Lei 4.320) — nenhuma conta de receita |
| `ParametrosDiaria` | Parece real (valores de diária/passagem/auxílio/reajuste sem marcação "TESTE") |
| `Datas` (calendário 2022-2027) | Real, mas **código morto** — carregada por `loaders.datas()` e nunca usada por nenhuma tela |
| `orcamento2026.db` | 7 lançamentos, todos do projeto de teste |

**Conclusão da fase de diagnóstico**: a arquitetura de cálculo (regra "D soma, C diminui" do
Diário, normalização de conta, junção Projeto/SubProjeto/Conta) era sólida e reaproveitável, mas
**não havia nenhum dado real** para alimentá-la, e **nenhuma infraestrutura de receita** existia
em lugar nenhum (nenhuma conta de receita cadastrada, nenhum lançamento, nenhum parâmetro).

O `README.md` original já avisava sobre isso explicitamente: *"substitua o conteúdo de bases.xlsx
e orcamento_historico.xlsx pelos dados reais quando for usar de verdade"*.

### 1.3 O pedido original do usuário

Evoluir o projeto para gerar **projeções de receita e despesa do CFC para 2026** de forma
"bem eficaz" — não apenas continuar com lançamento manual, mas um modelo de projeção defensável.
Depois, o escopo foi refinado em etapas (ver seção 2): primeiro focar só em despesa, deixando
receita para depois; e usar como base um **modelo confiável** em vez de "chutes".

---

## 2. Decisões tomadas (cronologia)

### 2.1 Primeira rodada de opções (antes de saber que havia dados reais disponíveis)

Nesse ponto, ainda sem acesso a dados reais, foram apresentadas opções de arquitetura para
receita (estrutura paralela vs. schema unificado) e de método de projeção de despesa (bottom-up
por contrato, rolagem do executado, paramétrico, modelagem de pessoal, estatístico). O usuário
escolheu:
- **Estrutura paralela** para receita (não unificar com despesa no mesmo schema).
- Adiar receita para uma segunda etapa.
- Focar em um **modelo confiável de projeção de despesa** — e pediu para primeiro checar se
  havia dados reais disponíveis em algum lugar do computador.

### 2.2 Descoberta da fonte de dados reais

O usuário apontou a pasta `C:\Users\wandney\Documents\DECONT\Códigos`. Essa pasta continha:

```
Códigos/
  baixar_diario.py               script que consulta a API de dados abertos do CFC
  baixar_orçamentoatualizado.py  idem, para orçamento
  baixar_plano_contas.py         idem, para plano de contas
  baixar_saldoinicial.py         idem, para balanço patrimonial
  Diário/
    Diario_2022.csv ... Diario_2026.csv   (148–164 MB cada, ~150-160 mil lançamentos/ano, 27 conselhos)
  Fixas/
    balanco_patrimonial_2021.csv
    Conselhos.csv                cadastro dos 27 conselhos (CFC + 26 CRCs)
  OrçamentoAtualizado/
    orcamento_2022_2026.csv      27.798 linhas — Ano, Conselho, Conta, Descrição, Orçamento Inicial, Realizado
  PlanoContas/
    PlanoContas_2021_2024.csv    63 MB, plano de contas completo (todas as classes contábeis)
```

Os scripts `baixar_*.py` batem na API `https://www3.cfc.org.br/spw/API_SPW/dadosAbertos/...` —
**é a própria API de dados abertos do CFC**, cobrindo os 27 conselhos (CFC + 26 CRCs), anos
2021/2022 a 2026. Ou seja: **dados reais, oficiais, já em formato tabular**, muito superiores em
volume e qualidade ao que estava em `bases.xlsx`.

Amostragem confirmou, para o CFC especificamente:
- Orçamento 2026: R$ 132.578.920,00 (receita = despesa, orçamento equilibrado por desenho).
- Plano de contas: ramo `6.2` = Execução da Receita (antes inexistente em `bases.xlsx`), ramo
  `6.3` = Execução da Despesa.
- Diário do CFC: ~52 a 74 mil lançamentos reais por ano (2022-2025 fechados, 2026 até 17/06).

Também foi encontrado `DECONT/Alinhamento PO2027.docx` — um documento de reunião discutindo a
metodologia da Proposta Orçamentária 2027 e o conceito de "Orçamento Real", que **confirma o
contexto institucional**: a entidade está mesmo em processo de repensar a forma de projetar o
orçamento, o que valida a motivação do projeto.

### 2.3 Validação da regra de cálculo do executado

Antes de confiar em qualquer número derivado do Diário, a regra de sinal foi **testada
empiricamente** contra o "Realizado" oficial do CSV de orçamento (ano de 2025, fechado, portanto
um gabarito confiável):

- **Despesa** (contas folha do ramo `6.3`): `executado = ΣD − ΣC` → **92 de 92 contas bateram**
  (tolerância R$ 0,05).
- **Receita** (contas folha do ramo `6.2`): `realizado = ΣC − ΣD` → **40 de 40 contas bateram**.

Achado crítico documentado: aplicar a regra no ramo **inteiro** (não só nas contas-folha de 11
dígitos) soma zero, porque os níveis sintéticos e as contas de controle (`6.3.9`) se compensam.
A regra só é válida nas **contas folha**. Esse detalhe, se ignorado, teria produzido um motor de
projeção baseado em uma premissa de sinal errada.

### 2.4 Segunda rodada de decisões (com os dados reais confirmados)

Com a fonte de dados real identificada e a regra validada, três perguntas foram colocadas e
respondidas pelo usuário:

1. **Modelo de projeção de despesa**: escolhido o **Modelo 3 + Modelo 2 como conferência** — um
   modelo híbrido por natureza de despesa (método certo para cada tipo de conta) rodando como
   oficial, com um modelo estatístico simples (sazonal puro) rodando em paralelo só para
   destacar divergências e servir de checagem cruzada.
2. **Objetivo primário**: **só o fechamento de 2026** (não a Proposta Orçamentária 2027, que
   fica para outro momento/outro processo).
3. **Dimensão de análise**: **por conta contábil** — os dados abertos da API não trazem a
   dimensão Projeto/SubProjeto (isso exigiria uma extração interna do sistema SPW do CFC, fora do
   escopo atual); a granularidade de conta contábil já é suficiente para o objetivo de
   fechamento.

Essas três decisões definiram toda a arquitetura das etapas seguintes.

---

## 3. Etapa 1 — Importador de dados reais

### 3.1 Objetivo

Transformar os CSVs brutos da pasta `Códigos` (centenas de MB, todos os 27 conselhos, todas as
classes contábeis) em um banco SQLite compacto, filtrado só para o CFC, e comprovadamente
reconciliado com o dado oficial — sem que o app precise nunca ler os CSVs grandes diretamente.

### 3.2 Arquivos criados/alterados

- **`core/config.py`** (alterado): adicionadas as constantes `CODIGOS_DIR` (aponta para
  `DECONT/Códigos`, sobrescrevível por `ORCAMENTO_CODIGOS_DIR`), `DADOS_REAIS_DB` (novo arquivo
  `data/dados_reais.db`, **separado** de `orcamento2026.db` de propósito — um é dado real
  importado da API, o outro é a "tabela viva" de lançamentos manuais do app antigo; misturá-los
  correria o risco de contaminar um com o outro) e `CONSELHO_PADRAO = "CFC"`.
- **`core/dados_reais.py`** (novo módulo, independente do Streamlit — roda em linha de comando):
  - Schema SQL com 5 tabelas: `orcamento_anual` (ano, conselho, conta, descrição, orçamento
    inicial, realizado, flag `eh_folha`), `execucao_mensal` (ano, mês, conselho, conta, soma de
    débitos, soma de créditos, nº de lançamentos — o Diário já agregado por mês, não lançamento a
    lançamento), `plano_contas_real` (conta, descrição, 3 níveis de grupo), `reconciliacao`
    (conferência executado × realizado por conta/ano) e `importacao_meta` (metadados: data da
    importação, mês/data máxima do Diário por ano).
  - `importar_orcamento()`: lê `orcamento_2022_2026.csv`, filtra `Conselho == 'CFC'`, calcula
    `conta_norm` (código sem pontos) e `eh_folha` (11 dígitos = conta de lançamento, não
    agrupadora).
  - `importar_plano_contas()`: lê `PlanoContas_2021_2024.csv` **em blocos** (`chunksize=500_000`,
    arquivo de 63 MB) para não estourar memória, mantém a versão mais recente de cada conta.
  - `importar_diarios()`: para cada `Diario_AAAA.csv` (até 164 MB), lê em blocos de 1 milhão de
    linhas, filtra CFC, agrega por `(ano, mês, conta, D/C)` **já dentro do loop de leitura**
    (nunca materializa o arquivo inteiro em memória), grava em `execucao_mensal`, e registra a
    data máxima de lançamento de cada ano.
  - `reconciliar()`: implementa a regra de sinal validada (`D−C` despesa, `C−D` receita) só nas
    contas folha 6.2/6.3, compara com o `Realizado` oficial dos anos fechados, grava divergências
    (se houver) na tabela `reconciliacao`.
  - `importar_tudo()`: orquestra as 4 funções acima e registra o resultado em `importacao_meta`.
- **`importar_dados.py`** (novo, na raiz do app): CLI (`python importar_dados.py [--conselho
  CFC] [--codigos-dir ...]`), sai com código de erro 2 se a reconciliação encontrar qualquer
  divergência (torna o processo auditável e falha-visível, não silencioso).

### 3.3 Resultado da primeira execução

- Tempo: ~10 segundos para processar ~630 MB de CSV.
- `orcamento_anual`: 1.092 linhas (CFC, 2022-2026, todos os níveis).
- `execucao_mensal`: 18.198 linhas (conta × mês agregado).
- `plano_contas_real`: 3.195 contas distintas.
- Banco final: **2,5 MB** (vs. 630 MB de CSV de origem).
- **Reconciliação 2022-2025: 100%** (91-95 contas de despesa/ano, 40-42 de receita/ano, todas
  batendo).
- **Conferência extra em 2026 (ano aberto, sem gabarito "fechado")**: mesmo assim, a soma do
  executado nas contas orçamentárias bateu **ao centavo** com o `Realizado` do próprio CSV de
  orçamento (despesa R$ 42.503.922,95, receita R$ 69.876.919,73 até 17/06/2026) — evidência
  adicional de que a regra de sinal está correta mesmo fora da amostra de validação original.

---

## 4. Etapa 2 — Motor de projeção (M3 + M2)

### 4.1 Objetivo

Implementar o modelo híbrido decidido na seção 2.4: cada conta de despesa classificada por
natureza, cada natureza com o método de projeção mais adequado ao seu comportamento, mais uma
conferência estatística independente rodando em paralelo em toda conta.

### 4.2 Arquivo criado: `core/projecao_engine.py`

- **Schema novo**: `projecao_config` (override/reajuste manual por conta — `conselho, conta →
  método, parâmetros JSON`), `projecao_parametros` (parâmetros globais, ex. reajuste de
  data-base do Pessoal), `projecao_resultado` (o resultado persistido de cada rodada: orçamento,
  YTD, projeção restante, fechamento M3, conferência M2, divergência, confiança, memória de
  cálculo — 1 linha por conta/ano).
- **Classificação por natureza** (`natureza_da_conta()`): baseada no prefixo do código contábil.
  Para despesa: `6.3.1.1` → PESSOAL, `6.3.1.3.02.03`/`04` → DIÁRIAS_PASSAGENS, `6.3.1.3.02.01` →
  CONTRATOS (com exceção nomeada: `...011`, Exame de Suficiência, vira EVENTOS por ter perfil de
  gasto muito diferente de um contrato comum), `6.3.2` → CAPITAL, resto → DEMAIS.
- **Método sazonal** (`_projetar_sazonal`) — usado por Pessoal, Diárias, Eventos, Capital e
  Demais — com uma **cadeia de 4 fallbacks** (do mais informativo ao mais conservador):
  1. Perfil histórico 2022-2025 robusto (≥ 20% do ano já ocorrido até o mês de corte) → método
     da razão: `fechamento = YTD ÷ % acumulado histórico`.
  2. Perfil concentrado no fim do ano (ex.: 13º salário, que quebraria o método da razão) →
     método aditivo: média nominal dos meses restantes em 2024-2025, ajustada por um fator de
     crescimento do grupo (limitado a 0,8×–1,3× para não amplificar ruído).
  3. Sem histórico, mas com YTD → projeção proporcional ao tempo decorrido no ano.
  4. Sem histórico e sem YTD → 90% do orçamento (estimativa conservadora, não otimista).
- **Método run-rate** (`_projetar_runrate`) — usado por Contratos: média dos últimos 3 meses
  completos × meses restantes, com reajuste percentual opcional a partir de um mês configurável
  por conta (pensado para reajustes contratuais pontuais).
- **Reajuste de data-base do Pessoal**: parâmetro global (`pessoal_reajuste_pct`,
  `pessoal_mes_reajuste`) aplicado sobre o resultado do método sazonal, a partir do mês
  configurado.
- **Detecção automática do mês de corte** (`mes_corte_padrao`): olha a data máxima de lançamento
  do Diário do ano; se o dia for menor que 28, considera o mês parcial e recua para o mês
  anterior (evita projetar com base em um mês incompleto sem que ninguém precise lembrar disso).
- **Conferência M2**: para toda conta, roda o método sazonal puro (sem run-rate, sem reajustes),
  independente do método M3 escolhido — serve de "segunda opinião" estatística.
- **Overrides manuais**: exigem `justificativa` obrigatória; o valor de fechamento é aceito
  diretamente, mas o restante (fechamento − YTD) é distribuído pelos meses seguindo o perfil
  sazonal da própria conta (refinado depois, na etapa da curva mensal — ver seção 7).

### 4.3 Arquivo criado: `projetar_fechamento.py` (CLI)

`python projetar_fechamento.py [--ramo 6.3|6.2] [--mes-corte N] [--detalhe]` — imprime resumo por
natureza, alerta de divergências M3×M2 e de contas de confiança baixa.

### 4.4 Resultado da primeira execução (despesa, corte maio/2026)

| Natureza | Orçamento | Fechamento M3 | % |
|---|---:|---:|---:|
| Pessoal e Encargos | 36,1 mi | 38,5 mi | 106,8% |
| Contratos e Serviços | 53,9 mi | 35,2 mi | 65,3% |
| Diárias e Passagens | 10,7 mi | 19,7 mi | **183,9%** |
| Eventos e Exames | 13,4 mi | 8,2 mi | 61,4% |
| Despesas de Capital | 11,4 mi | 5,9 mi | 52,1% |
| Demais Correntes | 7,1 mi | 5,5 mi | 76,7% |
| **TOTAL** | **132,6 mi** | **113,0 mi** | **85,3%** |

Achados relevantes já na primeira rodada: Diárias e Passagens projetando quase o dobro do
orçamento (sinal para investigação prioritária), 15 contas de contratos com divergência
M3×M2 acima de 10% (candidatas a revisão humana), 14 contas com confiança baixa (majoritariamente
capital, que por natureza não se presta a projeção estatística pura).

### 4.5 Testes realizados

Um script de smoke-test validou, isoladamente: override manual com justificativa, reajuste
percentual de contrato a partir de um mês configurado, e reajuste global de data-base do
Pessoal — todos os três produzindo o efeito esperado na memória de cálculo e no valor final,
depois removidos do banco para não contaminar a projeção real.

---

## 5. Etapa 3 — Tela "Fechamento 2026"

### 5.1 Objetivo

Expor o motor de projeção como uma tela interativa dentro do próprio app Streamlit, no mesmo
padrão visual das telas existentes.

### 5.2 Arquivos criados/alterados

- **`core/projecao_engine.py`** (estendido): funções de acesso para a UI —
  `carregar_resultado()`, `carregar_configs()`, `salvar_config_conta()`,
  `remover_config_conta()`, `carregar_parametros()`, `salvar_parametro()`.
- **`core/tabela_html.py`** (estendido): nova função `gerar_html_fechamento()` — tabela HTML
  colapsável Natureza > Conta, com colunas Método/Orçamento/YTD/Fechamento M3/% Exec/Conferência
  M2/Divergência/Confiança, e destaques visuais automáticos (percentual de execução acima de
  100% em vermelho, divergência material em âmbar, confiança por cor).
- **`pages/fechamento.py`** (novo): a tela completa —
  cabeçalho com data de geração e mês de corte detectado, botão "Recalcular", 4 métricas gerais,
  tabela hierárquica com filtros ("só divergências materiais", "só confiança baixa"), expander de
  parâmetros globais de Pessoal, e um bloco de configuração por conta (seleciona a conta, mostra
  memória de cálculo, permite trocar o método entre Automático/Run-rate/Sazonal/Override e
  salvar — o que dispara recálculo automático do motor).
- **`Home.py`** (alterado): nova entrada de menu "🎯 Fechamento 2026", adicionada à navegação.

### 5.3 Bug pré-existente encontrado e corrigido

Ao testar a página com `streamlit.testing.v1.AppTest` (execução headless, sem navegador),
apareceu o erro `AttributeError: module 'streamlit' has no attribute 'iframe'`. Investigação
mostrou que **as 4 páginas originais do app** (`projecao.py`, `resumo.py`, `pca.py`,
`memoria.py`) chamavam `st.iframe(...)` — método que **não existe** na versão do Streamlit
efetivamente instalada no ambiente (1.49.1). Ou seja: **essas quatro telas do app original
quebrariam por completo ao serem abertas**, um bug pré-existente que não tinha sido percebido
antes porque ninguém havia rodado o app neste ambiente. Corrigido substituindo todas as
ocorrências por `streamlit.components.v1.html(..., scrolling=True)` — a API correta e
equivalente. As 4 páginas foram re-testadas headless e confirmadas funcionando; mais tarde,
também confirmadas visualmente no navegador (seção 9).

### 5.4 Verificação

Testada via `AppTest`: renderização da página, troca de conta no seletor, aplicação dos filtros
de divergência/confiança — tudo sem exceções.

---

## 6. Etapa 4 — Exportações (Excel e PDF)

### 6.1 Objetivo

Permitir levar a projeção para fora do sistema — reuniões, auditoria, arquivamento — com o mesmo
nível de detalhe (incluindo a memória de cálculo por conta) disponível na tela.

### 6.2 Arquivo alterado: `core/exportar.py`

- **`gerar_excel_fechamento()`**: workbook com 2 abas —
  `Resumo` (por natureza: nº de contas, orçamento, realizado, fechamento M3, % execução,
  conferência M2, com linha TOTAL) e `Detalhe` (as N contas, com método, confiança, divergência e
  a **memória de cálculo completa** de cada uma — o texto exato usado pelo motor, não um resumo).
  Formatação real de planilha via `openpyxl`: título, cabeçalho colorido, larguras de coluna,
  formato numérico (`#,##0.00` / `0.0%`), painel congelado.
- **`gerar_pdf_fechamento()`**: PDF A4 paisagem via `reportlab` — resumo por natureza, parágrafo
  de "pontos de atenção" (contagem de divergências materiais e de contas de confiança baixa),
  tabela detalhada por conta com marcadores `*` (divergência) e `‡` (confiança baixa).
- **`pages/fechamento.py`** (alterado): dois botões novos, gravando em `data/exportados/` e
  oferecendo download.

### 6.3 Verificação

Excel e PDF gerados e conferidos por script: totais do Excel batem com o banco ao centavo, texto
do PDF extraído e validado com `pypdf` (biblioteca usada só para verificação, não é dependência de
runtime do app). Clique do botão de exportação testado headless via `AppTest`. Um PDF de exemplo
foi entregue ao usuário para inspeção.

---

## 7. Fase 2 — Receita

### 7.1 Objetivo

Estender o mesmo motor, já validado para despesa, ao ramo `6.2` (receita) — sem duplicar código,
reaproveitando a mesma infraestrutura de dados (o importador já havia trazido os dados de receita
desde a Etapa 1, mesmo sem uso até aqui).

### 7.2 Mudanças no motor (`core/projecao_engine.py`)

- **Parâmetro `ramo`** adicionado a `_carregar_dados()` e `projetar_fechamento()`: o sinal do
  executado se inverte conforme o ramo (`D−C` despesa, `C−D` receita — a mesma regra validada na
  Etapa 1, agora parametrizada em vez de fixa).
- **7 novas naturezas de receita** (`natureza_da_conta()` estendida): Cota-Parte dos CRCs
  (`6.2.1.1.02`), Demais Contribuições (`6.2.1.1.*`), Exploração de Bens e Serviços (`6.2.1.2`),
  Receitas Financeiras (`6.2.1.3`), Outras Receitas (`6.2.1.9`), Receitas de Capital (`6.2.2`),
  Previsão Adicional (`6.2.3`).
- **Novo método `ytd`**: para a conta de **Previsão Adicional** — uma conta de equilíbrio
  orçamentário (R$ 25,9 mi orçados) que **nunca realiza** por desenho contábil. Sem esse
  tratamento especial, o motor teria tentado projetar 90% desse valor pelo fallback padrão — um
  erro grosseiro. Com o método `ytd`, o fechamento é simplesmente o realizado acumulado (zero),
  sem tentar projetar o que não vai acontecer.
- **Persistência por ramo**: `projecao_resultado` (e depois `projecao_mensal`) filtram e apagam
  só o ramo recalculado, permitindo que despesa e receita coexistam no mesmo banco sem se
  sobrescrever.

### 7.3 Mudanças na tela (`pages/fechamento.py`)

- Seletor "Despesa (6.3) / Receita (6.2)" no topo.
- Lógica de alerta de % de execução **invertida** para receita: no lado da despesa, o risco é
  estourar o orçamento (alerta se M3 > 100%); no lado da receita, o risco é **frustrar** a
  arrecadação (alerta se M3 < 100%) — a mesma cor vermelha significando o oposto conforme o ramo,
  documentado explicitamente no código para não confundir quem ler depois.
- **Resultado orçamentário projetado** (Receita − Despesa): aparece automaticamente quando os
  dois ramos já têm projeção persistida.
- Expander de reajuste de Pessoal escondido no ramo receita (não se aplica).

### 7.4 Mudanças nas exportações e no CLI

`projetar_fechamento.py --ramo 6.2`; nomes de arquivo e títulos de Excel/PDF passaram a incluir o
rótulo do ramo (`Fechamento2026_Despesa_*` / `Fechamento2026_Receita_*`).

### 7.5 Resultado da primeira projeção de receita (corte maio/2026)

| Natureza | Orçamento | Fechamento M3 | % |
|---|---:|---:|---:|
| Cota-Parte dos CRCs | 70,3 mi | 70,6 mi | 100,4% |
| Receitas Financeiras | 19,3 mi | 20,0 mi | 103,7% |
| Exploração de Bens e Serviços | 15,0 mi | 15,1 mi | 100,8% |
| Demais Contribuições | 0 | 5,5 mi | — |
| Receitas de Capital | 1,9 mi | 0,6 mi | 33,0% |
| Outras Receitas | 0,1 mi | 0,05 mi | 59,0% |
| Previsão Adicional | 25,9 mi | 0 | 0,0% |
| **TOTAL** | **132,6 mi** | **111,9 mi** | **84,4%** |

**Resultado orçamentário projetado 2026: Receita R$ 111,93 mi − Despesa R$ 113,04 mi = déficit de
~R$ 1,1 milhão** (a conferência M2 aponta receita de R$ 113,0 mi — praticamente equilíbrio). Nota
importante: a frustração aparente de receita é quase toda explicada pela Previsão Adicional (conta
de equilíbrio que nunca realiza); a receita "operacional" projeta acima do orçado.

Achados: 6 divergências materiais (majoritariamente amortizações de empréstimos de CRCs com
padrão de pagamento irregular — BA/PI/RS projetando zero pelo run-rate, mas com histórico de
pagamento concentrado no 2º semestre) e a rubrica "Demais Contribuições" (Fundo de Integração)
realizando ~R$ 5,5 mi sem ter orçamento algum alocado.

### 7.6 Verificação

CLI dos dois ramos, coexistência confirmada no banco (`SELECT` filtrado por prefixo de conta),
tela testada nos dois ramos via `AppTest`, exportações de receita conferidas (Excel ao centavo,
PDF validado).

---

## 8. Curva mensal de desembolso/arrecadação

### 8.1 Objetivo

Ir além do número anual único: mostrar a projeção **mês a mês**, com o realizado (Diário) e o
projetado (motor) lado a lado, para acompanhar o fluxo de caixa ao longo do ano — não só o total
de dezembro.

### 8.2 Mudanças no modelo de dados

- **Nova tabela `projecao_mensal`**: `(conselho, ano, conta, mes) → valor, projetado (0/1)`.
  Persistida junto com `projecao_resultado` a cada recálculo: meses ≤ corte vêm direto do Diário
  real, meses > corte vêm de `restante_por_mes` (a distribuição mensal calculada internamente
  pelo motor, que já existia como estrutura intermediária mas não era salva antes).
- **Refinamento do override manual**: antes, o override só definia o valor anual total; agora o
  residual (fechamento − YTD) é distribuído pelos meses restantes seguindo o perfil sazonal
  histórico da própria conta (ou uniformemente, se não houver perfil) — necessário para que a
  curva mensal também faça sentido em contas configuradas manualmente.
- Consistência verificada por script: a soma de `projecao_mensal` por conta bate com
  `proj_fechamento` **ao centavo**, em todas as contas, nos dois ramos.

### 8.3 Mudanças na visualização

- **`core/tabela_html.py`**: nova função `gerar_html_curva_mensal()` — matriz Natureza/Conta ×
  Jan-Dez + Total, meses projetados com cabeçalho destacado e marcador `*`.
- **`pages/fechamento.py`**: nova seção "Curva mensal de desembolso/arrecadação" —
  - Gráfico de barras (Altair): Realizado vs. Projetado, com paleta de cores **formalmente
    validada** para acessibilidade (script `validate_palette.js` do skill de visualização de
    dados: banda de luminosidade, piso de croma, separação para daltonismo ΔE 18-20, contraste —
    todos os critérios em PASS) — azul escuro `#2d5fa8` para realizado, azul-petróleo `#3fa0c8`
    para projetado. Tooltip por barra (mês, tipo, valor).
  - Seletor de natureza: "(Todas)" mostra o gráfico agregado + matriz por natureza; selecionar
    uma natureza detalha a matriz por conta dentro dela.
  - Rótulo adaptado ao ramo: "desembolso" (despesa) / "arrecadação" (receita).
- **Exportações**: Excel ganhou nova aba "Curva Mensal" (conta × mês + total, meses projetados
  com cabeçalho `Mês*`); PDF ganhou nova tabela "Curva mensal por natureza" (valores em R$ mil).
- **`requirements.txt`**: adicionado `altair>=5.0` (já vinha embutido no Streamlit, mas passou a
  ser dependência direta e explícita, já que o código a importa diretamente).

### 8.4 Bug real encontrado na verificação visual (não apenas headless)

Ao abrir a tela de verdade em um navegador (não só testes automatizados sem interface), o quadro
"Resultado orçamentário projetado" (da Fase 2, seção 7.3) aparecia com formatação quebrada:
parte do texto saía em itálico serifado, como se fosse uma fórmula matemática.

**Causa raiz**: a string tinha **três** ocorrências de "R$" na mesma chamada `st.info(...)`, que
renderiza o texto como Markdown. O Streamlit interpreta pares de `$` como delimitadores de LaTeX
(KaTeX) — com 3 cifrões, o primeiro par (1º e 2º `$`) foi lido como "abra e feche uma fórmula",
fazendo o trecho entre eles (o valor da receita) renderizar em modo matemático em vez de texto
normal.

**Correção**: escapado o cifrão (`R\$`) nas 3 ocorrências em `pages/fechamento.py`. Verificado que
nenhuma outra chamada `st.info/success/warning/error` do app tinha mais de um "R$" na mesma
string (o risco não se repete em outro lugar do código). Recarregado no navegador após a correção
— confirmado que o texto volta a renderizar normalmente.

Esse achado reforça por que a verificação visual em navegador (além dos testes automatizados
headless) faz parte do processo: bugs de renderização de Markdown/HTML só aparecem visualmente,
nunca em um teste que só checa "não lançou exceção".

### 8.5 Verificação

Consistência curva↔fechamento por script, teste específico de override com a nova distribuição
mensal do residual, tela testada nos dois ramos via `AppTest`, exportações com a nova aba/tabela
conferidas (Excel e PDF), e inspeção visual completa no navegador — incluindo o tooltip do
gráfico e a correção do bug acima.

---

## 9. Execução da aplicação e verificação final em navegador

Depois de toda a implementação, a aplicação foi efetivamente **executada** (não só testada) via
`streamlit run Home.py`, e navegada com automação de navegador (Chrome) para confirmar em
condição real:

- Tela **Início**: menu completo, status dos arquivos de dados.
- Tela **🎯 Fechamento 2026**: métricas, seletor Despesa/Receita, quadro de resultado
  orçamentário consolidado — confirmando ao vivo a correção do bug da seção 8.4.
- Tela **📈 Projeção Orçamento 2026** (a tela original do app, ainda com os dados de teste
  "COORDENADORIA TESTE" em `bases.xlsx`/`orcamento2026.db`, que não foram tocados): confirmando ao
  vivo a correção do bug `st.iframe` da seção 5.3 — sem essa correção, essa tela travaria ao
  abrir.

O servidor foi deixado rodando (porta 8577) para uso do usuário.

---

## 10. A mudança dos "arquivos base" — antes e depois, lado a lado

Esta seção responde diretamente à pergunta "a mudança dos arquivos base para o que temos agora":

### 10.1 O que existia antes (e continua existindo, intocado)

```
data/bases.xlsx              — abas fixas do app ORIGINAL (dados 100% de teste)
data/orcamento_historico.xlsx — histórico fixo do app ORIGINAL (3 linhas de teste)
data/orcamento2026.db         — SQLite "vivo" do app ORIGINAL (7 lançamentos de teste)
```

Esses três arquivos **não foram apagados nem alterados** — continuam existindo e alimentando as
telas originais (`Projeção Orçamento 2026`, `Resumo`, `Memória de Cálculo`, `PCA 2026`), que
seguem funcionando exatamente como antes (com os dados de teste, até que alguém substitua o
conteúdo desses arquivos pelos dados reais da entidade — o que está fora do escopo deste trabalho,
que seguiu por um caminho paralelo). Essa decisão foi deliberada (ver seção 2.1: "estrutura
paralela"): minimizar o risco de quebrar o que já funcionava.

### 10.2 O que foi criado, alimentado por dados reais

```
DECONT/Códigos/*.csv          — fonte: dados abertos oficiais da API do CFC (27 conselhos,
                                 2021/2022-2026), já existente no computador do usuário,
                                 descoberta e incorporada durante este projeto
        │
        ▼ importar_dados.py (novo)
data/dados_reais.db            — NOVO banco SQLite, ~2,5 MB, só CFC, com:
  orcamento_anual (1.092 linhas)       — orçamento inicial + realizado, todos os níveis, 2022-2026
  execucao_mensal (18.198 linhas)      — Diário agregado por conta × mês, todas as classes
  plano_contas_real (3.195 linhas)     — plano de contas completo com hierarquia de grupos
  reconciliacao (597 linhas)           — conferência executado × realizado, 2022-2025
  importacao_meta                      — metadados de cada importação (datas, mês de corte)
        │
        ▼ core/projecao_engine.py (novo)
  projecao_config      — overrides e reajustes manuais por conta
  projecao_parametros  — parâmetros globais (reajuste de data-base do Pessoal)
  projecao_resultado (136 linhas: 92 despesa + 44 receita) — resultado de cada projeção
  projecao_mensal (1.632 linhas: 136 contas × 12 meses)    — curva mensal realizado+projetado
```

### 10.3 Por que dois bancos separados, e não um só

`orcamento2026.db` (antigo) representa **lançamentos manuais digitados por um usuário** através
dos formulários do app — é uma fonte primária de dados, editável pela interface.
`dados_reais.db` (novo) representa **dados oficiais importados de uma API externa** — é uma
réplica derivada, regenerável a qualquer momento rodando `importar_dados.py` de novo (o processo
inteiro leva ~10 segundos). Misturar os dois no mesmo schema criaria ambiguidade sobre qual dado
é "fonte da verdade" e complicaria a lógica de exclusão/atualização. Mantê-los separados também
significa que uma reimportação futura dos dados reais **nunca** apaga ou sobrescreve lançamentos
manuais feitos pelo usuário no sistema antigo.

### 10.4 Como atualizar os dados reais no futuro

```bash
# 1. Rodar os scripts de download DE DENTRO de cada subpasta (eles salvam no
#    diretório atual, com o nome que o importador espera):
cd DECONT/Códigos/Diário               && python ../baixar_diario.py
cd DECONT/Códigos/OrçamentoAtualizado  && python ../baixar_orçamentoatualizado.py

# 2. Reimportar (na pasta orcamento_app):
python importar_dados.py

# 3. Recalcular a projeção (ou simplesmente abrir a tela e clicar em "Recalcular"):
python projetar_fechamento.py --ramo 6.3
python projetar_fechamento.py --ramo 6.2
```

Este procedimento foi de fato executado pela primeira vez em 26/07/2026 (seção
17) — ver lá os dois problemas reais que apareceram na prática (um bug no
script de download e uma falha de rede pontual que quase causou perda
silenciosa de dados) e como foram detectados e corrigidos.

---

## 11. Arquivos novos criados (lista consolidada)

| Arquivo | Papel |
|---|---|
| `Orcamento2026.md` | Documentação viva de referência do projeto (16 seções, atualizada a cada etapa) |
| `orcamento_app/core/dados_reais.py` | Importador dos CSVs da API do CFC para `dados_reais.db`, com reconciliação |
| `orcamento_app/importar_dados.py` | CLI do importador |
| `orcamento_app/core/projecao_engine.py` | Motor de projeção (M3 híbrido + M2 conferência), despesa e receita |
| `orcamento_app/projetar_fechamento.py` | CLI do motor de projeção |
| `orcamento_app/pages/fechamento.py` | Tela "Fechamento 2026" (métricas, tabela, curva mensal, configuração, exportação) |
| `Relatorio_Projecao_Despesa_2026.md` | Este relatório — detalhamento por conta contábil (gerado agora) |
| `Relatorio_Evolucao_Projeto.md` | Este documento |

## 12. Arquivos existentes alterados

| Arquivo | O que mudou |
|---|---|
| `core/config.py` | + `CODIGOS_DIR`, `DADOS_REAIS_DB`, `CONSELHO_PADRAO` |
| `core/tabela_html.py` | + `gerar_html_fechamento()`, + `gerar_html_curva_mensal()` |
| `core/exportar.py` | + `gerar_excel_fechamento()`, + `gerar_pdf_fechamento()` (despesa/receita, com curva mensal) |
| `Home.py` | + entrada de menu "Fechamento 2026" |
| `pages/projecao.py`, `pages/resumo.py`, `pages/pca.py`, `pages/memoria.py` | Correção do bug `st.iframe` → `streamlit.components.v1.html` |
| `requirements.txt` | + `altair>=5.0` |
| `Home.py` | Navegação reduzida a Início + Fechamento 2026 (as 4 telas antigas removidas do menu, seção 15) |
| `core/dados_reais.py` | `importar_plano_contas()` tolerante à ausência de `grupo2/3/4` (seção 17.6) |
| `DECONT/Códigos/baixar_diario.py` | Anos `[2022,2023,2024]` → `[...,2025,2026]`; nome de saída `lancamentos_{ano}.csv` → `Diario_{ano}.csv` (seção 17.1) |
| `DECONT/Códigos/baixar_plano_contas.py` | Anos `[2021..2024]` → `[...,2025,2026]`; nome de saída `plano_contas_2021_2024.csv` → `PlanoContas_2021_2024.csv` (seção 17.5) |

## 13. Bugs reais encontrados e corrigidos (não hipotéticos — todos confirmados em execução)

1. **`st.iframe` inexistente** (seção 5.3): as 4 telas originais do app quebrariam ao abrir nesta
   versão do Streamlit (1.49.1). Encontrado via teste automatizado headless. Corrigido em todas.
2. **`R$` interpretado como LaTeX** (seção 8.4): o quadro de resultado orçamentário renderizava
   com formatação quebrada. Encontrado via inspeção visual em navegador (não seria pego por
   testes headless, que só checam ausência de exceção). Corrigido escapando o cifrão.
3. **`baixar_diario.py` desatualizado** (seção 17.1): não buscava 2025/2026 e salvava com nome
   incompatível com o importador. Encontrado por inspeção do script antes de instruir a
   atualização. Corrigido.
4. **Falha SSL isolada em CFC/2022, com risco de perda silenciosa de dados** (seção 17.2): 1 de
   135 requisições falhou; como o script grava um CSV por ano com só quem respondeu, isso teria
   zerado o CFC inteiro de 2022 sem travar a execução nem gerar um arquivo obviamente quebrado.
   Encontrado por inspeção do log antes de reimportar. Corrigido com um script avulso de mescla,
   validado contra a contagem original.
5. **`baixar_plano_contas.py` desatualizado** (seção 17.5): mesma classe de bug do item 3 (anos +
   nome de arquivo). Corrigido.
6. **`KeyError` em `importar_plano_contas()` por hierarquia de grupos inexistente na API** (seção
   17.6): a API `planoContas` nunca devolveu `grupo2/3/4` — o arquivo antigo com esses campos
   veio de outro processo, não deste script. Encontrado ao reimportar após corrigir o item 5.
   Corrigido tornando o importador tolerante (preenche `None`), aceitando a perda dessa
   informação de referência (não usada em nenhum cálculo).

## 14. O que ficou fora do escopo (deliberadamente)

- Migrar `bases.xlsx`/`orcamento_historico.xlsx`/`orcamento2026.db` (dados de teste) para dados
  reais — o caminho escolhido foi um sistema paralelo alimentado pela API, não a substituição do
  sistema de lançamento manual existente.
- Dimensão Projeto/SubProjeto na projeção (decisão explícita da seção 2.4 — exigiria extração
  interna do SPW).
- Proposta Orçamentária 2027 — o escopo foi deliberadamente limitado ao fechamento de 2026
  (decisão explícita da seção 2.4).
- Cenários (otimista/conservador/pessimista) e visão de cota-parte por CRC individual — mencionados
  como possíveis próximos passos, ainda não implementados.

---

## 15. Simplificação do menu e confirmação da independência dos dois trilhos

### 15.1 Pergunta do usuário e verificação técnica

Depois da Fase 2 e da curva mensal, o usuário perguntou se só precisava das telas **Início** e
**Fechamento 2026** — e, em seguida, qual era a relação das outras quatro telas (`Projeção
Orçamento 2026`, `Resumo`, `Memória de Cálculo`, `PCA 2026`) com o **cálculo** da projeção.

A resposta não foi por suposição — foi verificada diretamente no código, inspecionando os
`import` de cada módulo:

- `core/projecao_engine.py` importa só `dataclasses, datetime, json, sqlite3, pandas` e
  `core.config` (`DADOS_REAIS_DB, CONSELHO_PADRAO, ANO_ORCAMENTO`). Nenhum import de
  `core.loaders`, `core.db`, `core.agregacao` ou `core.calculos` — os módulos que sustentam as
  quatro telas antigas.
- `pages/fechamento.py` importa `core.exportar`, `core.projecao_engine`, `core.config`,
  `core.formatos`, `core.tabela_html` — de novo, nenhum dos módulos legados.
- `core/exportar.py` importa só `core.config` e `core.formatos` (além das bibliotecas de
  terceiros `pandas`/`reportlab`/`openpyxl`).

Conclusão confirmada por inspeção, não por suposição: **relação zero**. As quatro telas antigas
rodam sobre `bases.xlsx` + `orcamento_historico.xlsx` + `orcamento2026.db` (dados de teste,
lançamento manual); o motor de projeção roda exclusivamente sobre `dados_reais.db` (dados reais da
API). Nenhuma gravação feita por uma tela afeta a outra, em nenhuma direção.

### 15.2 Remoção das 4 telas do menu

Com a relação zero confirmada, o usuário pediu a remoção das quatro telas do menu de navegação.
Alterado `Home.py`:
- Removidos os 4 `st.Page(...)` (`projecao`, `resumo`, `memoria`, `pca`) da lista passada a
  `st.navigation([...])` — mantidos só `inicio` e `fechamento`.
- Atualizado o texto de `pagina_inicio()`, que citava as telas removidas pelo nome (ficaria
  desatualizado/confuso apontar para itens de menu que não existem mais).
- Adicionado um comentário no código explicando a decisão e apontando para esta seção do
  raciocínio (relação zero com o motor de projeção), para quem for mexer no arquivo depois.

Os arquivos das 4 telas (`pages/projecao.py`, `pages/resumo.py`, `pages/memoria.py`,
`pages/pca.py`) e os módulos que elas usam (`core/agregacao.py`, `core/db.py`, `core/loaders.py`,
`core/calculos.py`, `core/dialogs.py`, `core/forms_diarias.py`, `core/forms_despesas.py`) **não
foram apagados** — só removidos da navegação, ação reversível a qualquer momento bastando
readicioná-los à lista de `st.navigation`.

Verificação: `Home.py` re-testado headless via `AppTest` (sem exceções, título correto) e
confirmado visualmente no navegador — o menu passou a mostrar só Início e Fechamento 2026.

## 16. Estado final — visão de conjunto

O sistema hoje opera em dois trilhos paralelos e independentes:

1. **Trilho original** (lançamento manual): `bases.xlsx` + `orcamento_historico.xlsx` +
   `orcamento2026.db` → telas `Projeção`/`Resumo`/`Memória`/`PCA` — inalterado, ainda com dados
   de teste. Os arquivos e o código continuam no projeto, mas as 4 telas foram **removidas do
   menu de navegação** (`Home.py`), por não terem nenhuma relação de dados com o motor de
   projeção (seção 15).
2. **Trilho novo** (projeção baseada em API real): `DECONT/Códigos/*.csv` → `importar_dados.py` →
   `dados_reais.db` → `projecao_engine.py` → tela `Fechamento 2026` → exportações Excel/PDF —
   cobre despesa e receita, com modelo híbrido de projeção, conferência estatística cruzada,
   curva mensal, e é o objeto deste relatório. É hoje o **único item de menu** além de Início.

Os dois trilhos compartilham a mesma aplicação Streamlit (`Home.py`) e o mesmo padrão de código
(`core/formatos.py`, `core/tabela_html.py`), mas não compartilham dados nem schema de banco —
por desenho, para isolar risco.

---

## 17. Primeira atualização operacional de dados — Jun/2026 (26/07/2026)

Até este ponto, o pipeline de atualização (baixar → reimportar → recalcular, seção 10.4) só
tinha sido **projetado e testado uma vez** (a importação inicial, seção 3.3, com dados até
17/06/2026). O usuário pediu a primeira atualização real, para trazer o mês de junho completo e
gerar uma nova projeção — e essa execução revelou dois problemas reais que só apareceriam em uso
de produção, não em nenhum teste anterior.

### 17.1 Bug encontrado antes de rodar: `baixar_diario.py` desatualizado

Ao revisar o script antes de instruir o usuário, ficou claro que `DECONT/Códigos/baixar_diario.py`
estava **dessincronizado** do resto do pipeline:
- `anos = [2022, 2023, 2024]` — não buscava 2025 nem 2026.
- Salvava como `lancamentos_{ano}.csv` — nome diferente do que `core/dados_reais.py` espera
  (`Diario_{ano}.csv`).

Ou seja: os arquivos `Diario_2025.csv`/`Diario_2026.csv` que já existiam na pasta **não foram
gerados por esta versão do script** — vieram de uma execução anterior (manual ou de uma versão
diferente). Se o usuário tivesse rodado o script do jeito que estava, ele não traria dado nenhum
de 2026, e ainda salvaria no lugar/nome errado. Corrigido antes de qualquer execução: `anos =
[2022, 2023, 2024, 2025, 2026]` e `nome_arquivo = f"Diario_{ano}.csv"`.

### 17.2 Incidente durante a execução: falha SSL isolada, risco de perda silenciosa de dados

Com o script corrigido, o download rodou 135 requisições (27 conselhos × 5 anos) contra a API do
CFC. **1 única requisição falhou**: `CFC - 2022`, com
`SSLCertVerificationError: self-signed certificate in certificate chain`. As outras 134 — inclusive
CFC nos outros 4 anos, na mesma sessão HTTP — tiveram sucesso, o que aponta para uma falha de rede
pontual (não um problema real do certificado do servidor, que se mostrou íntegro no resto das
chamadas).

**Por que isso era perigoso, especificamente**: o script grava **um único CSV por ano**, contendo
todos os conselhos que responderam com sucesso naquele ano. Como só o CFC falhou em 2022 (as
outras 26 CRCs foram buscadas normalmente), o `Diario_2022.csv` foi regravado **sem nenhuma linha
de CFC** — 759.571 linhas, mas 0 do conselho que interessa a este projeto. O script não trata isso
como erro fatal (ele imprime "Erro em CFC - 2022: ..." e segue adiante, terminando com "Arquivo CSV
gerado com sucesso" no fim) — ou seja, **a falha fica visível só no log, não impede a execução
nem gera um arquivo obviamente quebrado**. Se esse CSV tivesse sido importado direto, a
reconciliação de 2022 (que hoje bate 91-95 contas/ano) teria caído para 0 batendo — um sinal de
alarme claro, mas só depois de já ter sobrescrito o dado bom.

Esse é exatamente o tipo de falha que a etapa de reconciliação automática (seção 3.2,
`reconciliar()`) foi desenhada para pegar — mas neste caso foi pega **antes** de reimportar, por
inspeção direta do log de download (`grep` por "Erro em") e comparação de contagem de linhas do
CSV recém-baixado contra a expectativa.

**Correção aplicada**: em vez de repetir as 135 requisições (arriscando a mesma falha pontual de
novo, ou uma nova, em qualquer uma das outras 134), foi escrito um script avulso e descartável que
buscou só `conselho=CFC, ano=2022` na mesma API e mesclou o resultado de volta no
`Diario_2022.csv` existente (que já tinha as outras 26 CRCs corretas). O resultado bateu
**exatamente** com a contagem original de referência (52.309 linhas de CFC, 811.880 linhas totais)
— confirmando que nada mais tinha sido perdido ou duplicado.

### 17.3 Resultado da reimportação e do recálculo

- `python importar_dados.py`: reconciliação 2022-2025 **100%** de novo (a correção da seção 17.2
  evitou o que seria uma quebra total da reconciliação de 2022).
- O Diário de 2026 cresceu de 320.751 para **401.277 linhas** (37.821 de CFC) — dado agora vai até
  **21/07/2026**, cobrindo junho inteiro. Como julho está parcial (dia 21 < 28), o motor manteve o
  corte em maio→**junho** automaticamente (a mesma lógica de `mes_corte_padrao()` descrita na
  seção 4.2, sem qualquer intervenção manual).
- Projeção recalculada nos dois ramos, com resultado comparado ao da rodada anterior (maio):

| | Orçamento | YTD | Fechamento M3 | % |
|---|---:|---:|---:|---:|
| Despesa (corte maio) | 132,6 mi | 39,6 mi | 113,0 mi | 85,3% |
| Despesa (corte **junho**) | 132,6 mi | 47,9 mi | **110,1 mi** | 83,0% |
| Receita (corte maio) | 132,6 mi | 66,9 mi | 111,9 mi | 84,4% |
| Receita (corte **junho**) | 132,6 mi | 73,5 mi | **112,2 mi** | 84,6% |

**Resultado orçamentário projetado inverteu de sinal**: de um déficit de ~R$ 1,1 milhão (dados até
maio) para um **superávit de ~R$ 2,10 milhões** (dados até junho) — uma variação de ~R$ 3,2
milhões na leitura do fechamento do ano, causada por um único mês adicional de execução real.
Isso demonstra na prática por que a ferramenta foi desenhada para ser recalculada a cada
atualização de dados (o "Recalcular" da tela, ou o CLI) em vez de ser tratada como um número fixo
— a cada mês fechado, a base estatística do modelo sazonal e do run-rate muda, e o resultado pode
se mover de forma material.

Consistência pós-recálculo conferida por script (soma da curva mensal por conta = fechamento
projetado, ao centavo, nos dois ramos) — sem regressão em relação às verificações da seção 8.5.

### 17.4 Lição de processo para as próximas atualizações

Antes de rodar `python importar_dados.py` depois de um novo download, vale conferir o log do
`baixar_diario.py`/`baixar_orçamentoatualizado.py` por linhas `Erro em` — uma falha isolada não
impede o script de "terminar com sucesso" nem produz um arquivo obviamente corrompido; ela só
reduz silenciosamente a cobertura daquele ano/conselho. A reconciliação automática (seção 3.2)
pegaria o problema depois, mas checar o log antes é mais barato do que descobrir depois de já ter
sobrescrito o CSV bom.

### 17.5 Mesmo bug encontrado no quarto script: `baixar_plano_contas.py`

Depois de documentar o incidente acima, o usuário pediu para verificar o script irmão de plano de
contas — e ele tinha **exatamente a mesma classe de bug** do `baixar_diario.py` (seção 17.1):
`anos = [2021, 2022, 2023, 2024]` (sem 2025/2026) e salvava como
`plano_contas_2021_2024.csv` (minúsculo, com underscore), enquanto `core/dados_reais.py` espera
`PlanoContas_2021_2024.csv` (PascalCase). Ou seja: **3 dos 4 scripts de download** da pasta
`DECONT/Códigos` tinham o mesmo tipo de dessincronia entre o que o script produz e o que o
importador espera — um padrão recorrente que vale ter em mente ao revisar `baixar_saldoinicial.py`
(o quarto script, ainda não auditado) antes de usá-lo.

Corrigido da mesma forma: `anos` estendido até 2026; nome do arquivo de saída ajustado para
`PlanoContas_2021_2024.csv` — mantendo esse nome literal (não `..._2021_2026.csv`) mesmo cobrindo
mais anos agora, para não exigir nenhuma mudança em `core/dados_reais.py` (que aponta para um
caminho fixo, não construído a partir do intervalo de anos). Diferença notável em relação ao
`baixar_diario.py`: este script acumula todos os anos/conselhos em memória e grava **um único CSV
no final**, em vez de um arquivo por ano — então uma falha isolada de rede aqui reduziria
silenciosamente a cobertura de um conselho/ano dentro do arquivo combinado, sem exigir a mesma
manobra de mesclagem manual (bastaria rodar de novo só o download, sem risco de perder o restante
dos dados já corretos, já que tudo é escrito de uma vez só ao final).

### 17.6 Download executado — e um terceiro bug real, mais profundo que o anterior

O download rodou limpo (162/162 requisições, 0 erros no log — confirmando que este script, ao
contrário do `baixar_diario.py`, não teve nenhuma falha pontual desta vez). Mas a reimportação
**quebrou**: `KeyError: ['grupo2', 'grupo3', 'grupo4'] not in index`, em
`core/dados_reais.py::importar_plano_contas()`.

Investigação da causa raiz — chamada direta ao endpoint (`GET
.../dadosAbertos/planoContas/`, `conselho=CFC, ano=2026`) — revelou que a **API não retorna
hierarquia de grupos contábeis**. O JSON traz apenas: `ano, numeroConta, nomeConta,
descricaoDetalhadaConta, contaSuperior`. O arquivo `PlanoContas_2021_2024.csv` original (que tinha
colunas "Descrição Grupo 2/3/4", usadas por `core/dados_reais.py` desde a Etapa 1) **não pode ter
sido gerado por este script como está** — precisou vir de outro processo, provavelmente algo como
uma consulta Power Query que resolvia a hierarquia recursivamente subindo a cadeia de
`contaSuperior` (cada conta aponta para sua conta-pai; para saber o "grupo 2", por exemplo, seria
preciso subir a cadeia até o nível certo e buscar o `nomeConta` do ancestral). Esse é o **terceiro**
descompasso real encontrado entre os scripts de `DECONT/Códigos` e o que o pipeline de importação
historicamente recebeu — desta vez não é só nome de arquivo ou intervalo de anos, é uma
**transformação de dados inteira que nunca existiu neste script**.

**Decisão tomada**: não implementar a reconstrução de hierarquia agora. Antes de decidir como
corrigir, foi conferido se `plano_contas_real` é usada em algum cálculo do motor de projeção — não
é (`grep plano_contas_real core/projecao_engine.py` não retorna nada; é uma tabela de referência
carregada mas não consumida, no mesmo padrão da aba `Datas` do sistema original, seção 1.2). Dado
isso, a correção mínima e correta foi tornar `importar_plano_contas()` **tolerante** à ausência dos
campos de grupo — preenche com `None` em vez de assumir que sempre existem:

```python
for col in ("grupo2", "grupo3", "grupo4"):
    if col not in df.columns:
        df[col] = None
```

**Efeito colateral aceito, não corrigido**: as 3.195 contas em `plano_contas_real` perderam o
preenchimento de `grupo2/3/4` (antes existia, agora é `None` em 100% das linhas) — a informação
não é mais capturada por nenhum processo em uso. Sem impacto em nenhum número de projeção. Fica
registrado como débito técnico: se a hierarquia oficial de grupos vier a ser necessária (por
exemplo, se a tela de Fechamento 2026 ganhar uma visão por grupo contábil formal em vez de só por
"natureza" heurística), a reconstrução via `contaSuperior` é o caminho — não implementada por
falta de uso hoje.

Reimportação re-executada após a correção: sucesso, reconciliação 2022-2025 **100%** de novo.
Nenhum recálculo de projeção foi necessário — plano de contas não entra em nenhuma conta de
despesa/receita do motor, só enriquece metadados de referência não utilizados.

**Padrão que se repete**: dos 3 scripts de download auditados até este ponto (`baixar_diario.py`,
`baixar_orçamentoatualizado.py` — que já estava correto —, `baixar_plano_contas.py`), 2 tinham
bugs reais, e o segundo bug encontrado (este) era mais sério que o primeiro (perda de uma
transformação de dados inteira, não só um nome de arquivo). Reforça a recomendação da seção 17.4:
qualquer script de `DECONT/Códigos` que ainda não tenha sido exercitado neste pipeline deve ser
tratado com a mesma suspeita até ser testado de ponta a ponta.

### 17.7 Quarto e último script auditado: `baixar_saldoinicial.py` — o único sem bugs

Pedido do usuário para fechar a auditoria dos 4 scripts: rodar o último que faltava. Diferença
estrutural importante em relação aos outros três — **não alimenta nada em `dados_reais.db`**
(confirmado por `grep` em `core/dados_reais.py`: nenhuma referência a "balanço", "saldo" ou
"Fixas"). Gera `Fixas/balanco_patrimonial_2021.csv`, um saldo patrimonial de abertura (2021),
hoje puramente informativo/desconectado do motor de projeção — nem tem como "quebrar" a
reconciliação ou a projeção, já que nada o lê.

Rodado como estava (`anos = [2021]`, sem alterar nada antes — ao contrário dos dois scripts
anteriores, aqui não havia motivo para suspeitar de bug: o nome de saída
(`balanco_patrimonial_2021.csv`, minúsculo/underscore) já batia exatamente com o arquivo existente
em disco, sem o descompasso de nomenclatura visto em `Diario_*`/`PlanoContas_*`). Resultado:
**27/27 conselhos OK, 0 erros no log** — o único dos 4 downloads, entre todos os já executados
neste projeto, sem nenhuma falha de rede isolada. Estrutura de saída idêntica à original (9.747
linhas, colunas `Ano, Conselho, Conta, Descrição, Saldo`). Conferência de sanidade contábil: para
o CFC, `ATIVO` (conta `1`) = `PASSIVO E PATRIMÔNIO LÍQUIDO` (conta `2`) = R$ 231.973.500,00 —
a identidade fundamental do balanço patrimonial fecha, mais uma evidência de integridade dos
dados vindos da API.

**Fechamento da auditoria dos 4 scripts de `DECONT/Códigos`**:

| Script | Bug encontrado | Ação |
|---|---|---|
| `baixar_diario.py` | Anos desatualizados + nome de arquivo errado | Corrigido (17.1) |
| `baixar_orçamentoatualizado.py` | Nenhum | — |
| `baixar_plano_contas.py` | Anos desatualizados + nome de arquivo errado + campos de hierarquia inexistentes na API | Corrigido (17.5, 17.6) |
| `baixar_saldoinicial.py` | Nenhum | — (mas também não é usado pelo pipeline) |
