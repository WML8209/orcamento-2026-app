"""
Motor de Projeção de Fechamento 2026 — despesa (6.3) e receita (6.2).
Ver Orcamento2026.md.

Modelo oficial (M3, híbrido por natureza). Despesa:
  - PESSOAL            -> curva sazonal histórica + reajuste de data-base (parâmetro global)
  - CONTRATOS          -> run-rate dos últimos K meses completos + reajuste por conta
  - DIARIAS_PASSAGENS  -> curva sazonal histórica
  - EVENTOS (exames)   -> curva sazonal histórica
  - CAPITAL            -> curva sazonal, confiança baixa (informar cronograma via override)
  - DEMAIS             -> curva sazonal histórica

Receita:
  - COTA_PARTE / EXPLORACAO_SERVICOS / DEMAIS_CONTRIBUICOES / OUTRAS -> sazonal
  - FINANCEIRAS_RECEITA / CAPITAL_RECEITA -> run-rate (juros e amortizações
    acompanham o cenário corrente, não o perfil de anos anteriores)
  - PREVISAO_ADICIONAL -> método 'ytd' (conta de equilíbrio orçamentário: não
    realiza; fechamento = realizado acumulado, sem projeção)

Sinal do executado (regra validada na reconciliação): despesa = ΣD − ΣC;
receita = ΣC − ΣD — sempre nas contas folha.

Conferência (M2): curva sazonal pura para TODAS as contas; divergências
M3 x M2 acima de LIMIAR_DIVERGENCIA são destacadas para revisão.

Toda projeção carrega memória de cálculo (método, números e fallbacks usados).
Independente do Streamlit — usado pelo CLI projetar_fechamento.py e pelas telas.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
import json
import sqlite3

import pandas as pd

from core.config import DADOS_REAIS_DB, CONSELHO_PADRAO, ANO_ORCAMENTO

ANOS_HISTORICO = [2022, 2023, 2024, 2025]
ANOS_FALLBACK_NOMINAL = [2024, 2025]   # média nominal p/ contas de perfil concentrado (ex.: 13º)
K_MESES_RUNRATE = 3                    # run-rate de contratos: média dos últimos K meses completos
SHARE_ACUM_MINIMO = 0.20               # abaixo disso o método da razão é instável -> fallback aditivo
TAXA_EXECUCAO_FALLBACK = 0.90          # conta sem histórico e sem YTD: orçamento x esta taxa
LIMIAR_DIVERGENCIA = 0.10              # 10% entre M3 e M2 acende alerta
DIA_MES_COMPLETO = 28                  # data_max com dia >= 28 indica mês contábil completo

SCHEMA = """
CREATE TABLE IF NOT EXISTS projecao_config (
    conselho TEXT NOT NULL,
    conta TEXT NOT NULL,
    metodo TEXT,
    parametros_json TEXT,
    PRIMARY KEY (conselho, conta)
);

CREATE TABLE IF NOT EXISTS projecao_parametros (
    chave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS projecao_resultado (
    gerado_em TEXT,
    conselho TEXT NOT NULL,
    ano INTEGER NOT NULL,
    mes_corte INTEGER,
    conta TEXT NOT NULL,
    descricao TEXT,
    natureza TEXT,
    metodo TEXT,
    orcamento REAL,
    ytd REAL,
    proj_restante REAL,
    proj_fechamento REAL,
    proj_m2 REAL,
    divergencia_pct REAL,
    confianca TEXT,
    memoria TEXT,
    PRIMARY KEY (conselho, ano, conta)
);

CREATE TABLE IF NOT EXISTS projecao_mensal (
    conselho TEXT NOT NULL,
    ano INTEGER NOT NULL,
    conta TEXT NOT NULL,
    mes INTEGER NOT NULL,
    valor REAL,
    projetado INTEGER,   -- 0 = realizado (mes <= corte), 1 = projetado
    PRIMARY KEY (conselho, ano, conta, mes)
);
"""

RAMO_DESPESA = "6.3"
RAMO_RECEITA = "6.2"
RAMOS_ROTULOS = {RAMO_DESPESA: "Despesa", RAMO_RECEITA: "Receita"}

# Contas com tratamento específico independente do prefixo
EXCECOES_NATUREZA = {
    "6.3.1.3.02.01.011": "EVENTOS",  # Seleção/treinamento/organização de exames: sazonal por natureza
}

NATUREZAS_ROTULOS = {
    # Despesa (6.3)
    "PESSOAL": "Pessoal e Encargos",
    "CONTRATOS": "Contratos e Serviços",
    "DIARIAS_PASSAGENS": "Diárias e Passagens",
    "EVENTOS": "Eventos e Exames",
    "CAPITAL": "Despesas de Capital",
    "DEMAIS": "Demais Despesas Correntes",
    # Receita (6.2)
    "COTA_PARTE": "Cota-Parte dos CRCs",
    "DEMAIS_CONTRIBUICOES": "Demais Contribuições",
    "EXPLORACAO_SERVICOS": "Exploração de Bens e Serviços",
    "FINANCEIRAS_RECEITA": "Receitas Financeiras",
    "OUTRAS_RECEITAS": "Outras Receitas Correntes",
    "CAPITAL_RECEITA": "Receitas de Capital",
    "PREVISAO_ADICIONAL": "Previsão Adicional (equilíbrio)",
}

# Rótulos em português exibidos na tela/exportações — não altera as chaves
# internas ('runrate', 'override', 'ytd', ...) usadas no código e no banco.
METODO_ROTULOS = {
    "sazonal_reajuste": "Sazonal + Reajuste",
    "sazonal": "Sazonal",
    "runrate": "Média Móvel",
    "ytd": "Acumulado (sem projeção)",
    "override": "Fechamento Manual",
}


def natureza_da_conta(conta: str, ramo: str = RAMO_DESPESA) -> str:
    if ramo == RAMO_RECEITA:
        if conta.startswith("6.2.1.1.02"):
            return "COTA_PARTE"
        if conta.startswith("6.2.1.1"):
            return "DEMAIS_CONTRIBUICOES"
        if conta.startswith("6.2.1.2"):
            return "EXPLORACAO_SERVICOS"
        if conta.startswith("6.2.1.3"):
            return "FINANCEIRAS_RECEITA"
        if conta.startswith("6.2.2"):
            return "CAPITAL_RECEITA"
        if conta.startswith("6.2.3"):
            return "PREVISAO_ADICIONAL"
        return "OUTRAS_RECEITAS"
    if conta in EXCECOES_NATUREZA:
        return EXCECOES_NATUREZA[conta]
    if conta.startswith("6.3.1.1"):
        return "PESSOAL"
    if conta.startswith("6.3.1.3.02.03") or conta.startswith("6.3.1.3.02.04"):
        return "DIARIAS_PASSAGENS"
    if conta.startswith("6.3.1.3.02.01"):
        return "CONTRATOS"
    if conta.startswith("6.3.2"):
        return "CAPITAL"
    return "DEMAIS"


METODO_POR_NATUREZA = {
    # Despesa
    "PESSOAL": "sazonal_reajuste",
    "CONTRATOS": "runrate",
    "DIARIAS_PASSAGENS": "sazonal",
    "EVENTOS": "sazonal",
    "CAPITAL": "sazonal",
    "DEMAIS": "sazonal",
    # Receita
    "COTA_PARTE": "sazonal",
    "DEMAIS_CONTRIBUICOES": "sazonal",
    "EXPLORACAO_SERVICOS": "sazonal",
    "FINANCEIRAS_RECEITA": "runrate",
    "OUTRAS_RECEITAS": "sazonal",
    "CAPITAL_RECEITA": "runrate",
    "PREVISAO_ADICIONAL": "ytd",
}


@dataclass
class ProjecaoConta:
    conta: str
    descricao: str
    natureza: str
    metodo: str
    orcamento: float
    ytd: float
    proj_restante: float
    proj_fechamento: float
    proj_m2: float
    divergencia_pct: float
    confianca: str          # 'alta' | 'media' | 'baixa'
    memoria: str
    restante_por_mes: dict = field(default_factory=dict)
    realizado_por_mes: dict = field(default_factory=dict)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DADOS_REAIS_DB)
    conn.executescript(SCHEMA)
    return conn


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _meta(conn, chave: str, default=None):
    row = conn.execute("SELECT valor FROM importacao_meta WHERE chave = ?", (chave,)).fetchone()
    return row[0] if row else default


def _parametro(conn, chave: str, default=None):
    row = conn.execute("SELECT valor FROM projecao_parametros WHERE chave = ?", (chave,)).fetchone()
    return row[0] if row else default


def mes_corte_padrao(conn, ano: int) -> int:
    """Último mês COMPLETO do Diário: se a data máxima de lançamento do ano cair
    antes do dia DIA_MES_COMPLETO, o mês é considerado parcial e recua um mês."""
    data_max = _meta(conn, f"diario_{ano}_data_max")
    if data_max:
        d = date.fromisoformat(data_max)
        return d.month if d.day >= DIA_MES_COMPLETO else max(d.month - 1, 1)
    mes_max = _meta(conn, f"diario_{ano}_mes_max")
    return max(int(mes_max) - 1, 1) if mes_max else 12


def _carregar_dados(conn, conselho: str, ano: int, ramo: str = RAMO_DESPESA):
    """Contas folha do ramo no orçamento do ano + execução mensal (histórico e
    ano), com o valor já no sinal certo: despesa = D−C, receita = C−D."""
    sinal = "(soma_d - soma_c)" if ramo == RAMO_DESPESA else "(soma_c - soma_d)"
    contas = pd.read_sql_query(
        """SELECT conta, descricao, orcamento_inicial AS orcamento, realizado
           FROM orcamento_anual
           WHERE conselho = ? AND ano = ? AND eh_folha = 1 AND conta LIKE ? || '%'""",
        conn, params=(conselho, ano, ramo))
    exec_ = pd.read_sql_query(
        f"""SELECT ano, mes, conta, {sinal} AS valor
            FROM execucao_mensal
            WHERE conselho = ? AND conta LIKE ? || '%'""",
        conn, params=(conselho, ramo))
    return contas, exec_


def _mensal(exec_: pd.DataFrame, conta: str, ano: int) -> pd.Series:
    """Série mensal (1..12) da conta no ano; meses sem movimento = 0."""
    sub = exec_[(exec_["conta"] == conta) & (exec_["ano"] == ano)]
    s = pd.Series(0.0, index=range(1, 13))
    for _, r in sub.iterrows():
        s[int(r["mes"])] += float(r["valor"])
    return s


def _perfil_sazonal(exec_: pd.DataFrame, conta: str) -> tuple[pd.Series | None, list[int]]:
    """Perfil médio (share de cada mês no total anual) nos anos de histórico com
    total relevante. Retorna (perfil ou None, anos usados)."""
    perfis, anos_usados = [], []
    for ano in ANOS_HISTORICO:
        s = _mensal(exec_, conta, ano)
        total = s.sum()
        if abs(total) > 0.01:
            perfis.append(s / total)
            anos_usados.append(ano)
    if not perfis:
        return None, []
    return pd.concat(perfis, axis=1).mean(axis=1), anos_usados


def _fator_grupo(exec_: pd.DataFrame, contas_grupo: list[str], mes_corte: int, ano: int) -> float:
    """Crescimento do grupo: YTD do ano projetado ÷ YTD do ano anterior (mesmos
    meses), limitado a [0.8, 1.3]. Usado só no fallback aditivo (nominal)."""
    ytd_atual = ytd_ant = 0.0
    for conta in contas_grupo:
        ytd_atual += _mensal(exec_, conta, ano).loc[1:mes_corte].sum()
        ytd_ant += _mensal(exec_, conta, ano - 1).loc[1:mes_corte].sum()
    if ytd_ant <= 0.01 or ytd_atual <= 0.01:
        return 1.0
    return min(max(ytd_atual / ytd_ant, 0.8), 1.3)


def _projetar_sazonal(exec_: pd.DataFrame, conta: str, ytd: float, mes_corte: int,
                      orcamento: float, fator_grupo: float = 1.0):
    """Método sazonal com cadeia de fallbacks. Retorna
    (fechamento, restante_por_mes, confianca, memoria)."""
    perfil, anos_usados = _perfil_sazonal(exec_, conta)
    meses_restantes = list(range(mes_corte + 1, 13))

    if perfil is not None:
        share_acum = float(perfil.loc[1:mes_corte].sum())
        if share_acum >= SHARE_ACUM_MINIMO and ytd > 0.01:
            base_anual = ytd / share_acum
            restante = {m: base_anual * float(perfil.loc[m]) for m in meses_restantes}
            fechamento = ytd + sum(restante.values())
            conf = "alta" if len(anos_usados) >= 3 else "media"
            memoria = (f"Sazonal (razão): Acumulado jan-{mes_corte:02d} = R$ {_fmt(ytd)}; "
                       f"perfil {anos_usados} acumula {share_acum:.1%} até o mês {mes_corte}; "
                       f"fechamento = {_fmt(ytd)} / {share_acum:.4f} = R$ {_fmt(fechamento)}.")
            return fechamento, restante, conf, memoria

        # Fallback aditivo: média nominal dos meses restantes nos anos recentes
        nominais = []
        for ano_h in ANOS_FALLBACK_NOMINAL:
            s = _mensal(exec_, conta, ano_h)
            if abs(s.sum()) > 0.01:
                nominais.append(s.loc[mes_corte + 1:12].reindex(meses_restantes, fill_value=0.0))
        if nominais:
            media = pd.concat(nominais, axis=1).mean(axis=1) * fator_grupo
            restante = {m: float(media.get(m, 0.0)) for m in meses_restantes}
            fechamento = ytd + sum(restante.values())
            memoria = (f"Sazonal (aditivo): Acumulado = R$ {_fmt(ytd)}; perfil histórico concentrado "
                       f"após o mês {mes_corte} (acum. {float(perfil.loc[1:mes_corte].sum()):.1%}) — usa média "
                       f"nominal {ANOS_FALLBACK_NOMINAL} dos meses restantes x fator do grupo "
                       f"{fator_grupo:.2f} = R$ {_fmt(sum(restante.values()))}; "
                       f"fechamento = R$ {_fmt(fechamento)}.")
            return fechamento, restante, "media", memoria

    # Sem histórico utilizável
    if ytd > 0.01:
        fechamento = ytd / (mes_corte / 12.0)
        rest_total = fechamento - ytd
        n = len(meses_restantes) or 1
        restante = {m: rest_total / n for m in meses_restantes}
        memoria = (f"Sem histórico: projeção uniforme — Acumulado R$ {_fmt(ytd)} ÷ ({mes_corte}/12) "
                   f"= R$ {_fmt(fechamento)}.")
        return fechamento, restante, "baixa", memoria

    fechamento = orcamento * TAXA_EXECUCAO_FALLBACK
    n = len(meses_restantes) or 1
    restante = {m: fechamento / n for m in meses_restantes}
    memoria = (f"Sem histórico e sem execução: orçamento R$ {_fmt(orcamento)} x taxa de "
               f"execução padrão {TAXA_EXECUCAO_FALLBACK:.0%} = R$ {_fmt(fechamento)}.")
    return fechamento, restante, "baixa", memoria


def _projetar_runrate(exec_: pd.DataFrame, conta: str, ytd: float, mes_corte: int, ano: int,
                      reajuste_pct: float = 0.0, mes_reajuste: int | None = None):
    """Run-rate: média dos últimos K meses completos x meses restantes, com
    reajuste opcional a partir de um mês."""
    s = _mensal(exec_, conta, ano)
    ini = max(mes_corte - K_MESES_RUNRATE + 1, 1)
    janela = s.loc[ini:mes_corte]
    base = float(janela.mean()) if len(janela) else 0.0
    meses_restantes = list(range(mes_corte + 1, 13))
    restante = {}
    for m in meses_restantes:
        fator = (1 + reajuste_pct / 100.0) if (mes_reajuste and m >= mes_reajuste) else 1.0
        restante[m] = base * fator
    fechamento = ytd + sum(restante.values())
    txt_reaj = (f", com reajuste de {reajuste_pct:.2f}% a partir do mês {mes_reajuste}"
                if mes_reajuste and reajuste_pct else "")
    memoria = (f"Média Móvel: média mensal dos meses {ini}-{mes_corte} = R$ {_fmt(base)}; "
               f"Acumulado R$ {_fmt(ytd)} + {len(meses_restantes)} meses x base{txt_reaj} "
               f"= R$ {_fmt(fechamento)}.")
    return fechamento, restante, "alta" if base > 0 else "baixa", memoria


def _config_conta(conn, conselho: str, conta: str) -> dict:
    row = conn.execute(
        "SELECT metodo, parametros_json FROM projecao_config WHERE conselho = ? AND conta = ?",
        (conselho, conta)).fetchone()
    if not row:
        return {}
    cfg = {"metodo": row[0]} if row[0] else {}
    if row[1]:
        try:
            cfg.update(json.loads(row[1]))
        except json.JSONDecodeError:
            pass
    return cfg


def projetar_fechamento(conselho: str = CONSELHO_PADRAO, ano: int = ANO_ORCAMENTO,
                        mes_corte: int | None = None, persistir: bool = True,
                        ramo: str = RAMO_DESPESA) -> list[ProjecaoConta]:
    """Roda M3 (oficial) + M2 (conferência) para todas as contas folha do ramo
    (6.3 despesa / 6.2 receita) no ano. Retorna a lista de ProjecaoConta e, se
    persistir=True, grava projecao_resultado (sem tocar no outro ramo)."""
    conn = get_conn()
    try:
        if mes_corte is None:
            mes_corte = mes_corte_padrao(conn, ano)

        contas, exec_ = _carregar_dados(conn, conselho, ano, ramo)

        # Parâmetros globais de pessoal (data-base) — só fazem sentido na despesa
        pes_pct = float(_parametro(conn, "pessoal_reajuste_pct", 0) or 0) if ramo == RAMO_DESPESA else 0.0
        pes_mes = _parametro(conn, "pessoal_mes_reajuste") if ramo == RAMO_DESPESA else None
        pes_mes = int(pes_mes) if pes_mes else None

        # Fator de crescimento por natureza (para o fallback aditivo)
        contas["natureza"] = contas["conta"].map(lambda c: natureza_da_conta(c, ramo))
        fatores = {
            nat: _fator_grupo(exec_, grupo["conta"].tolist(), mes_corte, ano)
            for nat, grupo in contas.groupby("natureza")
        }

        resultados = []
        for _, row in contas.iterrows():
            conta, descricao, orcamento = row["conta"], row["descricao"], float(row["orcamento"] or 0)
            natureza = row["natureza"]
            serie_ano = _mensal(exec_, conta, ano)
            ytd = float(serie_ano.loc[1:mes_corte].sum())
            realizado_por_mes = {m: float(serie_ano.loc[m]) for m in range(1, mes_corte + 1)}
            cfg = _config_conta(conn, conselho, conta)
            metodo = cfg.get("metodo") or METODO_POR_NATUREZA[natureza]

            # --- M2 (conferência): sazonal puro (exceto contas 'ytd', em que
            # a conferência não se aplica — conta de equilíbrio não realiza) ---
            if metodo == "ytd":
                m2 = ytd
            else:
                m2, _, _, _ = _projetar_sazonal(exec_, conta, ytd, mes_corte, orcamento,
                                                fatores.get(natureza, 1.0))

            # --- M3 (oficial) ---
            if metodo == "ytd" and "override_fechamento" not in cfg:
                fechamento = ytd
                restante = {}
                conf = "alta"
                memoria = ("Conta de equilíbrio orçamentário (Previsão Adicional): não há "
                           f"realização a projetar — fechamento = realizado acumulado "
                           f"(R$ {_fmt(ytd)}).")
            elif "override_fechamento" in cfg:
                fechamento = float(cfg["override_fechamento"])
                residual = fechamento - ytd
                meses_rest = list(range(mes_corte + 1, 13))
                perfil_ovr, _ = _perfil_sazonal(exec_, conta)
                share_rest = float(perfil_ovr.loc[mes_corte + 1:12].sum()) if perfil_ovr is not None else 0.0
                if meses_rest and share_rest > 0.01:
                    restante = {m: residual * float(perfil_ovr.loc[m]) / share_rest for m in meses_rest}
                    dist_txt = "perfil sazonal histórico"
                elif meses_rest:
                    restante = {m: residual / len(meses_rest) for m in meses_rest}
                    dist_txt = "uniforme"
                else:
                    restante = {}
                    dist_txt = "—"
                conf = "alta"
                memoria = (f"Fechamento Manual: R$ {_fmt(fechamento)} "
                           f"(distribuição mensal do restante: {dist_txt}). "
                           f"Justificativa: {cfg.get('justificativa', '(não informada)')}")
                metodo = "override"
            elif metodo == "runrate":
                fechamento, restante, conf, memoria = _projetar_runrate(
                    exec_, conta, ytd, mes_corte, ano,
                    reajuste_pct=float(cfg.get("reajuste_pct", 0) or 0),
                    mes_reajuste=int(cfg["mes_reajuste"]) if cfg.get("mes_reajuste") else None)
            elif metodo == "sazonal_reajuste":
                fechamento, restante, conf, memoria = _projetar_sazonal(
                    exec_, conta, ytd, mes_corte, orcamento, fatores.get(natureza, 1.0))
                if pes_mes and pes_pct:
                    acrescimo = sum(v * (pes_pct / 100.0) for m, v in restante.items() if m >= pes_mes)
                    restante = {m: v * (1 + pes_pct / 100.0) if m >= pes_mes else v
                                for m, v in restante.items()}
                    fechamento += acrescimo
                    memoria += (f" Reajuste de data-base: +{pes_pct:.2f}% a partir do mês "
                                f"{pes_mes} (+R$ {_fmt(acrescimo)}).")
            else:  # sazonal
                fechamento, restante, conf, memoria = _projetar_sazonal(
                    exec_, conta, ytd, mes_corte, orcamento, fatores.get(natureza, 1.0))

            if natureza == "CAPITAL" and metodo != "override":
                conf = "baixa"
                memoria += " [CAPITAL: projeção estatística é frágil — informar cronograma via Fechamento Manual.]"

            divergencia = abs(fechamento - m2) / max(abs(m2), 1.0)
            resultados.append(ProjecaoConta(
                conta=conta, descricao=descricao, natureza=natureza, metodo=metodo,
                orcamento=orcamento, ytd=ytd, proj_restante=fechamento - ytd,
                proj_fechamento=fechamento, proj_m2=m2, divergencia_pct=divergencia,
                confianca=conf, memoria=memoria, restante_por_mes=restante,
                realizado_por_mes=realizado_por_mes,
            ))

        if persistir:
            gerado_em = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                "DELETE FROM projecao_resultado WHERE conselho = ? AND ano = ? AND conta LIKE ? || '%'",
                (conselho, ano, ramo))
            conn.executemany(
                """INSERT INTO projecao_resultado
                   (gerado_em, conselho, ano, mes_corte, conta, descricao, natureza, metodo,
                    orcamento, ytd, proj_restante, proj_fechamento, proj_m2,
                    divergencia_pct, confianca, memoria)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(gerado_em, conselho, ano, mes_corte, r.conta, r.descricao, r.natureza,
                  r.metodo, r.orcamento, r.ytd, r.proj_restante, r.proj_fechamento,
                  r.proj_m2, r.divergencia_pct, r.confianca, r.memoria) for r in resultados])

            # Curva mensal: realizado (1..corte) + projetado (corte+1..12)
            conn.execute(
                "DELETE FROM projecao_mensal WHERE conselho = ? AND ano = ? AND conta LIKE ? || '%'",
                (conselho, ano, ramo))
            linhas_mensal = []
            for r in resultados:
                for m in range(1, 13):
                    if m <= mes_corte:
                        valor, proj = r.realizado_por_mes.get(m, 0.0), 0
                    else:
                        valor, proj = float(r.restante_por_mes.get(m, 0.0)), 1
                    linhas_mensal.append((conselho, ano, r.conta, m, valor, proj))
            conn.executemany(
                """INSERT INTO projecao_mensal (conselho, ano, conta, mes, valor, projetado)
                   VALUES (?, ?, ?, ?, ?, ?)""", linhas_mensal)
            conn.commit()

        return resultados
    finally:
        conn.close()


def carregar_resultado(conselho: str = CONSELHO_PADRAO, ano: int = ANO_ORCAMENTO,
                       ramo: str | None = None) -> pd.DataFrame:
    """Última projeção persistida (tabela projecao_resultado). Se `ramo` for
    informado ('6.3' ou '6.2'), filtra só as contas daquele ramo."""
    conn = get_conn()
    try:
        if ramo:
            return pd.read_sql_query(
                """SELECT * FROM projecao_resultado
                   WHERE conselho = ? AND ano = ? AND conta LIKE ? || '%' ORDER BY conta""",
                conn, params=(conselho, ano, ramo))
        return pd.read_sql_query(
            "SELECT * FROM projecao_resultado WHERE conselho = ? AND ano = ? ORDER BY conta",
            conn, params=(conselho, ano))
    finally:
        conn.close()


def carregar_mensal(conselho: str = CONSELHO_PADRAO, ano: int = ANO_ORCAMENTO,
                    ramo: str = RAMO_DESPESA) -> pd.DataFrame:
    """Curva mensal persistida (realizado + projetado), já com natureza e
    descrição de cada conta (join com projecao_resultado)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """SELECT m.conta, r.descricao, r.natureza, m.mes, m.valor, m.projetado
               FROM projecao_mensal m
               JOIN projecao_resultado r
                 ON r.conselho = m.conselho AND r.ano = m.ano AND r.conta = m.conta
               WHERE m.conselho = ? AND m.ano = ? AND m.conta LIKE ? || '%'
               ORDER BY m.conta, m.mes""",
            conn, params=(conselho, ano, ramo))
    finally:
        conn.close()


def carregar_configs(conselho: str = CONSELHO_PADRAO) -> dict:
    """{conta: {'metodo': ..., **parametros}} das configurações salvas."""
    conn = get_conn()
    try:
        out = {}
        for conta, metodo, pjson in conn.execute(
                "SELECT conta, metodo, parametros_json FROM projecao_config WHERE conselho = ?",
                (conselho,)):
            cfg = {"metodo": metodo} if metodo else {}
            if pjson:
                try:
                    cfg.update(json.loads(pjson))
                except json.JSONDecodeError:
                    pass
            out[conta] = cfg
        return out
    finally:
        conn.close()


def salvar_config_conta(conta: str, metodo: str | None = None,
                        parametros: dict | None = None,
                        conselho: str = CONSELHO_PADRAO):
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO projecao_config (conselho, conta, metodo, parametros_json)
               VALUES (?, ?, ?, ?)""",
            (conselho, conta, metodo, json.dumps(parametros or {}, ensure_ascii=False)))
        conn.commit()
    finally:
        conn.close()


def remover_config_conta(conta: str, conselho: str = CONSELHO_PADRAO):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM projecao_config WHERE conselho = ? AND conta = ?",
                     (conselho, conta))
        conn.commit()
    finally:
        conn.close()


def carregar_parametros() -> dict:
    conn = get_conn()
    try:
        return dict(conn.execute("SELECT chave, valor FROM projecao_parametros"))
    finally:
        conn.close()


def salvar_parametro(chave: str, valor):
    conn = get_conn()
    try:
        if valor is None or valor == "":
            conn.execute("DELETE FROM projecao_parametros WHERE chave = ?", (chave,))
        else:
            conn.execute("INSERT OR REPLACE INTO projecao_parametros (chave, valor) VALUES (?, ?)",
                         (chave, str(valor)))
        conn.commit()
    finally:
        conn.close()


def resumo_por_natureza(resultados: list[ProjecaoConta]) -> pd.DataFrame:
    df = pd.DataFrame([{
        "natureza": NATUREZAS_ROTULOS.get(r.natureza, r.natureza),
        "orcamento": r.orcamento, "ytd": r.ytd, "fechamento": r.proj_fechamento,
        "m2": r.proj_m2,
    } for r in resultados])
    agg = df.groupby("natureza", sort=False).sum()
    agg["exec_projetada_pct"] = agg["fechamento"] / agg["orcamento"].where(agg["orcamento"] != 0)
    return agg.sort_values("fechamento", ascending=False)
