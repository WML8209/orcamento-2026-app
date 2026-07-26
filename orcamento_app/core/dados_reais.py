"""
Importador dos dados reais da API de dados abertos do CFC (pasta DECONT/Códigos)
para o banco compacto data/dados_reais.db. Ver Orcamento2026.md.

Independente do Streamlit — roda em linha de comando via importar_dados.py.

Regra do executado (validada contra o Realizado oficial de 2025, 100% das
contas folha): despesa (6.3.x, folha) = ΣD − ΣC; receita (6.2.x, folha) = ΣC − ΣD.
A regra só vale nas contas FOLHA (11 dígitos sem pontos) — nos níveis
sintéticos e contas de controle o ramo se compensa e soma zero.
"""
from datetime import datetime
from pathlib import Path
import sqlite3

import pandas as pd

from core.config import CODIGOS_DIR, DADOS_REAIS_DB, CONSELHO_PADRAO

SCHEMA = """
CREATE TABLE IF NOT EXISTS orcamento_anual (
    ano INTEGER NOT NULL,
    conselho TEXT NOT NULL,
    conta TEXT NOT NULL,
    conta_norm TEXT,
    descricao TEXT,
    orcamento_inicial REAL,
    realizado REAL,
    eh_folha INTEGER,
    PRIMARY KEY (ano, conselho, conta)
);

CREATE TABLE IF NOT EXISTS execucao_mensal (
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    conselho TEXT NOT NULL,
    conta TEXT NOT NULL,
    conta_norm TEXT,
    soma_d REAL,
    soma_c REAL,
    n_lancamentos INTEGER,
    PRIMARY KEY (ano, mes, conselho, conta)
);

CREATE TABLE IF NOT EXISTS plano_contas_real (
    conselho TEXT NOT NULL,
    conta TEXT NOT NULL,
    conta_norm TEXT,
    descricao TEXT,
    grupo2 TEXT,
    grupo3 TEXT,
    grupo4 TEXT,
    ano_ref INTEGER,
    PRIMARY KEY (conselho, conta)
);

CREATE TABLE IF NOT EXISTS reconciliacao (
    ano INTEGER NOT NULL,
    conselho TEXT NOT NULL,
    conta TEXT NOT NULL,
    descricao TEXT,
    ramo TEXT,
    realizado_orcamento REAL,
    executado_diario REAL,
    diferenca REAL,
    bate INTEGER,
    PRIMARY KEY (ano, conselho, conta)
);

CREATE TABLE IF NOT EXISTS importacao_meta (
    chave TEXT PRIMARY KEY,
    valor TEXT
);
"""

TOLERANCIA_RECONCILIACAO = 0.05  # R$


def _norm(conta: pd.Series) -> pd.Series:
    return conta.astype(str).str.replace(".", "", regex=False)


def get_conn() -> sqlite3.Connection:
    DADOS_REAIS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DADOS_REAIS_DB)
    conn.executescript(SCHEMA)
    return conn


def _meta_set(conn, chave: str, valor):
    conn.execute("INSERT OR REPLACE INTO importacao_meta (chave, valor) VALUES (?, ?)",
                 (chave, str(valor)))


def importar_orcamento(conn, conselho: str, log) -> int:
    caminho = CODIGOS_DIR / "OrçamentoAtualizado" / "orcamento_2022_2026.csv"
    log(f"Lendo {caminho.name} ...")
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype={"Conta": str})
    df = df[df["Conselho"] == conselho].copy()
    df["conta_norm"] = _norm(df["Conta"])
    df["eh_folha"] = (df["conta_norm"].str.len() == 11).astype(int)
    df = df.rename(columns={
        "Ano": "ano", "Conselho": "conselho", "Conta": "conta",
        "Descrição": "descricao", "Orçamento Inicial": "orcamento_inicial",
        "Realizado": "realizado",
    })[["ano", "conselho", "conta", "conta_norm", "descricao",
        "orcamento_inicial", "realizado", "eh_folha"]]

    conn.execute("DELETE FROM orcamento_anual WHERE conselho = ?", (conselho,))
    df.to_sql("orcamento_anual", conn, if_exists="append", index=False)
    log(f"  orcamento_anual: {len(df)} linhas ({conselho}), anos {sorted(df['ano'].unique().tolist())}")
    return len(df)


def importar_plano_contas(conn, conselho: str, log) -> int:
    caminho = CODIGOS_DIR / "PlanoContas" / "PlanoContas_2021_2024.csv"
    log(f"Lendo {caminho.name} (em blocos) ...")
    partes = []
    for chunk in pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype=str,
                             chunksize=500_000):
        c = chunk[chunk["Conselho"] == conselho]
        if not c.empty:
            partes.append(c)
    df = pd.concat(partes, ignore_index=True)
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    # Mantém a versão mais recente de cada conta
    df = df.sort_values("Ano").drop_duplicates(subset=["Conselho", "Conta"], keep="last")
    df = df.rename(columns={
        "Conselho": "conselho", "Conta": "conta", "Descrição": "descricao",
        "Descrição Grupo 2": "grupo2", "Descrição Grupo 3": "grupo3",
        "Descrição Grupo 4": "grupo4", "Ano": "ano_ref",
    })
    df["conta_norm"] = _norm(df["conta"])
    # A API "planoContas" não devolve a hierarquia de grupos (só ano, conta,
    # descrição, contaSuperior) — grupo2/3/4 só existem se o CSV de origem já
    # vier enriquecido por outro processo. Tratados como opcionais para o
    # importador não quebrar quando ausentes.
    for col in ("grupo2", "grupo3", "grupo4"):
        if col not in df.columns:
            df[col] = None
    df = df[["conselho", "conta", "conta_norm", "descricao", "grupo2", "grupo3", "grupo4", "ano_ref"]]

    conn.execute("DELETE FROM plano_contas_real WHERE conselho = ?", (conselho,))
    df.to_sql("plano_contas_real", conn, if_exists="append", index=False)
    log(f"  plano_contas_real: {len(df)} contas distintas ({conselho})")
    return len(df)


def importar_diarios(conn, conselho: str, log) -> dict:
    pasta = CODIGOS_DIR / "Diário"
    arquivos = sorted(pasta.glob("Diario_*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum Diario_*.csv encontrado em {pasta}")

    usecols = ["Conselho", "Conta", "D/C", "Data Lançamento", "Soma de Valor"]
    conn.execute("DELETE FROM execucao_mensal WHERE conselho = ?", (conselho,))
    resumo = {}
    datas_max: dict[int, pd.Timestamp] = {}

    for arq in arquivos:
        log(f"Lendo {arq.name} (em blocos) ...")
        partes = []
        descartadas = 0
        for chunk in pd.read_csv(arq, sep=";", encoding="utf-8-sig",
                                 usecols=usecols, dtype=str, chunksize=1_000_000):
            c = chunk[chunk["Conselho"] == conselho]
            if c.empty:
                continue
            c = c.copy()
            c["data"] = pd.to_datetime(c["Data Lançamento"], errors="coerce")
            descartadas += int(c["data"].isna().sum())
            c = c.dropna(subset=["data"])
            c["valor"] = pd.to_numeric(c["Soma de Valor"], errors="coerce").fillna(0.0)
            c["ano"] = c["data"].dt.year
            c["mes"] = c["data"].dt.month
            for ano_v, dmax in c.groupby("ano")["data"].max().items():
                if ano_v not in datas_max or dmax > datas_max[ano_v]:
                    datas_max[int(ano_v)] = dmax
            g = (c.groupby(["ano", "mes", "Conta", "D/C"])
                  .agg(valor=("valor", "sum"), n=("valor", "size"))
                  .reset_index())
            partes.append(g)

        if not partes:
            log(f"  {arq.name}: nenhum lançamento de {conselho}")
            continue

        g = (pd.concat(partes, ignore_index=True)
               .groupby(["ano", "mes", "Conta", "D/C"])
               .agg(valor=("valor", "sum"), n=("n", "sum"))
               .reset_index())
        pv = g.pivot_table(index=["ano", "mes", "Conta"], columns="D/C",
                           values="valor", aggfunc="sum", fill_value=0.0)
        for col in ("D", "C"):
            if col not in pv.columns:
                pv[col] = 0.0
        pv["n_lancamentos"] = g.groupby(["ano", "mes", "Conta"])["n"].sum()
        out = pv.reset_index().rename(columns={"Conta": "conta", "D": "soma_d", "C": "soma_c"})
        out["conselho"] = conselho
        out["conta_norm"] = _norm(out["conta"])
        out = out[["ano", "mes", "conselho", "conta", "conta_norm", "soma_d", "soma_c", "n_lancamentos"]]
        out.to_sql("execucao_mensal", conn, if_exists="append", index=False)

        n_lanc = int(out["n_lancamentos"].sum())
        anos = sorted(out["ano"].unique().tolist())
        resumo[arq.name] = dict(linhas_agregadas=len(out), lancamentos=n_lanc,
                                anos=anos, descartadas=descartadas)
        log(f"  {arq.name}: {n_lanc:,} lançamentos ({conselho}) -> {len(out)} linhas conta×mês"
            + (f" | {descartadas} sem data válida (descartados)" if descartadas else ""))

    # data máxima por ano (para o motor saber o mês de corte / mês parcial)
    q = pd.read_sql_query(
        "SELECT ano, MAX(mes) AS mes_max FROM execucao_mensal WHERE conselho = ? GROUP BY ano",
        conn, params=(conselho,))
    for _, r in q.iterrows():
        _meta_set(conn, f"diario_{int(r['ano'])}_mes_max", int(r["mes_max"]))
    for ano_v, dmax in datas_max.items():
        _meta_set(conn, f"diario_{ano_v}_data_max", dmax.date().isoformat())
    return resumo


def reconciliar(conn, conselho: str, log) -> pd.DataFrame:
    """Confere executado (Diário) x Realizado (orçamento) nas contas folha 6.2/6.3
    dos anos fechados. Grava a tabela `reconciliacao` e retorna o resultado."""
    orc = pd.read_sql_query(
        """SELECT ano, conta, conta_norm, descricao, realizado FROM orcamento_anual
           WHERE conselho = ? AND eh_folha = 1
             AND (conta LIKE '6.2%' OR conta LIKE '6.3%')""",
        conn, params=(conselho,))
    exec_ = pd.read_sql_query(
        """SELECT ano, conta, SUM(soma_d) AS d, SUM(soma_c) AS c FROM execucao_mensal
           WHERE conselho = ? AND (conta LIKE '6.2%' OR conta LIKE '6.3%')
           GROUP BY ano, conta""",
        conn, params=(conselho,))

    anos_fechados = sorted(a for a in orc["ano"].unique() if a < datetime.now().year)
    j = orc[orc["ano"].isin(anos_fechados)].merge(exec_, on=["ano", "conta"], how="left")
    j[["d", "c"]] = j[["d", "c"]].fillna(0.0)
    j["ramo"] = j["conta"].str[:3]
    j["executado_diario"] = j.apply(
        lambda r: (r["d"] - r["c"]) if r["ramo"] == "6.3" else (r["c"] - r["d"]), axis=1)
    j["diferenca"] = j["executado_diario"] - j["realizado"].fillna(0.0)
    j["bate"] = (j["diferenca"].abs() <= TOLERANCIA_RECONCILIACAO).astype(int)
    j["conselho"] = conselho

    conn.execute("DELETE FROM reconciliacao WHERE conselho = ?", (conselho,))
    j_out = j.rename(columns={"realizado": "realizado_orcamento"})[[
        "ano", "conselho", "conta", "descricao", "ramo",
        "realizado_orcamento", "executado_diario", "diferenca", "bate"]]
    j_out.to_sql("reconciliacao", conn, if_exists="append", index=False)

    log("\nReconciliação (contas folha 6.2/6.3, anos fechados):")
    for (ano, ramo), grupo in j_out.groupby(["ano", "ramo"]):
        relevantes = grupo[(grupo["realizado_orcamento"].abs() > 0.005)
                           | (grupo["executado_diario"].abs() > 0.005)]
        ok = int(relevantes["bate"].sum())
        log(f"  {ano} {ramo}: {ok}/{len(relevantes)} contas batem"
            + ("" if ok == len(relevantes) else "  <-- VERIFICAR DIVERGÊNCIAS"))
    return j_out


def importar_tudo(conselho: str = CONSELHO_PADRAO, log=print) -> dict:
    inicio = datetime.now()
    log(f"Importando dados reais ({conselho}) de: {CODIGOS_DIR}")
    log(f"Destino: {DADOS_REAIS_DB}\n")
    conn = get_conn()
    try:
        n_orc = importar_orcamento(conn, conselho, log)
        n_pc = importar_plano_contas(conn, conselho, log)
        resumo_diarios = importar_diarios(conn, conselho, log)
        rec = reconciliar(conn, conselho, log)

        _meta_set(conn, "ultima_importacao", inicio.isoformat(timespec="seconds"))
        _meta_set(conn, "conselho", conselho)
        _meta_set(conn, "codigos_dir", CODIGOS_DIR)
        divergentes = rec[(rec["bate"] == 0)
                          & ((rec["realizado_orcamento"].abs() > 0.005)
                             | (rec["executado_diario"].abs() > 0.005))]
        _meta_set(conn, "reconciliacao_divergencias", len(divergentes))
        conn.commit()

        dur = (datetime.now() - inicio).total_seconds()
        log(f"\nImportação concluída em {dur:,.0f}s.")
        return dict(orcamento=n_orc, plano_contas=n_pc, diarios=resumo_diarios,
                    reconciliacao_divergencias=len(divergentes))
    finally:
        conn.close()
