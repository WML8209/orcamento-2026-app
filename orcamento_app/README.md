# Ferramenta de Projeção de Orçamento 2026

App local (Streamlit) com o motor de **projeção de fechamento de despesa e
receita 2026** do CFC, alimentado por dados reais da API de dados abertos do
CFC (ver `Orcamento2026.md` para o histórico completo do projeto).

## Instalação (uma vez só)

1. Instale o [Python 3.11+](https://www.python.org/downloads/) (marque "Add to PATH" no instalador do Windows).
2. Abra um terminal (PowerShell/Prompt de Comando) nesta pasta e rode:

```
pip install -r requirements.txt
```

## Rodar o sistema

```
streamlit run Home.py
```

Isso abre automaticamente uma aba no seu navegador (endereço tipo
`http://localhost:8501`). É o app "rodando" — pode deixar o terminal aberto
enquanto usa. Para fechar, feche o terminal ou aperte `Ctrl+C`.

## Onde ficam os dados

Tudo dentro da pasta `data/`. A tela **Início** do app mostra o status de
cada um desses arquivos e permite enviar/substituir qualquer um deles direto
pela interface (útil sobretudo depois de publicar o app na nuvem).

Opcionalmente, esses 4 arquivos podem ser sincronizados automaticamente com
uma pasta **Data** no seu Google Drive — resolve a perda de dados quando o
Streamlit Cloud reinicia o container (disco efêmero). Ver
`CONFIGURAR_GOOGLE_DRIVE.md` para o passo a passo; sem essa configuração, o
app funciona normalmente só com o disco local.

| Arquivo | O que é | Como atualizar |
|---|---|---|
| `dados_reais.db` | Banco SQLite com o orçamento e o executado reais do CFC — é o que alimenta a tela **Fechamento 2026** | Gerado localmente por `python importar_dados.py` (ver Orcamento2026.md). Depois é só enviar o arquivo pela tela Início ou substituir em `data/`. |
| `bases.xlsx` | Abas fixas de referência (Datas, PlanoDeContas, Projetos, SubProjetos, PCA2025, ListaContratos, ParametrosDiaria, Diario) | Legado do sistema anterior — hoje não é lido por nenhuma tela ativa. |
| `orcamento_historico.xlsx` | Orçamento fixo de anos anteriores a 2026 | Legado do sistema anterior — hoje não é lido por nenhuma tela ativa. |
| `orcamento2026.db` | Banco SQLite criado/mantido automaticamente pelo app (`core/db.py`) | Não precisa mexer — é recriado vazio sozinho se não existir. |
| `exportados/` | PDFs e Excel gerados pela tela Fechamento 2026 | Criada automaticamente a cada exportação. |

Se quiser acessar de mais de um computador (ex. notebook + PC) sem usar a
sincronização com o Google Drive acima, mova a pasta `data/` inteira para
uma pasta sincronizada (OneDrive, Google Drive Desktop) e aponte
`ORCAMENTO_DATA_DIR` (variável de ambiente) ou edite `core/config.py` para
esse caminho.

## Tela Fechamento 2026

Projeção de despesa (6.3) e receita (6.2) por natureza e conta, com:

- Tabela hierárquica Natureza > Conta (Orçamento | Realizado Acumulado |
  Fechamento M3 | % execução | Conferência M2 | divergência | confiança).
- Curva mensal de desembolso/arrecadação (gráfico + matriz por natureza).
- Configuração de método por conta (Automático, Média Móvel, Sazonal ou
  Fechamento Manual com justificativa) e parâmetro global de reajuste de
  data-base para a folha de pessoal.
- Exportação em Excel (Resumo + Detalhe com memória de cálculo) e PDF.

Os métodos de projeção, a regra de sinal do executado (D−C despesa, C−D
receita) e o modelo de conferência M2 estão documentados em
`core/projecao_engine.py` e em `Orcamento2026.md`.

## Estrutura do código

```
Home.py                -> tela inicial: status e upload dos arquivos de dados
importar_dados.py      -> CLI: importa os CSVs da API do CFC para data/dados_reais.db
projetar_fechamento.py -> CLI: roda a projeção e imprime o relatório no terminal
pages/
  fechamento.py         -> tela Fechamento 2026
core/
  config.py             -> caminhos dos arquivos (edite aqui se mudar a pasta de dados)
  db.py                 -> banco SQLite orcamento2026.db (criado automaticamente)
  dados_reais.py        -> importador dos CSVs do CFC para dados_reais.db
  projecao_engine.py    -> motor de projeção (M3 híbrido por natureza + conferência M2)
  exportar.py           -> geração de PDF e Excel da Projeção de Fechamento
  tabela_html.py         -> renderização das tabelas HTML da tela Fechamento 2026
  formatos.py            -> formatação de números/datas no padrão BR
data/                    -> arquivos de dados (ver tabela acima)
```
