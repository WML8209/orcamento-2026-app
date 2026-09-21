"""
Importador dos dados reais do CFC para o banco compacto data/dados_reais.db.
Ver Orcamento2026.md.

Duas fontes, um caminho só:

  - `FonteCSV` — os CSVs baixados pelos scripts `baixar_*.py` na pasta
    DECONT/Códigos (caminho histórico, ver Checklist_Atualizacao_Mensal.md).
  - `FonteAPI` — consulta direta à API de dados abertos do CFC, só do
    conselho projetado (`core/fonte_api.py`). É o que alimenta o botão
    "Atualizar Dados" da tela Início, e o único caminho que funciona no app
    publicado, onde a pasta `Códigos` não existe.

As duas entregam DataFrames com as MESMAS colunas, de modo que agregação,
reconciliação e gravação abaixo são idênticas para ambas — a fonte muda de
onde os dados vêm, nunca como são tratados.

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

from core import fonte_api
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


# ---------------------------------------------------------------------------
# Fontes de dados
# ---------------------------------------------------------------------------

class FonteCSV:
    """CSVs da pasta Códigos, gerados pelos scripts `baixar_*.py`.

    Cobre todos os anos e conselhos que os scripts baixaram, por isso
    `anos = None`: a importação substitui a base inteira do conselho."""

    nome = "CSVs da pasta Códigos"
    anos = None          # None = a fonte cobre todo o histórico disponível
    BLOCO = 1_000_000    # linhas por bloco — os CSVs do Diário passam de 150 MB

    def __init__(self, codigos_dir: Path | None = None):
        self.codigos_dir = Path(codigos_dir) if codigos_dir else CODIGOS_DIR

    def descricao(self) -> str:
        return f"{self.nome} ({self.codigos_dir})"

    def orcamento(self, conselho: str, log) -> pd.DataFrame:
        caminho = self.codigos_dir / "OrçamentoAtualizado" / "orcamento_2022_2026.csv"
        log(f"Lendo {caminho.name} ...")
        df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype={"Conta": str})
        return df[df["Conselho"] == conselho].copy()

    def plano_contas(self, conselho: str, log) -> pd.DataFrame:
        caminho = self.codigos_dir / "PlanoContas" / "PlanoContas_2021_2024.csv"
        log(f"Lendo {caminho.name} (em blocos) ...")
        partes = []
        for bloco in pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype=str,
                                 chunksize=500_000):
            c = bloco[bloco["Conselho"] == conselho]
            if not c.empty:
                partes.append(c)
        if not partes:
            raise FileNotFoundError(
                f"Nenhuma conta de {conselho} em {caminho.name}.")
        return pd.concat(partes, ignore_index=True)

    def lotes_diario(self, conselho: str, log):
        """Um lote por arquivo Diario_*.csv, cada um lido em blocos."""
        pasta = self.codigos_dir / "Diário"
        arquivos = sorted(pasta.glob("Diario_*.csv"))
        if not arquivos:
            raise FileNotFoundError(f"Nenhum Diario_*.csv encontrado em {pasta}")
        for arq in arquivos:
            yield arq.name, self._blocos(arq, conselho, log)

    def _blocos(self, arq: Path, conselho: str, log):
        log(f"Lendo {arq.name} (em blocos) ...")
        usecols = ["Conselho", "Conta", "D/C", "Data Lançamento", "Soma de Valor"]
        for bloco in pd.read_csv(arq, sep=";", encoding="utf-8-sig",
                                 usecols=usecols, dtype=str, chunksize=self.BLOCO):
            c = bloco[bloco["Conselho"] == conselho]
            if not c.empty:
                yield c.copy()


class FonteAPI:
    """API de dados abertos do CFC, consultada só para o conselho projetado.

    `anos` é sempre uma lista concreta: a importação substitui **apenas**
    esses anos no banco, preservando o histórico já importado. É o que
    permite a atualização mensal rápida (só o ano corrente, ~10 s) sem
    rebaixar 2022-2025, que não mudam mais."""

    nome = "API de dados abertos do CFC"

    def __init__(self, anos: list[int] | None = None):
        self.anos = sorted(anos or fonte_api.ANOS_PADRAO)

    def descricao(self) -> str:
        return f"{self.nome} — anos {self.anos}"

    def orcamento(self, conselho: str, log) -> pd.DataFrame:
        log("Buscando orçamento na API ...")
        return fonte_api.baixar_orcamento(conselho, self.anos, log)

    def plano_contas(self, conselho: str, log) -> pd.DataFrame:
        log("Buscando plano de contas na API ...")
        return fonte_api.baixar_plano_contas(conselho, self.anos, log)

    def lotes_diario(self, conselho: str, log):
        """Um lote por ano. Cada ano cabe folgado na memória depois de
        filtrado pelo conselho (o CFC/2026 inteiro tem ~50 mil linhas), então
        o 'bloco' é o próprio ano."""
        log("Buscando o Diário na API ...")
        for ano in self.anos:
            yield f"Diário {ano} (API)", self._bloco_ano(conselho, ano, log)

    def _bloco_ano(self, conselho: str, ano: int, log):
        df = fonte_api.baixar_diario(conselho, ano, log)
        if not df.empty:
            yield df


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


def _limpar(conn, tabela: str, conselho: str, anos: list[int] | None):
    """Apaga o que vai ser reposto: a base inteira do conselho quando a fonte
    cobre todo o histórico, ou só os anos que ela traz quando é parcial —
    caso contrário uma atualização de um ano só apagaria 2022-2025."""
    if anos is None:
        conn.execute(f"DELETE FROM {tabela} WHERE conselho = ?", (conselho,))
        return
    marcadores = ",".join("?" * len(anos))
    conn.execute(f"DELETE FROM {tabela} WHERE conselho = ? AND ano IN ({marcadores})",
                 (conselho, *anos))


def importar_orcamento(conn, conselho: str, log, fonte) -> int:
    df = fonte.orcamento(conselho, log).copy()
    df["conta_norm"] = _norm(df["Conta"])
    df["eh_folha"] = (df["conta_norm"].str.len() == 11).astype(int)
    df = df.rename(columns={
        "Ano": "ano", "Conselho": "conselho", "Conta": "conta",
        "Descrição": "descricao", "Orçamento Inicial": "orcamento_inicial",
        "Realizado": "realizado",
    })[["ano", "conselho", "conta", "conta_norm", "descricao",
        "orcamento_inicial", "realizado", "eh_folha"]]
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    _limpar(conn, "orcamento_anual", conselho, fonte.anos)
    df.to_sql("orcamento_anual", conn, if_exists="append", index=False)
    log(f"  orcamento_anual: {len(df)} linhas ({conselho}), anos "
        f"{sorted(df['ano'].dropna().unique().tolist())}")
    return len(df)


def importar_plano_contas(conn, conselho: str, log, fonte) -> int:
    df = fonte.plano_contas(conselho, log).copy()
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
    colunas = ["conselho", "conta", "conta_norm", "descricao",
               "grupo2", "grupo3", "grupo4", "ano_ref"]
    df = df[colunas]

    if fonte.anos is not None:
        # Fonte parcial: o plano de contas é indexado por conta (sem ano), então
        # substituir tudo pelo recorte de um ano só perderia contas extintas
        # que ainda descrevem lançamentos do histórico. Funde preferindo o
        # ano_ref mais recente.
        antigo = pd.read_sql_query(
            "SELECT * FROM plano_contas_real WHERE conselho = ?", conn,
            params=(conselho,))
        if not antigo.empty:
            df = (pd.concat([antigo[colunas], df], ignore_index=True)
                    .sort_values("ano_ref")
                    .drop_duplicates(subset=["conselho", "conta"], keep="last"))
    conn.execute("DELETE FROM plano_contas_real WHERE conselho = ?", (conselho,))
    df.to_sql("plano_contas_real", conn, if_exists="append", index=False)
    log(f"  plano_contas_real: {len(df)} contas distintas ({conselho})")
    return len(df)


def importar_diarios(conn, conselho: str, log, fonte) -> dict:
    _limpar(conn, "execucao_mensal", conselho, fonte.anos)
    resumo = {}
    datas_max: dict[int, pd.Timestamp] = {}

    for rotulo, blocos in fonte.lotes_diario(conselho, log):
        partes = []
        descartadas = 0
        for bloco in blocos:
            c = bloco.copy()
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
            log(f"  {rotulo}: nenhum lançamento de {conselho}")
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

        # Uma fonte parcial declara os anos que traz; um lançamento fora deles
        # (ex.: o Diário 2026 que ainda carrega ajustes datados de 2025) não
        # pode entrar, porque o DELETE não limpou aquele ano e viraria linha
        # duplicada/conflitante na chave primária.
        if fonte.anos is not None:
            fora = out[~out["ano"].isin(fonte.anos)]
            if not fora.empty:
                log(f"  {rotulo}: {int(fora['n_lancamentos'].sum())} lançamento(s) "
                    f"datados de {sorted(fora['ano'].unique().tolist())} ignorados "
                    f"(fora dos anos atualizados)")
                out = out[out["ano"].isin(fonte.anos)]
            datas_max = {a: d for a, d in datas_max.items() if a in fonte.anos}

        out.to_sql("execucao_mensal", conn, if_exists="append", index=False)

        n_lanc = int(out["n_lancamentos"].sum())
        anos = sorted(out["ano"].unique().tolist())
        resumo[rotulo] = dict(linhas_agregadas=len(out), lancamentos=n_lanc,
                              anos=anos, descartadas=descartadas)
        log(f"  {rotulo}: {n_lanc:,} lançamentos ({conselho}) -> {len(out)} linhas conta×mês"
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


def importar_tudo(conselho: str = CONSELHO_PADRAO, log=print, fonte=None) -> dict:
    """Importa tudo o que a `fonte` traz para o dados_reais.db e reconcilia.

    `fonte` padrão é `FonteCSV()` — o caminho histórico do CLI. As telas
    passam `FonteAPI([...])` para buscar direto na API do CFC."""
    fonte = fonte or FonteCSV()
    inicio = datetime.now()
    log(f"Importando dados reais ({conselho}) de: {fonte.descricao()}")
    log(f"Destino: {DADOS_REAIS_DB}\n")
    conn = get_conn()
    try:
        n_orc = importar_orcamento(conn, conselho, log, fonte)
        n_pc = importar_plano_contas(conn, conselho, log, fonte)
        resumo_diarios = importar_diarios(conn, conselho, log, fonte)
        rec = reconciliar(conn, conselho, log)

        _meta_set(conn, "ultima_importacao", inicio.isoformat(timespec="seconds"))
        _meta_set(conn, "conselho", conselho)
        _meta_set(conn, "fonte", fonte.descricao())
        if isinstance(fonte, FonteCSV):
            _meta_set(conn, "codigos_dir", fonte.codigos_dir)
        else:
            # A pasta Códigos não participou desta importação — o caminho
            # antigo ficaria como se ainda fosse a origem dos dados.
            conn.execute("DELETE FROM importacao_meta WHERE chave = 'codigos_dir'")
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


def importar_da_api(conselho: str = CONSELHO_PADRAO, anos: list[int] | None = None,
                    log=print) -> dict:
    """Atalho para o caminho novo: busca na API e importa. Usado pelo botão
    "Atualizar Dados" da tela Início e por `importar_dados.py --api`."""
    return importar_tudo(conselho=conselho, log=log, fonte=FonteAPI(anos))
