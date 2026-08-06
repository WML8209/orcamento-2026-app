"""
Tela "Projeção de Fechamento 2026" (despesa 6.3) — ver Orcamento2026.md.
Mostra a última projeção persistida (projecao_resultado); recalcula sob demanda
ou automaticamente após salvar parâmetros/configurações de conta.
"""
from pathlib import Path
from datetime import datetime
import traceback

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from core import exportar, projecao_engine as eng, agente_ia, drive_sync
from core.config import ANO_ORCAMENTO, CONSELHO_PADRAO, DADOS_REAIS_DB, PROJECAO_DB
from core.formatos import fmt_num_br, parse_valor_br, MESES_PT
from core.tabela_html import gerar_html_fechamento, gerar_html_curva_mensal

st.title("🎯 Projeção de Fechamento 2026")

if not DADOS_REAIS_DB.exists():
    st.error(f"Banco de dados reais não encontrado em `{DADOS_REAIS_DB}`. "
             "Rode `python importar_dados.py` primeiro (ver Orcamento2026.md).")
    st.stop()

ramo_ui = st.radio("Ramo", ["Despesa (6.3)", "Receita (6.2)"], horizontal=True,
                   label_visibility="collapsed")
ramo = eng.RAMO_DESPESA if "6.3" in ramo_ui else eng.RAMO_RECEITA


def _recalcular():
    with st.spinner("Recalculando projeção..."):
        eng.projetar_fechamento(conselho=CONSELHO_PADRAO, ano=ANO_ORCAMENTO,
                                persistir=True, ramo=ramo)
        drive_sync.enviar_arquivo(PROJECAO_DB)


def _fmt_mes(m):
    if m == 0:
        return "(sem reajuste)"
    return MESES_PT.get(m, str(m))


df = eng.carregar_resultado(ramo=ramo)
if df.empty:
    st.info(f"Nenhuma projeção de {eng.RAMOS_ROTULOS[ramo].lower()} gerada ainda.")
    if st.button("▶️ Gerar projeção agora", type="primary"):
        _recalcular()
        st.rerun()
    st.stop()

gerado_em = str(df["gerado_em"].iloc[0]).replace("T", " ")
mes_corte = int(df["mes_corte"].iloc[0])

c_info, c_btn = st.columns([4, 1.2])
with c_info:
    st.caption(f"Gerada em {gerado_em} — último mês completo considerado: "
               f"**{MESES_PT[mes_corte]}/{ANO_ORCAMENTO}**. Para atualizar os dados, rode os "
               "scripts `baixar_*.py` (pasta Códigos) e depois `python importar_dados.py`.")
with c_btn:
    if st.button("🔄 Recalcular", use_container_width=True):
        _recalcular()
        st.rerun()

# --- Métricas gerais ---
# Fonte reduzida e sem quebra em reticências: com o valor cheio (não mais em
# milhares), o tamanho padrão do st.metric estoura a largura da coluna.
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 1.4rem;
    white-space: normal;
    overflow: visible;
    text-overflow: unset;
}
[data-testid="stMetricLabel"] * {
    white-space: normal;
    overflow: visible;
    text-overflow: unset;
}
</style>
""", unsafe_allow_html=True)

tot_orc = float(df["orcamento"].sum())
tot_ytd = float(df["ytd"].sum())
tot_m3 = float(df["proj_fechamento"].sum())
tot_m2 = float(df["proj_m2"].sum())
m1, m2_, m3_, m4 = st.columns(4)
rotulo_ramo = eng.RAMOS_ROTULOS[ramo]
m1.metric(f"Orçamento 2026 ({rotulo_ramo}) — R$", fmt_num_br(tot_orc))
m2_.metric(f"Realizado até {MESES_PT[mes_corte]} — R$", fmt_num_br(tot_ytd))
m3_.metric("Fechamento projetado (M3) — R$", fmt_num_br(tot_m3),
           delta=f"{tot_m3 / tot_orc:.1%} do orçamento", delta_color="off")
m4.metric("Conferência (M2) — R$", fmt_num_br(tot_m2),
          delta=f"{(tot_m3 - tot_m2) / max(abs(tot_m2), 1):.1%} vs M3", delta_color="off")

# --- Resultado orçamentário projetado (quando os dois ramos já foram gerados) ---
outro_ramo = eng.RAMO_RECEITA if ramo == eng.RAMO_DESPESA else eng.RAMO_DESPESA
df_outro = eng.carregar_resultado(ramo=outro_ramo)
if not df_outro.empty:
    tot_outro = float(df_outro["proj_fechamento"].sum())
    receita_m3 = tot_m3 if ramo == eng.RAMO_RECEITA else tot_outro
    despesa_m3 = tot_m3 if ramo == eng.RAMO_DESPESA else tot_outro
    resultado = receita_m3 - despesa_m3
    situacao = "superávit" if resultado >= 0 else "déficit"
    st.info(f"**Resultado orçamentário projetado 2026**: Receita R\\$ {fmt_num_br(receita_m3)} − "
            f"Despesa R\\$ {fmt_num_br(despesa_m3)} = **{situacao} de R\\$ {fmt_num_br(abs(resultado))}**")

st.divider()

# --- Curva mensal (realizado + projetado) ---
rotulo_fluxo = "desembolso" if ramo == eng.RAMO_DESPESA else "arrecadação"
st.subheader(f"📅 Curva mensal de {rotulo_fluxo}")
df_mensal = eng.carregar_mensal(ramo=ramo)
if df_mensal.empty:
    st.info("Curva mensal ainda não gerada — clique em Recalcular para gerá-la.")
else:
    nats_curva = [n for n in eng.NATUREZAS_ROTULOS if n in set(df_mensal["natureza"])]
    nat_sel = st.selectbox(
        "Natureza (curva)", ["(Todas)"] + nats_curva,
        format_func=lambda n: "(Todas as naturezas)" if n == "(Todas)" else eng.NATUREZAS_ROTULOS.get(n, n),
        label_visibility="collapsed",
    )
    df_curva = df_mensal if nat_sel == "(Todas)" else df_mensal[df_mensal["natureza"] == nat_sel]

    import altair as alt
    agg = df_curva.groupby(["mes", "projetado"], as_index=False)["valor"].sum()
    agg["Tipo"] = agg["projetado"].map({0: "Realizado", 1: "Projetado"})
    agg["mes_nome"] = agg["mes"].map(MESES_PT)
    agg["valor_mi"] = agg["valor"] / 1e6
    agg["valor_fmt"] = agg["valor"].map(lambda v: "R$ " + fmt_num_br(v))
    ordem_meses = [MESES_PT[m] for m in range(1, 13)]
    grafico = (
        alt.Chart(agg)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("mes_nome:N", sort=ordem_meses, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("valor_mi:Q", title="R$ milhões"),
            color=alt.Color("Tipo:N", title=None, sort=["Realizado", "Projetado"],
                            scale=alt.Scale(domain=["Realizado", "Projetado"],
                                            range=["#2d5fa8", "#3fa0c8"])),
            tooltip=[alt.Tooltip("mes_nome:N", title="Mês"),
                     alt.Tooltip("Tipo:N", title="Tipo"),
                     alt.Tooltip("valor_fmt:N", title="Valor")],
        )
        .properties(height=280)
    )
    st.altair_chart(grafico, use_container_width=True)

    # Matriz mensal: por natureza (visão geral) ou por conta (natureza escolhida)
    linhas_matriz = []
    if nat_sel == "(Todas)":
        for nat in nats_curva:
            sub_m = df_mensal[df_mensal["natureza"] == nat]
            valores = sub_m.groupby("mes")["valor"].sum().to_dict()
            linhas_matriz.append({"rotulo": eng.NATUREZAS_ROTULOS.get(nat, nat),
                                  "valores": valores, "total": sub_m["valor"].sum()})
    else:
        for conta_m, sub_m in df_curva.groupby("conta"):
            valores = sub_m.groupby("mes")["valor"].sum().to_dict()
            linhas_matriz.append({"rotulo": f"{conta_m} — {sub_m['descricao'].iloc[0]}",
                                  "valores": valores, "total": sub_m["valor"].sum()})
        linhas_matriz.sort(key=lambda x: -x["total"])
    valores_tot = df_curva.groupby("mes")["valor"].sum().to_dict()
    linhas_matriz.append({"rotulo": "TOTAL", "valores": valores_tot,
                          "total": df_curva["valor"].sum(), "eh_total": True})
    components.html(gerar_html_curva_mensal(linhas_matriz, mes_corte, MESES_PT),
                    height=min(160 + len(linhas_matriz) * 32, 700), scrolling=True)

st.divider()

# --- Filtros ---
c_f1, c_f2 = st.columns(2)
so_divergentes = c_f1.checkbox(f"Só divergências M3×M2 > {eng.LIMIAR_DIVERGENCIA:.0%} (materiais)")
so_baixa = c_f2.checkbox("Só confiança baixa")

df_view = df.copy()
df_view["material"] = df_view[["proj_fechamento", "proj_m2"]].abs().max(axis=1) > eng.LIMIAR_MATERIALIDADE
if so_divergentes:
    df_view = df_view[(df_view["divergencia_pct"] > eng.LIMIAR_DIVERGENCIA) & df_view["material"]]
if so_baixa:
    df_view = df_view[df_view["confianca"] == "baixa"]

# --- Tabela hierárquica Natureza > Conta ---
def _pct(fech, orc):
    return (fech / orc) if orc else None


def _fmt_pct(p):
    return f"{p * 100:,.1f}%".replace(",", "_").replace(".", ",").replace("_", ".") if p is not None else "—"


def _pct_alerta(p, metodo=None):
    """Despesa: alerta quando projeta ACIMA do orçamento. Receita: quando
    projeta ABAIXO (frustração de receita) — exceto contas de equilíbrio."""
    if p is None or metodo == "ytd":
        return False
    return p > 1.0 if ramo == eng.RAMO_DESPESA else p < 1.0


grupos = []
for nat in eng.NATUREZAS_ROTULOS:
    sub = df_view[df_view["natureza"] == nat]
    if sub.empty:
        continue
    sub = sub.sort_values("proj_fechamento", ascending=False)
    g_orc, g_ytd = float(sub["orcamento"].sum()), float(sub["ytd"].sum())
    g_m3, g_m2 = float(sub["proj_fechamento"].sum()), float(sub["proj_m2"].sum())
    g_pct = _pct(g_m3, g_orc)
    so_ytd = (sub["metodo"] == "ytd").all()
    contas = []
    for _, r in sub.iterrows():
        pct = _pct(r["proj_fechamento"], r["orcamento"])
        contas.append({
            "conta": r["conta"], "descricao": r["descricao"],
            "metodo": eng.METODO_ROTULOS.get(r["metodo"], r["metodo"]),
            "orcamento": fmt_num_br(r["orcamento"]), "ytd": fmt_num_br(r["ytd"]),
            "m3": fmt_num_br(r["proj_fechamento"]), "m2": fmt_num_br(r["proj_m2"]),
            "pct": _fmt_pct(pct), "pct_alerta": _pct_alerta(pct, r["metodo"]),
            "div": _fmt_pct(r["divergencia_pct"]),
            "div_alerta": bool(r["divergencia_pct"] > eng.LIMIAR_DIVERGENCIA and r["material"]),
            "confianca": r["confianca"],
        })
    grupos.append({
        "rotulo": eng.NATUREZAS_ROTULOS[nat],
        "orcamento": fmt_num_br(g_orc), "ytd": fmt_num_br(g_ytd),
        "m3": fmt_num_br(g_m3), "m2": fmt_num_br(g_m2),
        "pct": _fmt_pct(g_pct), "pct_alerta": _pct_alerta(g_pct, "ytd" if so_ytd else None),
        "contas": contas,
    })

if not grupos:
    st.info("Nenhuma conta atende aos filtros selecionados.")
else:
    v_orc = float(df_view["orcamento"].sum())
    v_m3 = float(df_view["proj_fechamento"].sum())
    v_pct = _pct(v_m3, v_orc)
    total = {
        "orcamento": fmt_num_br(v_orc), "ytd": fmt_num_br(float(df_view["ytd"].sum())),
        "m3": fmt_num_br(v_m3), "m2": fmt_num_br(float(df_view["proj_m2"].sum())),
        "pct": _fmt_pct(v_pct), "pct_alerta": _pct_alerta(v_pct),
    }
    n_linhas = len(df_view) + len(grupos) + 1
    components.html(gerar_html_fechamento(grupos, total), height=min(140 + n_linhas * 34, 900), scrolling=True)

st.divider()

# --- Exportação ---
df_mensal_exp = df_mensal if not df_mensal.empty else None
c_e1, c_e2, c_e3 = st.columns(3)
with c_e1:
    if st.button("📊 Exportar Excel (Resumo + Detalhe com memória)", use_container_width=True):
        caminho = exportar.gerar_excel_fechamento(df, mes_corte, ANO_ORCAMENTO, ramo=ramo,
                                                  df_mensal=df_mensal_exp)
        with open(caminho, "rb") as f:
            st.download_button("⬇️ Baixar Excel gerado", f, file_name=caminho.name,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        st.success(f"Excel gerado em: {caminho}")
with c_e2:
    if st.button("📄 Exportar PDF (relatório para reunião)", use_container_width=True):
        caminho = exportar.gerar_pdf_fechamento(df, mes_corte, ANO_ORCAMENTO, ramo=ramo,
                                                df_mensal=df_mensal_exp)
        with open(caminho, "rb") as f:
            st.download_button("⬇️ Baixar PDF gerado", f, file_name=caminho.name,
                               mime="application/pdf", use_container_width=True)
        st.success(f"PDF gerado em: {caminho}")
with c_e3:
    # A análise de IA sempre cobre despesa + receita juntas (para falar do
    # resultado orçamentário consolidado), reaproveitando df/df_outro já
    # carregados acima — sem nova consulta ao banco.
    df_despesa_ia = df if ramo == eng.RAMO_DESPESA else df_outro
    df_receita_ia = df if ramo == eng.RAMO_RECEITA else df_outro
    ambos_prontos = not df_despesa_ia.empty and not df_receita_ia.empty
    gerar_ia = st.button("🤖 Gerar Análise com IA", use_container_width=True,
                         disabled=not ambos_prontos)
    if not ambos_prontos:
        faltando = [r for r, d in [("Despesa (6.3)", df_despesa_ia),
                                   ("Receita (6.2)", df_receita_ia)] if d.empty]
        st.caption(f"⚠️ Gere a projeção de {', '.join(faltando)} antes de usar a análise de IA.")

if gerar_ia:
    with st.spinner("Consultando IA — pode levar até 1 minuto..."):
        try:
            texto_ia = agente_ia.gerar_analise_ia(df_despesa_ia, df_receita_ia, mes_corte, ANO_ORCAMENTO)
            caminho_ia = exportar.gerar_md_analise_ia(texto_ia, ANO_ORCAMENTO)
            st.session_state["analise_ia"] = {
                "texto": texto_ia, "caminho": str(caminho_ia), "gerado_em": datetime.now(),
            }
        except agente_ia.AgenteIAError as e:
            st.error(f"Não foi possível gerar a análise de IA: {e}")
        except Exception:
            print(f"[agente_ia] erro inesperado ao gerar análise: {traceback.format_exc()}")
            st.error("Erro inesperado ao gerar a análise de IA. Verifique o log do servidor.")

if "analise_ia" in st.session_state:
    st.divider()
    st.subheader("🤖 Análise de IA — Projeção e Resultado Orçamentário 2026")
    st.warning("Conteúdo gerado por inteligência artificial — **revise e valide antes de "
              "usar em qualquer decisão orçamentária**.")
    st.caption(f"Gerada em {st.session_state['analise_ia']['gerado_em']:%d/%m/%Y %H:%M}. "
              "Se você recalculou a projeção ou alterou configurações depois disso, "
              "gere a análise novamente para refletir os novos números.")
    # Escapa "$" antes de renderizar: st.markdown trata pares de "$" como
    # delimitadores de fórmula LaTeX, o que embaralha o texto sempre que há
    # duas ou mais menções a "R$" na mesma sequência de texto corrido. O
    # arquivo salvo em disco (download) mantém o texto original, sem escape.
    st.markdown(st.session_state["analise_ia"]["texto"].replace("$", r"\$"))
    caminho_ia = Path(st.session_state["analise_ia"]["caminho"])
    if caminho_ia.exists():
        with open(caminho_ia, "rb") as f:
            st.download_button("⬇️ Baixar relatório de IA (.md)", f, file_name=caminho_ia.name,
                               mime="text/markdown", use_container_width=True)
    if st.button("🗑️ Limpar análise de IA da tela"):
        del st.session_state["analise_ia"]
        st.rerun()

st.divider()

# --- Parâmetros globais (Pessoal) — só no ramo despesa ---
if ramo == eng.RAMO_DESPESA:
    with st.expander("⚙️ Parâmetros globais — reajuste de data-base (Pessoal)"):
        params = eng.carregar_parametros()
        c1, c2, c3 = st.columns([1, 1, 1])
        pct_atual = float(params.get("pessoal_reajuste_pct") or 0)
        mes_atual = int(params.get("pessoal_mes_reajuste") or 0)
        novo_pct = c1.number_input("Reajuste (%)", min_value=0.0, max_value=50.0, step=0.5,
                                   value=pct_atual)
        opcoes_mes = list(range(0, 13))
        novo_mes = c2.selectbox("A partir do mês", opcoes_mes,
                                index=opcoes_mes.index(mes_atual) if mes_atual in opcoes_mes else 0,
                                format_func=_fmt_mes)
        with c3:
            st.write("")
            st.write("")
            if st.button("💾 Salvar e recalcular", key="salvar_pessoal"):
                eng.salvar_parametro("pessoal_reajuste_pct", novo_pct if novo_mes else None)
                eng.salvar_parametro("pessoal_mes_reajuste", novo_mes or None)
                _recalcular()
                st.rerun()

# --- Configuração por conta (método / reajuste / fechamento manual) ---
st.subheader("Configurar conta (método, reajuste, fechamento manual)")
configs = eng.carregar_configs()
df_sel = df.sort_values("proj_fechamento", ascending=False)
contas_opts = df_sel["conta"].tolist()
rotulos = {r["conta"]: f"{r['conta']} — {r['descricao']}"
           + (" ⚙️" if r["conta"] in configs else "")
           for _, r in df_sel.iterrows()}
conta_sel = st.selectbox("Conta", contas_opts, format_func=lambda c: rotulos[c])

linha = df[df["conta"] == conta_sel].iloc[0]
cfg_atual = configs.get(conta_sel, {})

ca, cb, cc, cd = st.columns(4)
ca.metric("Orçamento", fmt_num_br(linha["orcamento"]))
cb.metric("Realizado Acumulado", fmt_num_br(linha["ytd"]))
cc.metric("Fechamento M3", fmt_num_br(linha["proj_fechamento"]))
cd.metric("Conferência M2", fmt_num_br(linha["proj_m2"]))
st.caption(f"Natureza: **{eng.NATUREZAS_ROTULOS[linha['natureza']]}** · método atual: "
           f"**{eng.METODO_ROTULOS.get(linha['metodo'], linha['metodo'])}** · "
           f"confiança: **{linha['confianca']}**")
st.text_area("Memória de cálculo", linha["memoria"], height=100, disabled=True,
             key=f"memoria_{conta_sel}")

opcoes_metodo = ["Automático (padrão da natureza)", "Média Móvel", "Sazonal", "Fechamento Manual"]
if "override_fechamento" in cfg_atual:
    idx_metodo = 3
elif cfg_atual.get("metodo") == "runrate":
    idx_metodo = 1
elif cfg_atual.get("metodo") == "sazonal":
    idx_metodo = 2
else:
    idx_metodo = 0
metodo_ui = st.radio("Método", opcoes_metodo, horizontal=True, index=idx_metodo,
                     key=f"metodo_{conta_sel}")

reajuste_pct = mes_reajuste = None
valor_override = justificativa = None
if metodo_ui == "Média Móvel":
    c1, c2 = st.columns(2)
    reajuste_pct = c1.number_input("Reajuste do contrato (%)", min_value=0.0, max_value=100.0,
                                   step=0.5, value=float(cfg_atual.get("reajuste_pct") or 0),
                                   key=f"reaj_{conta_sel}")
    opcoes_mes = list(range(0, 13))
    mes_cfg = int(cfg_atual.get("mes_reajuste") or 0)
    mes_reajuste = c2.selectbox("Reajuste a partir do mês", opcoes_mes,
                                index=opcoes_mes.index(mes_cfg) if mes_cfg in opcoes_mes else 0,
                                format_func=_fmt_mes,
                                key=f"mesreaj_{conta_sel}")
elif metodo_ui == "Fechamento Manual":
    c1, c2 = st.columns([1, 2])
    valor_txt = c1.text_input("Fechamento (R$)", key=f"ovr_{conta_sel}",
                              value=fmt_num_br(cfg_atual["override_fechamento"])
                              if "override_fechamento" in cfg_atual else "",
                              placeholder="0,00")
    valor_override = parse_valor_br(valor_txt)
    justificativa = c2.text_input("Justificativa (obrigatória)", key=f"just_{conta_sel}",
                                  value=cfg_atual.get("justificativa", ""))

c_salvar, c_remover = st.columns(2)
with c_salvar:
    if st.button("💾 Salvar configuração e recalcular", type="primary",
                 key=f"salvar_{conta_sel}", use_container_width=True):
        if metodo_ui == "Automático (padrão da natureza)":
            eng.remover_config_conta(conta_sel)
        elif metodo_ui == "Média Móvel":
            params_cfg = {}
            if mes_reajuste and reajuste_pct:
                params_cfg = {"reajuste_pct": reajuste_pct, "mes_reajuste": mes_reajuste}
            eng.salvar_config_conta(conta_sel, metodo="runrate", parametros=params_cfg)
        elif metodo_ui == "Sazonal":
            eng.salvar_config_conta(conta_sel, metodo="sazonal")
        else:  # Fechamento Manual
            if valor_override is None:
                st.error("Informe o valor do fechamento.")
                st.stop()
            if not (justificativa or "").strip():
                st.error("A justificativa é obrigatória para o fechamento manual.")
                st.stop()
            eng.salvar_config_conta(conta_sel, parametros={
                "override_fechamento": valor_override, "justificativa": justificativa.strip()})
        _recalcular()
        st.success("Configuração salva.")
        st.rerun()
with c_remover:
    if conta_sel in configs and st.button("🗑️ Remover configuração desta conta",
                                          key=f"remover_{conta_sel}", use_container_width=True):
        eng.remover_config_conta(conta_sel)
        _recalcular()
        st.rerun()
