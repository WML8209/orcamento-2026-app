# Snapshot das posições — 09/08/2026

Registro do estado dos dados reais e da Projeção de Fechamento, para servir
de referência de comparação — mesmo propósito do snapshot anterior
(`../2026-07-26/README.md`), já que a URL pública do app
(`https://orcamento-2026-cfc.streamlit.app`) permite upload de dados sem
autenticação pela tela Início (ver `orcamento_app/README.md`).

Corresponde ao commit `721af24` (branch `master`) do repositório
`WML8209/orcamento-2026-app`. Diário baixado até 2026-07-27, mas o mês de
corte da projeção é **Jun/2026** — julho ainda não está completo na base
baixada, então o motor de projeção (`mes_corte_padrao`) usa o último mês
fechado. Os relatórios de Fechamento foram gerados fora da tela Streamlit,
chamando diretamente `core.projecao_engine.projetar_fechamento()` +
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

## Números de referência (totais, Jun/2026)

**Despesa (6.3)**: Orçamento R$ 132.578.920,00 · Realizado R$ 47.913.353,99 ·
Fechamento M3 R$ 110.061.216,26 (83,0% do orçamento) · Conferência M2
R$ 115.133.180,71

**Receita (6.2)**: Realizado R$ 73.508.739,73 · Fechamento M3
R$ 107.689.914,90 (81,2% do orçamento) · Conferência M2 R$ 111.263.802,53

**Resultado orçamentário projetado 2026**: déficit de R$ 2.371.301,36

**Reconciliação**: 0 divergências (Executado do Diário bate 100% com o
Realizado oficial nos anos fechados).

Nota: o Realizado acumulado (YTD) e a Fechamento M3 da despesa não mudaram
em relação ao snapshot de 26/07 — o mês de corte continua Jun/2026 nos dois
casos, e a execução de jan-jun não foi alterada pela reimportação. A Receita
M3 mudou (R$ 112.164.742,17 → R$ 107.689.914,90): reflete ajuste nos
overrides/métodos por conta salvos em `projecao.db` entre as duas datas, não
mudança nos dados brutos.

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
