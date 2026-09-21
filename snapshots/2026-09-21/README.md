# Snapshot das posições — 21/09/2026 (atualização Ago/2026 completo)

Primeiro snapshot tirado com o **novo caminho de atualização**: o botão
**"Atualizar dados agora"** da tela Início, que busca só o CFC/2026 direto na
API de dados abertos do CFC (`core/fonte_api.py`), reimporta o
`dados_reais.db`, recalcula a projeção dos dois ramos e reenvia os bancos ao
Google Drive — tudo em ~10 s, sem depender da pasta `Códigos` nem dos scripts
`baixar_*.py` (que continuam disponíveis como caminho antigo).

Mesmo propósito dos snapshots anteriores: registro de referência para
comparação, já que a URL pública do app
(`https://orcamento-2026-cfc.streamlit.app`) permite upload de dados sem
autenticação pela tela Início (ver `orcamento_app/README.md`).

Diário baixado até **2026-09-10** (setembro parcial, dia 10 < 28), então o
mês de corte automático avançou para **Ago/2026** — agosto ficou completo
pela primeira vez e a projeção agora cobre **setembro a dezembro** como
meses restantes. Reconciliação 2022–2025 100% OK (0 divergências).

Validação do caminho novo antes de aplicar: a agregação conta × mês obtida
pela API foi comparada com a que estava no banco (importada dos CSVs em
09/08/2026) — **janeiro a junho batem centavo a centavo** (mesmas linhas,
mesmos ΣD/ΣC e nº de lançamentos, estornos incluídos como no caminho CSV);
julho só difere pelos lançamentos registrados depois de 09/08 (5.367 →
5.636 lançamentos).

Os relatórios de Fechamento foram gerados chamando diretamente
`core.projecao_engine` + `core.exportar` (com curva mensal), a partir da
projeção persistida pelo próprio botão — aplicam os mesmos overrides e
métodos por conta já salvos em `data/projecao.db`, resultado idêntico ao
"Exportar" da tela Fechamento 2026.

## Conteúdo

| Arquivo | O que é |
|---|---|
| `Fechamento2026_Despesa.xlsx` / `.pdf` | Projeção de fechamento de despesa (6.3) — resumo por natureza, detalhe por conta com memória de cálculo, curva mensal |
| `Fechamento2026_Receita.xlsx` / `.pdf` | Mesma coisa, para receita (6.2) |
| `dados_reais_orcamento_anual.csv` | Orçamento Inicial + Realizado oficial por conta/ano (tabela `orcamento_anual` de `dados_reais.db`) |
| `dados_reais_execucao_mensal.csv` | ΣD, ΣC e nº de lançamentos por conta × mês (tabela `execucao_mensal`) |
| `dados_reais_plano_contas_real.csv` | Plano de contas (tabela `plano_contas_real`) |
| `dados_reais_reconciliacao.csv` | Executado (Diário) × Realizado oficial, contas folha 6.2/6.3 (tabela `reconciliacao`) |
| `dados_reais_importacao_meta.csv` | Metadados da última importação (data, fonte, contagens, etc.) |

## Números de referência (totais, Ago/2026)

**Despesa (6.3)**: Orçamento R$ 132.578.920,00 · Realizado (jan-ago)
R$ 73.427.315,68 · Fechamento M3 R$ 124.250.090,27 (93,7% do orçamento) ·
Conferência M2 R$ 128.115.234,45

**Receita (6.2)**: Realizado (jan-ago) R$ 90.240.522,43 · Fechamento M3
R$ 113.793.467,70 (85,8% do orçamento) · Conferência M2 R$ 117.370.698,45

**Resultado orçamentário projetado 2026**: déficit de R$ 10.456.622,57

**Reconciliação**: 0 divergências (Executado do Diário bate 100% com o
Realizado oficial nos anos fechados).

### Por natureza (M3)

| Despesa | Orçamento | YTD (jan-ago) | Fechamento M3 | % |
|---|---:|---:|---:|---:|
| Pessoal e Encargos | 36.067.030,75 | 26.327.387,27 | 40.366.700 | 111,9% |
| Contratos e Serviços | 47.930.369,40 | 21.802.012,50 | 34.772.290 | 72,5% |
| Diárias e Passagens | 15.623.201,00 | 11.030.196,53 | 17.660.020 | 113,0% |
| Eventos e Exames | 14.398.660,00 | 7.551.742,51 | 17.521.130 | 121,7% |
| Demais Despesas Correntes | 7.142.402,85 | 3.280.837,19 | 7.093.491 | 99,3% |
| Despesas de Capital | 11.417.256,00 | 3.435.139,68 | 6.836.452 | 59,9% |

| Receita | Orçamento | YTD (jan-ago) | Fechamento M3 | % |
|---|---:|---:|---:|---:|
| Cota-Parte dos CRCs | 70.310.428,00 | 59.743.712,98 | 69.928.680 | 99,5% |
| Receitas Financeiras | 19.295.913,00 | 13.246.120,86 | 20.259.030 | 105,0% |
| Exploração de Bens e Serviços | 15.022.898,00 | 13.795.559,66 | 15.728.660 | 104,7% |
| Outras Receitas Correntes | 87.410,00 | 1.336.037,16 | 4.763.306 | 5449% |
| Receitas de Capital | 1.913.351,00 | 982.617,78 | 1.977.318 | 103,3% |
| Demais Contribuições | 0,00 | 1.136.473,99 | 1.136.474 | — |
| Previsão Adicional (equilíbrio) | 25.948.920,00 | 0,00 | 0 | 0% |

### Comparação com o snapshot anterior (`../2026-08-09b/`, corte Jul/2026)

| | Jul/2026 (`../2026-08-09b/`) | Ago/2026 (este) |
|---|---:|---:|
| Despesa YTD | 61.645.201,37 | 73.427.315,68 |
| Despesa M3 | 119.683.766,76 (90,3%) | 124.250.090,27 (93,7%) |
| Receita YTD | 81.469.306,92 | 90.240.522,43 |
| Receita M3 | 112.856.654,73 (85,1%) | 113.793.467,70 (85,8%) |
| Resultado | déficit R$ 6.827.112,03 | déficit R$ 10.456.622,57 |

Mais um mês de execução real piorou a leitura do fechamento em ~R$ 3,63
milhões, de novo quase todo pelo lado da despesa (M3 subiu 3,4 p.p. do
orçamento; a receita subiu só 0,7 p.p.). Os pontos de atenção já
registrados em `Analise_Projeção_JULHO.md` continuam valendo — em especial
"Outras Receitas Correntes" (a conta Indenizações, com lançamento isolado de
R$ 1,3 mi em julho, segue extrapolada pelo método sazonal) e as naturezas
de despesa acima de 110% do orçado (Pessoal, Diárias e Passagens, Eventos e
Exames).

## Como usar em caso de suspeita de alteração indevida

1. Baixe o `dados_reais.db` (ou `bases.xlsx`/`orcamento_historico.xlsx`/
   `orcamento2026.db`) atual pela tela Início do app publicado, ou acesse o
   servidor.
2. Rode `python importar_dados.py --api --anos 2022 2023 2024 2025 2026`
   local (ou abra o `.db` direto) e compare os CSVs gerados com os desta
   pasta — mesmas colunas/ordenação, então dá pra usar `diff`/Excel/
   comparador de CSV. Lembre que o ano corrente muda todo dia útil; os anos
   fechados (2022–2025) têm de bater exatamente.
3. Se os totais acima não baterem com o que a tabela `orcamento_anual` mostra
   hoje, os dados publicados foram alterados — restaure fazendo commit dos
   arquivos originais (git tem o histórico completo em `orcamento_app/data/`)
   e um novo deploy no Streamlit Cloud (ele redesenha a partir do repositório
   a cada push/reboot).
