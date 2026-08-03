"""
Agente de IA — análise da Projeção de Fechamento 2026 (despesa + receita).

Monta um resumo condensado dos resultados já calculados por
core.projecao_engine (não recalcula nada) e pede a um modelo de linguagem,
via API do OpenRouter, um relatório em Markdown explicando a projeção e
possíveis medidas mitigadoras em caso de déficit orçamentário projetado.

Independente do Streamlit — chamado pela tela pages/fechamento.py.
"""
import pandas as pd
import requests

from core import config
from core.config import ANO_ORCAMENTO, CONSELHO_PADRAO
from core.formatos import fmt_brl, fmt_num_br, MESES_PT
from core.projecao_engine import (LIMIAR_DIVERGENCIA, LIMIAR_MATERIALIDADE,
                                  NATUREZAS_ROTULOS)

TOP_N_ALERTAS = 15


class AgenteIAError(Exception):
    """Erro amigável (chave ausente, rede, timeout, erro da API) — capturado
    em pages/fechamento.py para exibir st.error sem stack trace."""


def _fmt_pct(p) -> str:
    if p is None or p != p:  # NaN
        return "—"
    return f"{p * 100:,.1f}%".replace(",", "_").replace(".", ",").replace("_", ".")


def _linha_totais(df: pd.DataFrame, mes_corte: int) -> str:
    orc = float(df["orcamento"].sum())
    ytd = float(df["ytd"].sum())
    m3 = float(df["proj_fechamento"].sum())
    m2 = float(df["proj_m2"].sum())
    pct_exec = (m3 / orc) if orc else None
    return (f"- Orçamento: {fmt_brl(orc)}\n"
            f"- Realizado até {MESES_PT.get(mes_corte, mes_corte)}: {fmt_brl(ytd)}\n"
            f"- Fechamento projetado (M3): {fmt_brl(m3)} ({_fmt_pct(pct_exec)} do orçamento)\n"
            f"- Conferência (M2, sazonal puro): {fmt_brl(m2)}\n")


def _tabela_por_natureza(df: pd.DataFrame) -> str:
    linhas = ["| Natureza | Nº contas | Orçamento | Realizado (YTD) | Fechamento (M3) | % Exec. | Conferência (M2) |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for nat in NATUREZAS_ROTULOS:
        sub = df[df["natureza"] == nat]
        if sub.empty:
            continue
        orc, ytd = float(sub["orcamento"].sum()), float(sub["ytd"].sum())
        m3, m2 = float(sub["proj_fechamento"].sum()), float(sub["proj_m2"].sum())
        pct = (m3 / orc) if orc else None
        linhas.append(f"| {NATUREZAS_ROTULOS[nat]} | {len(sub)} | {fmt_brl(orc)} | "
                      f"{fmt_brl(ytd)} | {fmt_brl(m3)} | {_fmt_pct(pct)} | {fmt_brl(m2)} |")
    return "\n".join(linhas)


def _tabela_confianca(df: pd.DataFrame) -> str:
    linhas = ["| Confiança | Nº contas | Fechamento projetado (M3) |", "|---|---:|---:|"]
    for nivel in ("alta", "media", "baixa"):
        sub = df[df["confianca"] == nivel]
        if sub.empty:
            continue
        linhas.append(f"| {nivel} | {len(sub)} | {fmt_brl(float(sub['proj_fechamento'].sum()))} |")
    return "\n".join(linhas)


def _contas_divergentes(df: pd.DataFrame, rotulo_ramo: str) -> pd.DataFrame:
    d = df.copy()
    d["material"] = d[["proj_fechamento", "proj_m2"]].abs().max(axis=1) > LIMIAR_MATERIALIDADE
    d = d[(d["divergencia_pct"] > LIMIAR_DIVERGENCIA) & d["material"]].copy()
    d["ramo"] = rotulo_ramo
    return d


def _bloco_lista_contas(df: pd.DataFrame, colunas_extra: str) -> str:
    """df já filtrado e ordenado; colunas_extra é 'divergencia' ou 'confianca'."""
    if df.empty:
        return "Nenhuma conta nessa condição.\n"
    top = df.reindex(df["proj_fechamento"].abs().sort_values(ascending=False).index).head(TOP_N_ALERTAS)
    linhas = []
    for _, r in top.iterrows():
        extra = (f" · divergência M3×M2: {_fmt_pct(r['divergencia_pct'])}"
                 if colunas_extra == "divergencia" else f" · confiança: {r['confianca']}")
        linhas.append(f"- [{r['ramo']}] `{r['conta']}` — {r['descricao']}: "
                      f"M3 {fmt_brl(r['proj_fechamento'])}, M2 {fmt_brl(r['proj_m2'])}{extra}")
    restante = len(df) - len(top)
    if restante > 0:
        valor_restante = float(df.iloc[len(top):]["proj_fechamento"].sum())
        linhas.append(f"- ... e mais {restante} conta(s) não detalhadas aqui "
                      f"(fechamento M3 somado: {fmt_brl(valor_restante)}).")
    return "\n".join(linhas) + "\n"


def _montar_resumo(df_despesa: pd.DataFrame, df_receita: pd.DataFrame,
                   mes_corte: int, ano: int, conselho: str) -> str:
    despesa_m3 = float(df_despesa["proj_fechamento"].sum())
    receita_m3 = float(df_receita["proj_fechamento"].sum())
    resultado = receita_m3 - despesa_m3
    situacao = "SUPERÁVIT" if resultado >= 0 else "DÉFICIT"
    pct_result = (abs(resultado) / despesa_m3) if despesa_m3 else None

    divergentes = pd.concat([
        _contas_divergentes(df_despesa, "Despesa"),
        _contas_divergentes(df_receita, "Receita"),
    ], ignore_index=True) if not df_despesa.empty or not df_receita.empty else pd.DataFrame()

    baixa_despesa = df_despesa[df_despesa["confianca"] == "baixa"].copy()
    baixa_despesa["ramo"] = "Despesa"
    baixa_receita = df_receita[df_receita["confianca"] == "baixa"].copy()
    baixa_receita["ramo"] = "Receita"
    baixa = pd.concat([baixa_despesa, baixa_receita], ignore_index=True)

    partes = [
        f"# Dados da Projeção de Fechamento {ano} — {conselho}",
        f"Mês de corte (último mês completo considerado): {MESES_PT.get(mes_corte, mes_corte)}/{ano}. "
        f"Contas analisadas: {len(df_despesa)} (despesa, ramo 6.3) e {len(df_receita)} (receita, ramo 6.2).",
        "\n## Despesa (6.3) — totais",
        _linha_totais(df_despesa, mes_corte),
        "\n## Receita (6.2) — totais",
        _linha_totais(df_receita, mes_corte),
        "\n## Resultado orçamentário consolidado",
        f"Receita projetada (M3) {fmt_brl(receita_m3)} - Despesa projetada (M3) {fmt_brl(despesa_m3)} = "
        f"**{situacao} de {fmt_brl(abs(resultado))}**"
        + (f" ({_fmt_pct(pct_result)} da despesa projetada)." if pct_result is not None else "."),
        "\n## Distribuição por natureza — Despesa",
        _tabela_por_natureza(df_despesa),
        "\n## Distribuição por natureza — Receita",
        _tabela_por_natureza(df_receita),
        "\n## Distribuição por confiança — Despesa",
        _tabela_confianca(df_despesa),
        "\n## Distribuição por confiança — Receita",
        _tabela_confianca(df_receita),
        f"\n## Contas com divergência material M3×M2 (> {_fmt_pct(LIMIAR_DIVERGENCIA)}, "
        f"valor > {fmt_brl(LIMIAR_MATERIALIDADE)})",
        _bloco_lista_contas(divergentes, "divergencia"),
        "\n## Contas com confiança BAIXA",
        _bloco_lista_contas(baixa, "confianca"),
    ]
    return "\n".join(partes)


def _montar_mensagens(resumo: str, ano: int, mes_corte: int) -> list:
    system = (
        "Você é um analista orçamentário e financeiro assessorando a diretoria de um "
        "conselho profissional brasileiro (entidade pública, regime orçamentário anual). "
        "Você recebe um resumo numérico já consolidado da projeção de fechamento do "
        f"orçamento de {ano} (despesa e receita) e deve escrever um relatório em "
        "Markdown, em português do Brasil, com EXATAMENTE esta estrutura de seções:\n\n"
        "## Resumo executivo\n"
        "## Análise da projeção\n"
        "## Recomendações\n\n"
        "No Resumo executivo: traga os números centrais (orçamento, realizado, "
        "fechamento projetado de despesa e receita, e o resultado orçamentário "
        "consolidado — superávit ou déficit).\n\n"
        "Na Análise da projeção: explique os principais fatores por trás do resultado "
        "(quais naturezas de despesa/receita mais pesam), comente as divergências "
        "materiais entre o modelo oficial (M3) e a conferência (M2) e as contas de "
        "confiança baixa, e os riscos que elas representam para a confiabilidade da "
        "projeção.\n\n"
        "Nas Recomendações: se o resultado projetado for DÉFICIT, proponha medidas "
        "mitigadoras concretas e fundamentadas nos números do resumo — por exemplo "
        "contingenciamento de despesas discricionárias ou de capital, renegociação de "
        "contratos cujo run-rate projeta acima do orçado, e possíveis medidas de "
        "incremento de receita — cada uma justificada por um número específico do "
        "resumo. Se o resultado for SUPERÁVIT, comente sobre uso responsável do "
        "superávit e riscos de reversão (ex.: contas de confiança baixa que podem "
        "consumir parte dele).\n\n"
        "Regras importantes:\n"
        "- Use SOMENTE os números e contas fornecidos no resumo. Nunca invente contas, "
        "valores ou dados que não estejam explicitamente no resumo.\n"
        "- Formate valores monetários como 'R$ 1.234.567,89' e percentuais com vírgula "
        "decimal, no padrão já usado no resumo.\n"
        "- Seja objetivo; evite floreios genéricos sem base nos números.\n"
        "- Termine SEMPRE o relatório com uma seção final:\n"
        "## Aviso\n"
        "avisando que o conteúdo foi gerado por inteligência artificial e deve ser "
        "revisado e validado por um responsável humano antes de embasar qualquer "
        "decisão orçamentária."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": resumo + "\n\nCom base nos dados acima, gere o relatório."},
    ]


def _extrair_erro_api(resp: requests.Response) -> str:
    try:
        corpo = resp.json()
        msg = corpo.get("error", {}).get("message")
        if msg:
            return msg
    except ValueError:
        pass
    return resp.text[:500] if resp.text else f"HTTP {resp.status_code}"


def _chamar_openrouter(mensagens: list, timeout: int = 60,
                       max_tokens: int = 3000, temperature: float = 0.4) -> str:
    if not config.OPENROUTER_API_KEY:
        raise AgenteIAError(
            "Chave da API do OpenRouter não configurada. Defina a variável de ambiente "
            "OPENROUTER_API_KEY antes de usar a análise de IA.")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "Ferramenta de Projeção de Orçamento 2026 (CFC/DECONT)",
    }
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": mensagens,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(config.OPENROUTER_CHAT_URL, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.Timeout:
        raise AgenteIAError(f"Tempo limite ({timeout}s) excedido ao consultar a API do OpenRouter. "
                            "Tente novamente.")
    except requests.exceptions.ConnectionError:
        raise AgenteIAError("Não foi possível conectar à API do OpenRouter. Verifique sua conexão "
                            "com a internet.")
    except requests.exceptions.RequestException as e:
        raise AgenteIAError(f"Erro ao consultar a API do OpenRouter: {e}")

    if resp.status_code == 401:
        raise AgenteIAError("Chave da API do OpenRouter inválida (HTTP 401). Verifique "
                            "OPENROUTER_API_KEY.")
    if resp.status_code in (402, 429):
        raise AgenteIAError(
            f"Limite ou crédito do modelo '{config.OPENROUTER_MODEL}' excedido (HTTP {resp.status_code}): "
            f"{_extrair_erro_api(resp)}. Tente novamente mais tarde ou troque OPENROUTER_MODEL.")
    if resp.status_code != 200:
        raise AgenteIAError(f"Erro da API do OpenRouter (HTTP {resp.status_code}): {_extrair_erro_api(resp)}")

    try:
        corpo = resp.json()
        texto = corpo["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise AgenteIAError("Resposta inesperada da API do OpenRouter.")

    texto = (texto or "").strip()
    if texto.startswith("```"):
        linhas = texto.splitlines()
        if linhas and linhas[0].startswith("```"):
            linhas = linhas[1:]
        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]
        texto = "\n".join(linhas).strip()

    if not texto:
        raise AgenteIAError("O modelo retornou uma resposta vazia. Tente novamente ou troque de "
                            "modelo (OPENROUTER_MODEL).")
    return texto


def gerar_analise_ia(df_despesa: pd.DataFrame, df_receita: pd.DataFrame,
                     mes_corte: int, ano: int = ANO_ORCAMENTO,
                     conselho: str = CONSELHO_PADRAO, timeout: int = 60) -> str:
    """Gera o relatório de análise de IA da projeção de fechamento (despesa + receita).

    df_despesa/df_receita: retorno de core.projecao_engine.carregar_resultado()
    para os ramos 6.3 e 6.2, respectivamente. Levanta AgenteIAError em qualquer
    falha (dados ausentes, chave ausente, rede, API)."""
    if df_despesa.empty or df_receita.empty:
        raise AgenteIAError("É necessário gerar a projeção de Despesa (6.3) e de Receita (6.2) "
                           "antes de solicitar a análise de IA.")
    resumo = _montar_resumo(df_despesa, df_receita, mes_corte, ano, conselho)
    mensagens = _montar_mensagens(resumo, ano, mes_corte)
    return _chamar_openrouter(mensagens, timeout=timeout)
