# Snapshot das posições — 09/08/2026 (atualização Jul/2026 completo)

Segundo snapshot do dia 09/08 — o de `../2026-08-09/` foi tirado **antes**
desta atualização de dados (corte ainda em Jun/2026); este reflete o estado
**depois** de rodar `atualizar_mensal.py` (baixar Diário + Orçamento
Atualizado da API do CFC e reimportar), que trouxe julho completo e mudou o
mês de corte automático da projeção.

Mesmo propósito dos snapshots anteriores: registro de referência para
comparação, já que a URL pública do app
(`https://orcamento-2026-cfc.streamlit.app`) permite upload de dados sem
autenticação pela tela Início (ver `orcamento_app/README.md`).

Corresponde ao commit `721af24` (branch `master`) do repositório
`WML8209/orcamento-2026-app`. Diário baixado até **2026-07-31** (mês de
corte **Jul/2026** — julho ficou completo pela primeira vez, então a
projeção agora cobre **agosto a dezembro** como meses restantes). Download
sem nenhum erro (Diário + Orçamento Atualizado, 27 conselhos × 5 anos cada);
reconciliação 2022–2025 100% OK.

Os relatórios de Fechamento foram gerados fora da tela Streamlit, chamando
diretamente `core.projecao_engine.projetar_fechamento()` +
`core.exportar.gerar_excel_fechamento()`/`gerar_pdf_fechamento()` — aplicam
os mesmos overrides e métodos por conta já salvos em `data/projecao.db`,
resultado idêntico ao botão "Recalcular" + "Exportar" da tela Fechamento 2026.

## Conteúdo

| Arquivo | O que é |
|---|---|
| `Fechamento2026_Despesa.xlsx` / `.pdf` | Projeção de fechamento de despesa (6.3) — resumo por natureza, detalhe por conta com memória de cálculo, curva mensal |
| `Fechamento2026_Receita.xlsx` / `.pdf` | Mesma coisa, para receita (6.2) |
| `dados_reais_orcamento_anual.csv` | Orçamento Inicial + Realizado oficial por conta/ano (tabela `orcamento_anual` de `dados_reais.db`) |
| `dados_reais_execucao_mensal.csv` | ΣD, ΣC e nº de lançamentos por conta × mês (tabela `execucao_mensal`) |
| `dados_reais_plano_contas_real.csv` | Plano de contas (tabela `plano_contas_real`) |
| `dados_reais_reconciliacao.csv` | Executado (Diário) × Realizado oficial, contas folha 6.2/6.3 (tabela `reconciliacao`) |
| `dados_reais_importacao_meta.csv` | Metadados da última importação (data, contagens, etc.) |

## Números de referência (totais, Jul/2026)

**Despesa (6.3)**: Orçamento R$ 132.578.920,00 · Realizado (jan-jul)
R$ 61.645.201,37 · Fechamento M3 R$ 119.683.766,76 (90,3% do orçamento) ·
Conferência M2 R$ 124.647.609,30

**Receita (6.2)**: Realizado (jan-jul) R$ 81.469.306,92 · Fechamento M3
R$ 112.856.654,73 (85,1% do orçamento) · Conferência M2 R$ 116.311.194,52

**Resultado orçamentário projetado 2026**: déficit de R$ 6.827.112,03

**Reconciliação**: 0 divergências (Executado do Diário bate 100% com o
Realizado oficial nos anos fechados).

### Comparação com o snapshot anterior (mesmo dia, corte Jun/2026)

| | Jun/2026 (`../2026-08-09/`) | Jul/2026 (este) |
|---|---:|---:|
| Despesa YTD | 47.913.353,99 | 61.645.201,37 |
| Despesa M3 | 110.061.216,26 (83,0%) | 119.683.766,76 (90,3%) |
| Receita YTD | 73.508.739,73 | 81.469.306,92 |
| Receita M3 | 107.689.914,90 (81,2%) | 112.856.654,73 (85,1%) |
| Resultado | déficit R$ 2.371.301,36 | déficit R$ 6.827.112,03 |

Um mês a mais de execução real piorou a leitura do fechamento em ~R$ 4,46
milhões — praticamente todo o efeito veio do lado da despesa (M3 subiu 9,6
p.p. do orçamento), com a receita acompanhando em ritmo mais próximo do
esperado.

## Como usar em caso de suspeita de alteração indevida

1. Baixe o `dados_reais.db` (ou `bases.xlsx`/`orcamento_historico.xlsx`/
   `orcamento2026.db`) atual pela tela Início do app publicado, ou acesse o
   servidor.
2. Rode `python importar_dados.py` local com os dados baixados (ou abra o
   `.db` direto) e compare os CSVs gerados com os desta pasta — mesmas
   colunas/ordenação, então dá pra usar `diff`/Excel/comparador de CSV.
3. Se os totais acima não baterem com o que a tabela `orcamento_anual` mostra
   hoje, os dados publicados foram alterados — restaure fazendo commit dos
   arquivos originais (git tem o histórico completo em `orcamento_app/data/`)
   e um novo deploy no Streamlit Cloud (ele redesenha a partir do repositório
   a cada push/reboot).
