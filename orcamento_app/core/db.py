"""
Banco SQLite que substitui a "tabela auxiliar viva" do Orçamento 2026 e a
tabela PCA2026 — o que a macro fazia gravando linhas na planilha, aqui é
feito gravando linhas no banco. Mesma lógica de Índice (todas as linhas de
um mesmo lançamento compartilham o índice e são excluídas juntas).
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import pandas as pd

from core.config import ORCAMENTO_2026_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS orcamento_2026 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indice INTEGER NOT NULL,
    projeto TEXT,
    subprojeto TEXT,
    conta TEXT,
    valor REAL,
    data TEXT,
    descricao TEXT,
    memoria_calculo TEXT,
    origem TEXT  -- 'diarias' ou 'despesas_gerais', só para rastreabilidade
);

CREATE TABLE IF NOT EXISTS lancamentos_meta (
    indice INTEGER PRIMARY KEY,
    tipo TEXT,            -- 'diarias' ou 'despesas_gerais'
    parametros_json TEXT  -- inputs originais do formulário, para permitir editar depois
);

CREATE TABLE IF NOT EXISTS pca_2026 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indice_orcamento INTEGER,  -- amarra ao mesmo índice do lançamento em orcamento_2026
    item INTEGER,
    descricao_objeto TEXT,
    justificativa TEXT,
    contratacao_renovacao TEXT,
    data_contratacao_renovacao TEXT,
    valor_contratacao_renovacao REAL,
    valor_orcamento_2026 REAL,
    grau_prioridade TEXT,
    classificacao TEXT,
    conta_contabil TEXT,
    descricao TEXT,
    projeto TEXT,
    uo TEXT,
    diferenca REAL,
    observacao_decont TEXT,
    mes TEXT,
    data_pca TEXT
);
"""


@contextmanager
def get_conn():
    ORCAMENTO_2026_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ORCAMENTO_2026_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def proximo_indice() -> int:
    with get_conn() as conn:
        cur = conn.execute("SELECT MAX(indice) FROM orcamento_2026")
        maior = cur.fetchone()[0]
    return (maior or 0) + 1


def inserir_linhas_orcamento(linhas: list[dict]):
    """linhas: lista de dicts com as chaves da tabela orcamento_2026 (menos id)."""
    if not linhas:
        return
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO orcamento_2026
               (indice, projeto, subprojeto, conta, valor, data, descricao, memoria_calculo, origem)
               VALUES (:indice, :projeto, :subprojeto, :conta, :valor, :data, :descricao, :memoria_calculo, :origem)""",
            linhas,
        )


def inserir_pca(linha: dict):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO pca_2026
               (indice_orcamento, item, descricao_objeto, justificativa, contratacao_renovacao,
                data_contratacao_renovacao, valor_contratacao_renovacao, valor_orcamento_2026,
                grau_prioridade, classificacao, conta_contabil, descricao, projeto, uo,
                diferenca, observacao_decont, mes, data_pca)
               VALUES (:indice_orcamento, :item, :descricao_objeto, :justificativa, :contratacao_renovacao,
                :data_contratacao_renovacao, :valor_contratacao_renovacao, :valor_orcamento_2026,
                :grau_prioridade, :classificacao, :conta_contabil, :descricao, :projeto, :uo,
                :diferenca, :observacao_decont, :mes, :data_pca)""",
            linha,
        )


def excluir_por_indice(indice: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM orcamento_2026 WHERE indice = ?", (indice,))
        conn.execute("DELETE FROM pca_2026 WHERE indice_orcamento = ?", (indice,))
        conn.execute("DELETE FROM lancamentos_meta WHERE indice = ?", (indice,))


def salvar_meta(indice: int, tipo: str, parametros: dict):
    import json
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO lancamentos_meta (indice, tipo, parametros_json) VALUES (?, ?, ?)",
            (indice, tipo, json.dumps(parametros, default=str)),
        )


def carregar_meta(indice: int):
    import json
    with get_conn() as conn:
        cur = conn.execute("SELECT tipo, parametros_json FROM lancamentos_meta WHERE indice = ?", (indice,))
        row = cur.fetchone()
    if not row:
        return None
    tipo, parametros_json = row
    return {"tipo": tipo, "parametros": json.loads(parametros_json)}


def carregar_orcamento_2026() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM orcamento_2026 ORDER BY indice DESC, id", conn)
    return df


def carregar_pca_2026() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM pca_2026 ORDER BY item", conn)
    return df


def proximo_item_pca() -> int:
    with get_conn() as conn:
        cur = conn.execute("SELECT MAX(item) FROM pca_2026")
        maior = cur.fetchone()[0]
    return (maior or 0) + 1


def atualizar_pca_editaveis(id_: int, justificativa, grau_prioridade, classificacao):
    """Atualiza só os 3 campos que o usuário pode editar direto na tela de PCA 2026."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE pca_2026 SET justificativa = ?, grau_prioridade = ?, classificacao = ? WHERE id = ?",
            (justificativa, grau_prioridade, classificacao, id_),
        )
