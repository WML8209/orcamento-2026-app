"""
Configuração de caminhos do sistema.

IMPORTANTE: edite os caminhos abaixo para apontar para os arquivos no SEU
computador. Os três arquivos podem ficar todos na mesma pasta.

- BASES_XLSX: aba(s) fixas de referência (Datas, Plano de Contas, Projetos,
  SubProjetos, PCA2025, Lista de Contratos, Parâmetros Diária). Você edita
  esse arquivo livremente quando precisar atualizar uma base; o app relê
  sozinho sempre que detectar que o arquivo mudou (por data de modificação).

- ORCAMENTO_HISTORICO_XLSX: parte FIXA da tabela Orçamento (anos anteriores
  a 2026). Não é modificado pelo app.

- ORCAMENTO_2026_DB: banco SQLite que funciona como a "tabela auxiliar viva"
  do Orçamento 2026 — é nele que o app grava/exclui os lançamentos feitos
  pelas telas de Diárias/Passagens e Despesas Gerais, substituindo o que
  antes era feito pela macro.
"""
from pathlib import Path
import os

# Pasta onde ficam os arquivos de dados. Pode ser trocada por uma pasta
# do OneDrive/Google Drive sincronizada, se você quiser acessar de mais
# de um computador.
DATA_DIR = Path(os.environ.get("ORCAMENTO_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))

BASES_XLSX = DATA_DIR / "bases.xlsx"
ORCAMENTO_HISTORICO_XLSX = DATA_DIR / "orcamento_historico.xlsx"
ORCAMENTO_2026_DB = DATA_DIR / "orcamento2026.db"

# Pasta de saída de PDFs/Excel gerados pelo app
EXPORT_DIR = DATA_DIR / "exportados"

ANO_ORCAMENTO = 2026

# --- Dados reais (API de dados abertos do CFC, ver Orcamento2026.md) ---
# Pasta com os CSVs baixados pelos scripts baixar_*.py (Diário, Orçamento,
# Plano de Contas). Pode ser sobrescrita pela variável ORCAMENTO_CODIGOS_DIR.
CODIGOS_DIR = Path(os.environ.get(
    "ORCAMENTO_CODIGOS_DIR",
    Path(__file__).resolve().parent.parent.parent.parent / "Códigos",
))

# Banco SQLite compacto gerado por importar_dados.py a partir dos CSVs acima.
# Separado do orcamento2026.db (lançamentos manuais) de propósito.
DADOS_REAIS_DB = DATA_DIR / "dados_reais.db"

CONSELHO_PADRAO = "CFC"

# --- Agente de IA (análise da projeção via OpenRouter) ---
# Chave obrigatória apenas para quem for usar o botão "Gerar Análise com IA"
# (validada em tempo de uso por core/agente_ia.py, não aqui).
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
