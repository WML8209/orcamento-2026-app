# Snapshot das posições — 26/07/2026

Registro do estado dos dados reais **logo após a publicação do app no
Streamlit Cloud** (`https://orcamento-2026-cfc.streamlit.app`), para servir
de referência de comparação caso os arquivos publicados sejam alterados
(a URL é pública e a tela Início permite upload sem autenticação — ver
`orcamento_app/README.md`).

Corresponde ao commit `89691c5` (branch `master`) do repositório
`WML8209/orcamento-2026-app`, mês de corte Jun/2026.

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
R$ 112.164.742,17 (84,6% do orçamento) · Conferência M2 R$ 111.263.802,53

**Resultado orçamentário projetado 2026**: superávit de R$ 2.103.525,91

## Como usar em caso de suspeita de alteração indevida

1. Baixe o `dados_reais.db` (ou `bases.xlsx`/`orcamento_historico.xlsx`/
   `orcamento2026.db`) atual pela tela Início do app publicado, ou acesse o
   servidor.
2. Rode `python importar_dados.py` local com os dados baixados (ou abra o
   `.db` direto) e compare os CSVs gerados com os desta pasta — mesmas
   colunas/ordenação, então dá pra usar `diff`/Excel/comparador de CSV.
3. Se os totais acima não baterem com o que a tela Fechamento 2026 mostra
   hoje, os dados publicados foram alterados — restaure fazendo commit dos
   arquivos originais (git tem o histórico completo em `orcamento_app/data/`)
   e um novo deploy no Streamlit Cloud (ele redesenha a partir do repositório
   a cada push/reboot).
