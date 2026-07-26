# Ferramenta de Projeção de Orçamento 2026 (CFC) — Documentação do Projeto

> Documento de referência do projeto de evolução do `orcamento_app` para se
> tornar a **Ferramenta de Projeção de Orçamento 2026 do CFC** (despesa
> primeiro, receita em fase posterior), com base nos dados reais da API de
> dados abertos do CFC.
>
> Última atualização: 26/07/2026.

---

## 1. Contexto e objetivo

O app `orcamento_app` (Streamlit) nasceu substituindo as macros VBA da planilha
`Proposta_Orçamentária_2026.xlsb`: lançamento manual de diárias/passagens e
despesas gerais, projeção por Projeto/SubProjeto/Conta, Resumo, Memória de
Cálculo e PCA. Todo o conteúdo de `orcamento_app/data/` era **dado de teste**
(projeto fictício "5008 - PROJETO TESTE").

O objetivo desta evolução é: **projetar de forma confiável como o orçamento de
2026 do CFC vai fechar** (realizado até o momento + projeção dos meses
restantes), por conta contábil, usando os dados reais disponíveis.

Contexto institucional: as reuniões da Proposta Orçamentária 2027 começam após a
Plenária de agosto/2026 (ver `DECONT/Alinhamento PO2027.docx`, que discute o
conceito de "Orçamento Real"). A projeção de fechamento 2026 é insumo natural
desse processo, mas o escopo atual é **somente o fechamento de 2026**.

## 2. Decisões tomadas (jul/2026)

| # | Decisão | Escolha |
|---|---|---|
| 1 | Escopo | **Despesa primeiro**; receita em segundo momento |
| 2 | Modelo de projeção | **Modelo 3 (Híbrido por natureza)** como oficial + **Modelo 2 (run-rate sazonal)** rodando em paralelo como conferência |
| 3 | Objetivo primário | **Projeção de fechamento de 2026** (não PO2027, por ora) |
| 4 | Dimensão de análise | **Por conta contábil** (dados abertos não têm Projeto/SubProjeto; visão por projeto exigiria extração interna do SPW) |
| 5 | Modelagem de dados | **Estrutura paralela** — banco novo `dados_reais.db`, sem tocar nas tabelas/telas existentes do app |

## 3. Fontes de dados reais (`C:\Users\wandney\Documents\DECONT\Códigos`)

Dados baixados da **API de dados abertos do CFC** (sistema SPW,
`https://www3.cfc.org.br/spw/API_SPW/dadosAbertos/...`), pelos scripts Python da
própria pasta (`baixar_diario.py`, `baixar_orçamentoatualizado.py`,
`baixar_plano_contas.py`, `baixar_saldoinicial.py`). Cobrem os 27 conselhos
(CFC + 26 CRCs).

| Arquivo | Conteúdo | Cobertura |
|---|---|---|
| `OrçamentoAtualizado/orcamento_2022_2026.csv` | Orçamento Inicial + Realizado por conta (hierarquia completa, ramos 6.2 receita e 6.3 despesa) | 2022–2026, todos os conselhos |
| `Diário/Diario_2022..2026.csv` | Diário contábil completo (todas as classes 1–8), ~150 MB/ano | CFC: 52–74 mil lançamentos/ano; 2026 até **17/06/2026** |
| `PlanoContas/PlanoContas_2021_2024.csv` | Plano de contas com descrições de grupo (níveis 2, 3 e 4) | 2021–2024 |
| `Fixas/balanco_patrimonial_2021.csv` | Saldos de abertura | 2021 |
| `Fixas/Conselhos.csv` | Cadastro dos 27 conselhos | — |

Números-chave do CFC:

- Orçamento 2026: **R$ 132,58 milhões** (receita = despesa, equilibrado).
- Realizado até ~17/06/2026: receita R$ 69,9 mi · despesa R$ 42,5 mi.
- Taxa de execução da despesa 2025: ~90% (R$ 113,1 mi de R$ 125,8 mi).
- Maiores despesas 2025: Serviços de TI (16,5 mi), Salários (16,0 mi),
  Exames (9,8 mi), Diárias/Passagens de conselheiros e colaboradores (~14 mi),
  INSS (5,2 mi), Subvenções (5,1 mi), Terceirização (4,7 mi).
- Contas folha (nível de lançamento, 11 dígitos): ~92–111 de despesa e ~40–46
  de receita por ano.

## 4. Descobertas técnicas relevantes

1. **Regra do executado — VALIDADA (2025, ano fechado, 100% de conferência):**
   - Despesa (folha 6.3.x): `executado = ΣD − ΣC` — 92/92 contas batem com o
     Realizado oficial (tolerância R$ 0,05).
   - Receita (folha 6.2.x): `realizado = ΣC − ΣD` — 40/40 contas batem.
   - Atenção: aplicar D−C no ramo 6.3 **inteiro** soma zero (níveis sintéticos e
     contas de controle 6.3.9 se compensam). A regra vale **somente nas contas
     folha** (código com 11 dígitos sem pontos).
2. **Os dados abertos não têm Projeto/SubProjeto** — só conta contábil. A visão
   por projeto (usada nas telas antigas do app) exigiria extração interna do SPW.
3. O CSV de orçamento traz **Orçamento Inicial** (não o atualizado por
   suplementações) + Realizado na data do download.
4. O Diário 2026 vai até 17/06/2026; para atualizar, basta rodar novamente os
   scripts `baixar_*.py` da pasta Códigos e reimportar.

## 5. Modelo de projeção adotado

### Motor oficial — Híbrido por natureza (Modelo 3)

| Natureza | Contas | Método |
|---|---|---|
| Pessoal e Encargos | `6.3.1.1.*` (R$ 36 mi) | Quase determinístico: média mensal da folha realizada × meses restantes, 13º/férias nos meses certos, parâmetro de reajuste de data-base |
| Contratos continuados | TI, terceirização, locações, representações etc. | Run-rate: média mensal recente × meses restantes, reajuste opcional por conta |
| Diárias/passagens/eventos | `6.3.1.3.02.03/04.*` e afins | Curva sazonal histórica 2022–2025 (calendário de reuniões/plenárias) |
| Capital | `6.3.2.*` (obras, equipamentos) | Cronograma informado manualmente; realizado acumulado como piso |
| Demais contas | resto de `6.3.*` | Run-rate sazonal |

### Conferência paralela — Run-rate sazonal (Modelo 2)

Para **todas** as contas: `projeção anual = realizado YTD ÷ (% historicamente
executado até o mês de corte)`, usando o perfil mensal médio 2022–2025 da
própria conta. Divergências acima de um limiar entre M3 e M2 são destacadas
para revisão humana.

### Mecanismos de confiabilidade

- Reconciliação automática Diário × Realizado oficial a cada importação.
- Crítica projetado × executado histórico (taxa de execução por conta).
- Toda projeção com memória de cálculo (método, parâmetros, números).
- Overrides manuais sempre registrados e justificados.

## 6. Arquitetura técnica

```
DECONT/Códigos/*.csv  (dados brutos da API — ~630 MB)
        │
        ▼  importar_dados.py (CLI, roda fora do Streamlit)
core/dados_reais.py  ──►  data/dados_reais.db  (SQLite compacto, só CFC agregado)
        │                        │
        │                        ▼  (próximas etapas)
        │                 core/projecao_engine.py  (motor híbrido + conferência)
        │                        │
        ▼                        ▼
  relatório de reconciliação   pages/fechamento_2026.py (tela de projeção)
```

- O app **nunca** lê os CSVs de 630 MB diretamente — só o SQLite agregado.
- `core/dados_reais.py` é independente do Streamlit (roda em linha de comando).
- O banco `orcamento2026.db` (lançamentos manuais do app antigo) permanece
  intocado; `dados_reais.db` é um arquivo separado.

## 7. Esquema do banco `data/dados_reais.db`

| Tabela | Conteúdo | Chave |
|---|---|---|
| `orcamento_anual` | Orçamento Inicial + Realizado por conta/ano (todos os níveis, com flag de folha) | (ano, conselho, conta) |
| `execucao_mensal` | ΣD, ΣC e nº de lançamentos por conta × mês (todas as classes, só CFC) | (ano, mes, conselho, conta) |
| `plano_contas_real` | Plano de contas com grupos (ano mais recente disponível por conta) | (conselho, conta) |
| `reconciliacao` | Executado (Diário) × Realizado (orçamento) por conta folha 6.2/6.3, anos fechados | (ano, conselho, conta) |
| `importacao_meta` | Datas de importação, arquivos, contagens, data máxima do Diário por ano | chave |

## 8. Como executar

```bash
# 1. Importar/atualizar os dados reais (na pasta orcamento_app):
python importar_dados.py                # usa DECONT/Códigos e conselho CFC
python importar_dados.py --conselho CFC --codigos-dir "C:\...\Códigos"

# 2. Rodar o app (telas de projeção virão nas próximas etapas):
streamlit run Home.py
```

Para atualizar os dados da API antes de importar, rodar os scripts `baixar_*.py`
**de dentro da subpasta correspondente** (eles gravam o CSV no diretório atual,
com o nome que o importador espera):

```bash
cd DECONT/Códigos/Diário               && python ../baixar_diario.py
cd DECONT/Códigos/OrçamentoAtualizado  && python ../baixar_orçamentoatualizado.py
```

Depois de baixar, **conferir o log por linhas `Erro em`** antes de rodar
`importar_dados.py` — uma falha isolada de rede não impede o script de
terminar "com sucesso", mas pode deixar o CSV daquele ano sem os dados do
conselho que falhou (ver seção 16 para um caso real disso acontecendo).

## 9. Roadmap e status

- [x] **Etapa 0 — Estudo dos dados** (app de teste, pasta Códigos, validação da regra do executado)
- [x] **Etapa 1 — Importador** (`core/dados_reais.py` + `importar_dados.py`): CSVs → `dados_reais.db`, com reconciliação automática
- [x] **Etapa 2 — Motor de projeção** (`core/projecao_engine.py` + `projetar_fechamento.py`): classificação por natureza, métodos do M3, conferência M2, overrides e reajustes
- [x] **Etapa 3 — Tela "Fechamento 2026"** (`pages/fechamento.py`): tabela hierárquica Natureza > Conta (Orçamento | YTD | Fechamento M3 | % exec | M2 | divergência | confiança), filtros, parâmetros globais de pessoal e configuração por conta (método/reajuste/override com justificativa) direto na interface
- [x] **Etapa 4 — Exportações** (`gerar_excel_fechamento` / `gerar_pdf_fechamento` em `core/exportar.py`, botões na tela): Excel com abas Resumo + Detalhe (incl. memória de cálculo por conta) e PDF A4 paisagem para reunião (resumo por natureza, alertas e detalhe por conta)
- [x] **Fase 2 — Receita**: motor generalizado para o ramo 6.2 (sinal C−D, naturezas próprias, método `ytd` para Previsão Adicional), seletor Despesa/Receita na tela, resultado orçamentário consolidado (Receita − Despesa) e exportações por ramo
- [x] **Curva mensal de desembolso/arrecadação** (seção 15): tabela `projecao_mensal`, gráfico Altair (Realizado × Projetado, paleta validada para acessibilidade), matriz mensal por natureza/conta, aba/tabela extra nas exportações
- [x] **Primeira atualização operacional de dados + auditoria dos 4 scripts de download** (seção 16): dados atualizados até Jun/2026 (corte automático), 2 bugs reais corrigidos (`baixar_diario.py`, `baixar_plano_contas.py`), 1 incidente de perda silenciosa de dados evitado (CFC/2022), 2 scripts confirmados sem problema (`baixar_orçamentoatualizado.py`, `baixar_saldoinicial.py`)

## 10. Resultado da importação (26/07/2026)

Primeira importação executada com sucesso (`python importar_dados.py`, ~10 s):

| Tabela | Linhas | Observação |
|---|---|---|
| `orcamento_anual` | 1.092 | CFC, 2022–2026, todos os níveis |
| `execucao_mensal` | 18.198 | conta × mês, todas as classes, CFC |
| `plano_contas_real` | 3.195 | contas distintas (versão mais recente) |
| `reconciliacao` | 597 | contas folha 6.2/6.3, 2022–2025 |

- Banco gerado: `orcamento_app/data/dados_reais.db` (**2,5 MB** — vs. 630 MB dos CSVs).
- **Reconciliação 2022–2025: 100%** — todas as contas folha de despesa (91–95/ano)
  e receita (40–42/ano) batem com o Realizado oficial (tolerância R$ 0,05).
- **Conferência extra 2026 (ano aberto): bate ao centavo** — despesa executada
  até 17/06 = R$ 42.503.922,95 e receita = R$ 69.876.919,73, idênticos ao CSV
  de orçamento, cruzando apenas as contas orçamentárias (a soma do ramo 6.3
  inteiro do Diário zera por causa das contas de controle 6.3.9 — comportamento
  esperado e documentado na seção 4).
- Mês de corte registrado: `diario_2026_mes_max = 6` (dados até 17/06/2026;
  junho é mês parcial — o motor detecta isso pela `diario_2026_data_max` e usa
  maio como último mês cheio automaticamente).

## 11. Motor de projeção — detalhes e primeira execução (26/07/2026)

### Implementação (`core/projecao_engine.py`)

- **Classificação por natureza** (prefixo da conta, com exceções nomeadas):
  `6.3.1.1`→PESSOAL · `6.3.1.3.02.03/04`→DIÁRIAS_PASSAGENS ·
  `6.3.1.3.02.01`→CONTRATOS (exceto `...011` Exames→EVENTOS) · `6.3.2`→CAPITAL ·
  resto→DEMAIS.
- **Método sazonal** (M2 e maioria do M3): perfil mensal médio 2022–2025 da
  conta; `fechamento = YTD ÷ share_acumulado_até_o_corte`. Cadeia de fallbacks:
  perfil concentrado no fim do ano (ex.: 13º) → método aditivo (média nominal
  2024–2025 dos meses restantes × fator de crescimento do grupo, limitado a
  0,8–1,3); sem histórico → proporcional uniforme; sem histórico e sem YTD →
  orçamento × 90%. Cada caso registra memória de cálculo e confiança
  (alta/média/baixa).
- **Run-rate (contratos)**: média dos últimos 3 meses completos × meses
  restantes, com reajuste opcional (`reajuste_pct`, `mes_reajuste`) por conta.
- **Pessoal**: sazonal + reajuste de data-base global
  (`projecao_parametros`: `pessoal_reajuste_pct`, `pessoal_mes_reajuste`).
- **Overrides manuais** (`projecao_config.parametros_json`):
  `{"override_fechamento": X, "justificativa": "..."}` — obrigatório informar
  justificativa; uso previsto principalmente para CAPITAL (cronogramas).
- **Mês de corte automático**: junho parcial (dados até dia 17) → usa maio.
- Resultados persistidos em `projecao_resultado` (com memória de cálculo por conta).
- Testes executados: override, reajuste de contrato e reajuste de pessoal — OK.

### Primeira projeção (corte: maio/2026)

| Natureza | Orçamento | YTD jan–mai | Fechamento M3 | Conferência M2 | % Exec |
|---|---:|---:|---:|---:|---:|
| Pessoal e Encargos | 36.067.031 | 15.095.847 | 38.515.382 | 38.515.382 | 106,8% |
| Contratos e Serviços | 53.873.729 | 12.074.302 | 35.193.955 | 40.560.450 | 65,3% |
| Diárias e Passagens | 10.712.081 | 7.133.226 | 19.699.534 | 19.699.534 | **183,9%** |
| Eventos e Exames | 13.373.500 | 1.461.550 | 8.214.441 | 8.214.441 | 61,4% |
| Despesas de Capital | 11.417.256 | 1.731.265 | 5.945.261 | 5.945.261 | 52,1% |
| Demais Correntes | 7.135.323 | 2.150.491 | 5.471.819 | 5.471.819 | 76,7% |
| **TOTAL** | **132.578.920** | **39.646.681** | **113.040.392** | **118.406.886** | **85,3%** |

Sinais relevantes da primeira rodada (a validar com a DECONT):

1. **Diárias e Passagens projetam 184% do orçamento** — YTD já é 67% do ano
   com perfil histórico de ~36% até maio. Ou o ritmo de 2026 está muito acima
   do orçado, ou houve mudança de comportamento; item prioritário de análise.
2. **Pessoal fecha em ~107%** do inicial (compatível com crescimento
   vegetativo + data-base; refinável com o parâmetro de reajuste).
3. **15 contas de contratos com divergência M3 × M2 > 10%** — na maioria,
   contratos "grumosos" em que o run-rate de 3 meses difere da curva sazonal
   (ex.: locação de bens móveis: M3 163 mil × M2 3,0 mi). São exatamente os
   casos para revisão humana/override na tela da Etapa 3.
4. **14 contas com confiança baixa** (capital + contas sem histórico) —
   candidatas a override com cronograma.
5. Total M3 (113,0 mi) ≈ realizado de 2025 (113,1 mi); M2 aponta 118,4 mi.

### Como rodar a projeção

```bash
python projetar_fechamento.py                 # resumo por natureza + alertas
python projetar_fechamento.py --detalhe       # memória de cálculo de cada conta
python projetar_fechamento.py --mes-corte 4   # forçar outro mês de corte
```

## 12. Tela "Fechamento 2026" (Etapa 3 — 26/07/2026)

Nova página no menu do app (`streamlit run Home.py` → **🎯 Fechamento 2026**),
implementada em `pages/fechamento.py`:

- **Cabeçalho**: data de geração, mês de corte, botão Recalcular e 4 métricas
  (Orçamento, Realizado YTD, Fechamento M3 com % do orçamento, Conferência M2
  com desvio vs M3).
- **Tabela hierárquica** Natureza > Conta (colapsável, mesmo padrão visual das
  demais telas): Método | Orçamento | Realizado YTD | Fechamento M3 | % Exec |
  Conferência M2 | Divergência | Confiança. Destaques automáticos: % Exec >
  100% em vermelho, divergência material > 10% em âmbar, confiança
  baixa/média/alta em cores.
- **Filtros**: só divergências materiais / só confiança baixa.
- **Parâmetros globais**: reajuste de data-base do Pessoal (%, mês) — salva e
  recalcula na hora.
- **Configuração por conta**: seleção da conta (com métricas e memória de
  cálculo), método Automático/Run-rate/Sazonal/Override; run-rate aceita
  reajuste contratual (%, mês); override exige valor e justificativa
  obrigatória; contas configuradas ganham marcador ⚙️ na lista.
- Qualquer gravação dispara recálculo automático do motor e atualiza a tela.

Verificação: página e interações testadas headless com `streamlit AppTest`
(streamlit 1.49.1) — render, troca de conta, filtros: OK.

**Correção lateral**: as páginas antigas (`projecao.py`, `resumo.py`, `pca.py`,
`memoria.py`) usavam `st.iframe(...)`, que **não existe** no Streamlit 1.49.1
instalado (todas quebrariam ao abrir). Trocado por
`streamlit.components.v1.html(..., scrolling=True)` em todas — as 4 páginas
foram re-testadas headless e estão OK.

## 13. Exportações da projeção (Etapa 4 — 26/07/2026)

Dois botões no rodapé da tabela da tela Fechamento 2026 (funções em
`core/exportar.py`; arquivos gravados em `data/exportados/`):

- **Excel** (`Fechamento2026_AAAAMMDD_HHMM.xlsx`), 2 abas com título, cabeçalho
  formatado, painel congelado e números de verdade (formatos `#,##0.00` / `0.0%`):
  - `Resumo`: por natureza — Nº contas, Orçamento, Realizado YTD, Fechamento
    (M3), % Execução, Conferência (M2) + linha TOTAL;
  - `Detalhe`: as 92 contas com método, confiança, divergência e a **memória de
    cálculo completa** de cada conta (auditabilidade).
- **PDF** (`Fechamento2026_AAAAMMDD_HHMM.pdf`, A4 paisagem, ~5 páginas), para
  distribuição em reunião: resumo por natureza, parágrafo de pontos de atenção
  (nº de divergências materiais e de contas com confiança baixa), detalhe por
  conta com marcadores `*` (divergência) e `‡` (confiança baixa), e nota de
  rodapé apontando para a memória de cálculo no Excel/sistema.

Verificação: ambos gerados e conferidos por script (totais do Excel batem com o
banco ao centavo; texto do PDF extraído e validado com pypdf) e clique do botão
de exportação testado headless via AppTest.

## 14. Fase 2 — Receita (26/07/2026)

O motor foi generalizado para o ramo **6.2 (receita)**, reaproveitando toda a
infraestrutura: mesmos dados (`dados_reais.db`), mesma tela, mesmos exportadores.

### O que mudou

- **Sinal do executado por ramo** (regra validada na reconciliação):
  despesa = ΣD − ΣC · receita = ΣC − ΣD.
- **Naturezas de receita** (classificação por prefixo): Cota-Parte dos CRCs
  (`6.2.1.1.02`, sazonal), Demais Contribuições (`6.2.1.1.*`, sazonal),
  Exploração de Bens e Serviços (`6.2.1.2`, sazonal), Receitas Financeiras
  (`6.2.1.3`, run-rate — juros acompanham o cenário corrente), Outras Receitas
  (`6.2.1.9`, sazonal), Receitas de Capital (`6.2.2`, run-rate — amortizações
  contratuais), **Previsão Adicional** (`6.2.3`, método `ytd`).
- **Método `ytd`** (novo): para a conta de equilíbrio orçamentário (Previsão
  Adicional, R$ 25,9 mi orçados que nunca realizam) — fechamento = realizado
  acumulado, sem projeção e sem conferência M2 (não aplicável).
- **Persistência por ramo**: `projecao_resultado` guarda os dois ramos lado a
  lado; recalcular um não apaga o outro.
- **Tela**: seletor Despesa/Receita no topo; na receita o alerta de % Exec
  inverte (vermelho = projetar **abaixo** do orçamento — frustração de
  receita); o expander de reajuste de Pessoal só aparece na despesa; quando os
  dois ramos têm projeção, aparece o **Resultado orçamentário projetado**
  (Receita − Despesa).
- **CLI**: `python projetar_fechamento.py --ramo 6.2`.
- **Exportações**: `Fechamento2026_Despesa_*.xlsx/pdf` e
  `Fechamento2026_Receita_*.xlsx/pdf` (título e seções por ramo).

### Primeira projeção de receita (corte: maio/2026)

| Natureza | Orçamento | YTD jan–mai | Fechamento M3 | % |
|---|---:|---:|---:|---:|
| Cota-Parte dos CRCs | 70.310.428 | 49.888.891 | 70.612.687 | 100,4% |
| Receitas Financeiras | 19.295.913 | 8.054.988 | 20.012.380 | 103,7% |
| Exploração de Bens e Serviços | 15.022.898 | 7.513.084 | 15.144.906 | 100,8% |
| Demais Contribuições | 0 | 1.150.149 | 5.474.511 | — |
| Receitas de Capital | 1.913.351 | 236.593 | 631.337 | 33,0% |
| Outras Receitas Correntes | 87.410 | 34.953 | 51.532 | 59,0% |
| Previsão Adicional (equilíbrio) | 25.948.920 | 0 | 0 | 0,0% |
| **TOTAL** | **132.578.920** | **66.878.658** | **111.927.353** | **84,4%** |

### Resultado orçamentário projetado 2026

> **Receita R$ 111,93 mi − Despesa R$ 113,04 mi = déficit de ~R$ 1,11 mi**
> (M2 aponta receita R$ 113,02 mi — praticamente equilíbrio). A frustração
> nominal de receita vs orçamento decorre quase toda da Previsão Adicional
> (R$ 25,9 mi que não realizam); a receita "real" projeta acima do orçado.

Sinais para revisão: 6 divergências materiais na receita (amortizações de
empréstimos de CRCs com pagamentos irregulares — BA/PI/RS com run-rate zero mas
histórico sazonal de pagamento no 2º semestre; candidatas a override ou método
sazonal) e a rubrica Demais Contribuições (Fundo de Integração) realizando sem
orçamento.

Verificação: CLI dos dois ramos, coexistência no banco, tela nos dois ramos
(AppTest), resultado consolidado e exportações de receita (Excel conferido ao
centavo; PDF validado com pypdf) — tudo OK.

## 15. Curva mensal de desembolso/arrecadação (26/07/2026)

Nova visualização na tela Fechamento 2026 (entre a tabela hierárquica e a
exportação): a projeção anual quebrada mês a mês, com o realizado (Diário) e o
projetado (motor) lado a lado — para acompanhar o fluxo de caixa ao longo do
ano, não só o total de dezembro.

### Modelo de dados

- **`projecao_mensal`** (nova tabela): `(conselho, ano, conta, mes) → valor,
  projetado (0/1)`. Persistida junto com `projecao_resultado` a cada
  recálculo — meses ≤ corte vêm do Diário real; meses > corte vêm de
  `restante_por_mes` do motor.
- **Distribuição mensal do override manual**: antes o override só definia o
  total do fechamento; agora o residual (fechamento − YTD) é distribuído pelos
  meses restantes seguindo o perfil sazonal histórico da conta (ou uniforme,
  se não houver perfil) — para que a curva mensal também faça sentido quando
  o usuário sobrescreve o valor anual.
- Conferência: soma de `projecao_mensal` por conta bate com `proj_fechamento`
  ao centavo, em todas as contas, nos dois ramos (testado).

### Tela

- **Gráfico de barras** (Altair): Jan–Dez, R$ milhões, categórico
  Realizado/Projetado (azul escuro `#2d5fa8` / azul-petróleo `#3fa0c8` —
  paleta validada com `validate_palette.js`: banda de luminosidade, piso de
  croma, separação CVD ΔE 18-20 e piso de visão normal todos PASS). Tooltip
  por barra (mês, tipo, valor). Meses futuros ficam visualmente diferenciados
  do realizado sem depender só da cor (posição temporal + tom).
- **Seletor de natureza**: "(Todas)" mostra o grafico agregado + matriz por
  natureza; escolher uma natureza detalha a matriz por conta dentro dela.
- **Matriz mensal** (`gerar_html_curva_mensal`): mesmo padrão visual das
  demais tabelas HTML do app; colunas de meses projetados com cabeçalho e
  fundo destacados e marcador `*`.
- Rótulo se adapta ao ramo: "Curva mensal de **desembolso**" (despesa) /
  "**arrecadação**" (receita).

### Exportações

- **Excel**: nova aba **Curva Mensal** — conta × mês (+ Total), meses
  projetados com cabeçalho `Mês*` em destaque e formato numérico; ordenada
  por total decrescente.
- **PDF**: nova tabela "Curva mensal por natureza" (R$ mil, meses projetados
  marcados com `*`) inserida entre o resumo por natureza e os alertas.

### Correção de bug encontrado na verificação visual

Ao inspecionar a tela no navegador (Chrome via automação), o quadro
**"Resultado orçamentário projetado"** (`st.info`, seção 14) renderizava
quebrado: como a string tinha **três** ocorrências de `R$` e `st.info` trata o
texto como Markdown, o par de `$` foi interpretado como delimitador de LaTeX
(KaTeX) pelo Streamlit — o trecho entre o 1º e 2º `$` saiu em itálico
serifado ("111.927.353,00 − DespesaR") em vez de texto normal. Corrigido
escapando o cifrão (`R\$`) em `pages/fechamento.py`. Conferido que nenhuma
outra chamada `st.info/success/warning/error` do app tem mais de um `R$` na
mesma string (risco não recorre em outro lugar). Recarregada no navegador após
a correção — texto renderiza normalmente.

Verificação: consistência curva↔fechamento (script), teste de override com
distribuição mensal do residual, tela nos dois ramos via AppTest, exportações
com a nova aba/tabela (Excel e PDF conferidos), e inspeção visual do gráfico e
da matriz no navegador (Chrome), incluindo o tooltip do gráfico.

## 16. Atualização de dados — Jun/2026 (26/07/2026)

Primeira atualização real do ciclo completo (baixar → reimportar → recalcular),
documentada em detalhe por ser a referência de como repetir o processo.

### Bug corrigido: `baixar_diario.py` desatualizado

O script em `DECONT/Códigos/baixar_diario.py` estava com `anos = [2022, 2023,
2024]` (sem 2025/2026) e salvava como `lancamentos_{ano}.csv` — nome diferente
do que `core/dados_reais.py` espera (`Diario_{ano}.csv`). Ou seja, os arquivos
`Diario_2025.csv`/`Diario_2026.csv` existentes não tinham sido gerados por essa
versão do script. Corrigido: `anos = [2022, 2023, 2024, 2025, 2026]` e
`nome_arquivo = f"Diario_{ano}.csv"`.

### Incidente durante o download: falha SSL isolada em CFC/2022

Rodando o script corrigido (135 requisições: 27 conselhos × 5 anos), **1 única
requisição falhou** — `CFC - 2022`, com `SSLCertVerificationError: self-signed
certificate in certificate chain`. As outras 134 (incluindo CFC nos outros 4
anos) tiveram sucesso com a mesma sessão/código, indicando falha de rede
pontual, não um problema real do certificado do servidor.

**Risco identificado**: como o script grava um único CSV por ano com todos os
conselhos que respondeu, a falha isolada de CFC/2022 fez o `Diario_2022.csv`
regravado ficar **sem nenhuma linha de CFC** (759.571 linhas, só as outras 26
CRCs) — o que teria zerado a reconciliação de despesa/receita 2022 se
importado assim.

**Correção aplicada**: script avulso (não versionado) que buscou só
`conselho=CFC, ano=2022` na mesma API e mesclou de volta no CSV (em vez de
repetir as 135 requisições). Bateu exatamente com a contagem original:
52.309 linhas de CFC, 811.880 linhas totais. Confirmado que nenhum outro
ano/conselho teve falha (só essa 1 linha de erro no log inteiro).

**Lição para próximas atualizações**: depois de rodar `baixar_diario.py`,
antes de reimportar, vale conferir o log por linhas `Erro em` — uma falha
isolada pode passar despercebida porque o script continua e ainda "gera o CSV
com sucesso", só que incompleto.

### Resultado da reimportação e recálculo

- `python importar_dados.py`: reconciliação 2022-2025 **100%** novamente (a
  correção do CFC/2022 resolveu o que seria uma quebra total naquele ano).
- Diário 2026 cresceu de 320.751 para **401.277 linhas** (37.821 de CFC) —
  dados agora vão até **21/07/2026**, cobrindo **junho inteiro**. Como julho
  está parcial (dia 21 < 28), o motor manteve o corte em **maio→junho**
  corretamente (detecção automática, sem intervenção manual).
- Projeção recalculada nos dois ramos:

| | Orçamento | YTD (até Jun) | Fechamento M3 | M2 | % |
|---|---:|---:|---:|---:|---:|
| Despesa | 132,6 mi | 47,9 mi | **110,1 mi** | 115,1 mi | 83,0% |
| Receita | 132,6 mi | 73,5 mi | **112,2 mi** | 111,3 mi | 84,6% |

**Resultado orçamentário projetado: Receita R$ 112,16 mi − Despesa R$ 110,06 mi
= superávit de ~R$ 2,10 milhões** — o sinal **inverteu** em relação à rodada
de maio (que apontava déficit de ~R$ 1,1 mi). Isso ilustra bem por que a
ferramenta precisa ser recalculada a cada atualização de dados, não é uma
foto única: um mês a mais de execução real mudou a leitura do fechamento do
ano em ~R$ 3,2 milhões.

Consistência conferida por script: curva mensal ↔ fechamento bate ao centavo
nos dois ramos após o recálculo.

### Bug corrigido: `baixar_plano_contas.py` (mesmo padrão do `baixar_diario.py`)

Mesma classe de problema: `anos = [2021, 2022, 2023, 2024]` (sem 2025/2026) e
salvava como `plano_contas_2021_2024.csv` (minúsculo/underscore) — o
importador espera `PlanoContas_2021_2024.csv`. Corrigido: `anos = [2021, 2022,
2023, 2024, 2025, 2026]`; o **nome do arquivo de saída foi mantido**
`PlanoContas_2021_2024.csv` (apesar de agora cobrir até 2026) para não exigir
nenhuma mudança em `core/dados_reais.py` — é só um rótulo, o conteúdo é que
importa.

**Executado em seguida** (162 requisições: 27 conselhos × 6 anos, 0 erros).
Reimportação (`python importar_dados.py`) **quebrou na primeira tentativa**:
`KeyError: ['grupo2', 'grupo3', 'grupo4'] not in index`. Investigação mostrou
que o endpoint `planoContas` da API **não retorna hierarquia de grupos** —
só `ano, numeroConta, nomeConta, descricaoDetalhadaConta, contaSuperior`
(confirmado inspecionando o JSON bruto). O arquivo antigo, que tinha
"Descrição Grupo 2/3/4", deve ter vindo de outro processo (provavelmente um
Power Query que resolvia a hierarquia recursivamente via `contaSuperior`) —
não deste script. Como `plano_contas_real` **não é usada em nenhum cálculo**
do motor (confirmado por grep em `core/projecao_engine.py`), corrigido
tornando `core/dados_reais.py::importar_plano_contas()` tolerante à ausência
desses campos (preenche com `None` em vez de quebrar) em vez de tentar
reconstruir a hierarquia.

**Efeito colateral aceito**: as 3.195 contas em `plano_contas_real` ficaram
**sem grupo2/3/4 preenchido** (antes tinham) — informação perdida por não
estar disponível na API na forma simples, mas sem impacto em nenhum número da
projeção. Se a hierarquia for necessária no futuro (ex.: agrupar a tela de
Fechamento por grupo contábil oficial em vez de só por natureza), dá para
reconstruir resolvendo `contaSuperior` recursivamente — não implementado por
não ter uso hoje.

Reimportação re-executada com sucesso após a correção: reconciliação 2022-2025
100% novamente; nenhum recálculo de projeção foi necessário (plano de contas
não entra nas contas de despesa/receita, só nos metadados de referência).

### Quarto script auditado: `baixar_saldoinicial.py` — sem bugs

Diferente dos outros três, **não é usado em nenhum lugar do pipeline de
importação** (`core/dados_reais.py` não referencia balanço/saldo) — gera
`Fixas/balanco_patrimonial_2021.csv`, hoje desconectado do motor de projeção.
Rodado para conferir (27 conselhos, ano 2021 — parece ser mesmo um "saldo
inicial" fixo, não um dado que se atualiza a cada ano): **27/27 OK, 0 erros**,
saída idêntica em estrutura e contagem ao arquivo já existente (9.747 linhas,
mesmas 5 colunas). Conferência de sanidade: ATIVO = PASSIVO + Patrimônio
Líquido para o CFC (R$ 231.973.500,00 nos dois lados) — balanço fecha. Dos 4
scripts de download, este é o único sem nenhum problema encontrado.

### Resumo da auditoria dos 4 scripts de `DECONT/Códigos`

| Script | Usado pelo importador? | Bug encontrado | Situação |
|---|---|---|---|
| `baixar_diario.py` | Sim (`execucao_mensal`) | Anos desatualizados + nome de arquivo errado | Corrigido e executado |
| `baixar_orçamentoatualizado.py` | Sim (`orcamento_anual`) | Nenhum | Executado, sem alteração |
| `baixar_plano_contas.py` | Sim (`plano_contas_real`) | Anos desatualizados + nome de arquivo errado + hierarquia de grupos inexistente na API | Corrigido e executado |
| `baixar_saldoinicial.py` | Não (desconectado do pipeline) | Nenhum | Executado só para conferência |
