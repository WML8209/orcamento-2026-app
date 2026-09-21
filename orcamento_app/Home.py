import io
import traceback
from contextlib import redirect_stdout
from datetime import date

import streamlit as st
from core import db, drive_sync

st.set_page_config(page_title="Ferramenta de Projeção de Orçamento 2026", page_icon="📊", layout="wide")
drive_sync.sincronizar_inicial()
db.init_db()


def _upload_arquivo(label: str, path, tipos: list[str], chave: str, ajuda: str = ""):
    """Mostra o status do arquivo e um uploader para enviar/substituí-lo.
    Necessário porque, ao publicar o app (Streamlit Cloud), o servidor não
    guarda os arquivos entre reinicializações — é preciso reenviá-los."""
    col_status, col_upload = st.columns([2, 1])
    with col_status:
        if path.exists():
            st.success(f"✅ {label}: `{path}`")
        else:
            st.error(f"⚠️ {label} não encontrado em: `{path}`")
        if ajuda:
            st.caption(ajuda)
    with col_upload:
        arquivo = st.file_uploader(label, type=tipos, key=f"uploader_{chave}",
                                    label_visibility="collapsed")

    if arquivo is not None:
        marcador = f"_upload_processado_{chave}"
        assinatura = (arquivo.name, arquivo.size)
        if st.session_state.get(marcador) != assinatura:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(arquivo.getvalue())
            drive_sync.enviar_arquivo(path)
            st.session_state[marcador] = assinatura
            st.success(f"{label} atualizado com sucesso.")
            st.rerun()


def _situacao_dados() -> dict | None:
    """Resumo do que está no dados_reais.db hoje (para a tela mostrar até
    onde os dados vão antes de o usuário decidir atualizar). None se o banco
    ainda não existe."""
    from core import projecao_engine as eng
    from core.config import ANO_ORCAMENTO, DADOS_REAIS_DB
    from core.formatos import MESES_PT

    if not DADOS_REAIS_DB.exists():
        return None
    conn = eng.get_conn_dados()
    try:
        meta = dict(conn.execute("SELECT chave, valor FROM importacao_meta").fetchall())
        if not meta:
            return None
        mes_corte = eng.mes_corte_padrao(conn, ANO_ORCAMENTO)
    finally:
        conn.close()
    data_max = meta.get(f"diario_{ANO_ORCAMENTO}_data_max")
    return dict(
        data_max=date.fromisoformat(data_max).strftime("%d/%m/%Y") if data_max else "—",
        mes_corte=f"{MESES_PT[mes_corte]}/{ANO_ORCAMENTO}",
        importado_em=str(meta.get("ultima_importacao", "—")).replace("T", " "),
        fonte=meta.get("fonte") or ("CSVs da pasta Códigos" if meta.get("codigos_dir") else "—"),
        divergencias=int(meta.get("reconciliacao_divergencias", 0) or 0),
    )


def _atualizar_pela_api(anos: list[int], recalcular: bool) -> dict:
    """Roda a atualização completa em processo: busca na API do CFC, reimporta
    o dados_reais.db, (opcionalmente) recalcula a projeção dos dois ramos e
    reenvia os bancos ao Google Drive. Narra tudo num st.status ao vivo e
    devolve um dict com o desfecho para a tela mostrar depois do rerun."""
    from atualizar_mensal import executar_api
    from core import projecao_engine as eng
    from core.config import DADOS_REAIS_DB, PROJECAO_DB

    linhas: list[str] = []
    with st.status("Atualizando dados pela API do CFC...", expanded=True) as status:
        painel = st.empty()

        def log(txt=""):
            linhas.append(str(txt))
            painel.code("\n".join(linhas))

        codigo = executar_api(anos=anos, log=log, avisar_recalculo=not recalcular)
        desfecho = dict(codigo=codigo, log="\n".join(linhas), recalculado=False)

        if codigo == 1:
            status.update(label="Atualização falhou — nada foi importado", state="error")
            return desfecho

        if recalcular:
            log("\nRecalculando a projeção (despesa e receita)...")
            try:
                for ramo in (eng.RAMO_DESPESA, eng.RAMO_RECEITA):
                    eng.projetar_fechamento(ramo=ramo, persistir=True)
                    log(f"  ✔ {eng.RAMOS_ROTULOS[ramo]} recalculada.")
                desfecho["recalculado"] = True
            except Exception:  # noqa: BLE001 — dados já importados; só a projeção falhou
                log("  ✗ Falha ao recalcular:\n" + traceback.format_exc())
                desfecho["erro_recalculo"] = True

        if drive_sync.esta_configurado():
            log("\nEnviando os bancos atualizados ao Google Drive...")
            drive_sync.enviar_arquivo(DADOS_REAIS_DB)
            if desfecho["recalculado"]:
                drive_sync.enviar_arquivo(PROJECAO_DB)
            log("  ✔ Google Drive atualizado.")

        desfecho["log"] = "\n".join(linhas)
        rotulo = "Dados atualizados" + (" e projeção recalculada" if desfecho["recalculado"] else "")
        status.update(label=rotulo, state="complete" if codigo == 0 else "error",
                      expanded=False)
    return desfecho


def _mostrar_desfecho(desfecho: dict):
    """Mensagem final da última atualização (guardada no session_state para
    sobreviver ao rerun que atualiza o resumo 'Dados atuais')."""
    from core.config import ANO_ORCAMENTO

    codigo = desfecho["codigo"]
    situacao = _situacao_dados() or {}
    with st.expander("Log da última atualização", expanded=codigo != 0):
        st.code(desfecho.get("log") or "(sem saída)")
    if codigo == 0:
        msg = (f"✔ Dados atualizados: Diário {ANO_ORCAMENTO} até "
               f"**{situacao.get('data_max', '—')}** · último mês completo "
               f"**{situacao.get('mes_corte', '—')}** · reconciliação 100% OK.")
        if desfecho.get("recalculado"):
            msg += " Projeção de despesa e receita recalculada — veja em **Fechamento 2026**."
        elif desfecho.get("erro_recalculo"):
            msg += " ⚠ A projeção **não** foi recalculada (ver log) — vá em **Fechamento 2026** e clique em **Recalcular**."
        else:
            msg += " Vá em **Fechamento 2026** e clique em **Recalcular**."
        st.success(msg)
    elif codigo == 2:
        st.warning("⚠ Importou, mas a reconciliação acusou divergência — revise a tabela "
                   "`reconciliacao` no banco antes de usar a projeção.")
    else:
        st.error(f"✗ A atualização falhou (código {codigo}) e nada foi importado. "
                 "Veja o log acima e tente de novo em alguns minutos.")


def _secao_atualizacao():
    from core.config import ANO_ORCAMENTO, CODIGOS_DIR
    from core import fonte_api

    st.subheader("Atualização dos dados reais")
    st.caption("Busca **direto na API de dados abertos do CFC** o Diário, o Orçamento "
               "Atualizado e o Plano de Contas do ano corrente, reimporta para "
               "`dados_reais.db` e roda a reconciliação Diário × Realizado. Leva cerca de "
               "10 segundos e funciona em qualquer ambiente, inclusive no app publicado. "
               "Seus overrides, métodos por conta e o reajuste da folha **não** são "
               "apagados (ficam em `projecao.db`).")

    situacao = _situacao_dados()
    if situacao:
        st.info(f"**Dados atuais:** Diário {ANO_ORCAMENTO} até **{situacao['data_max']}** · "
                f"último mês completo para a projeção: **{situacao['mes_corte']}** · "
                f"importado em {situacao['importado_em']} · fonte: {situacao['fonte']}"
                + (f" · ⚠ {situacao['divergencias']} divergência(s) na reconciliação"
                   if situacao["divergencias"] else ""))
    else:
        st.warning("Ainda não há `dados_reais.db` neste ambiente — a primeira atualização "
                   "precisa trazer **todos os anos** (marque 2022 a 2026 abaixo), porque "
                   "o histórico alimenta o perfil sazonal da projeção.")

    col_opcoes, col_botao = st.columns([3, 1.4])
    with col_opcoes:
        recalcular = st.checkbox(
            "Recalcular a projeção (despesa e receita) logo após atualizar",
            value=True, key="atualizar_api_recalcular",
            help="O mesmo que clicar em Recalcular na tela Fechamento 2026, para os dois ramos.")
        anos = st.multiselect(
            "Anos a buscar na API", options=fonte_api.ANOS_PADRAO,
            default=[ANO_ORCAMENTO] if situacao else fonte_api.ANOS_PADRAO,
            key="atualizar_api_anos",
            help="Na rotina mensal basta o ano corrente: 2022–2025 já estão fechados e "
                 "não mudam. Os anos não marcados ficam intocados no banco.")
    with col_botao:
        st.write("")
        clicou = st.button("🔄 Atualizar dados agora", type="primary",
                           use_container_width=True, disabled=not anos,
                           help="Busca na API do CFC e reimporta os anos marcados.")

    if clicou:
        st.session_state.pop("atualizacao_desfecho", None)
        desfecho = _atualizar_pela_api(sorted(anos), recalcular)
        st.session_state["atualizacao_desfecho"] = desfecho
        st.rerun()

    if "atualizacao_desfecho" in st.session_state:
        _mostrar_desfecho(st.session_state["atualizacao_desfecho"])

    # Caminho antigo (scripts baixar_*.py + CSVs), só onde a pasta Códigos existe.
    if CODIGOS_DIR.exists():
        with st.expander("Caminho antigo — scripts `baixar_*.py` e CSVs da pasta Códigos"):
            st.caption("Baixa os CSVs de **todos os conselhos e anos** pelos scripts da "
                       f"pasta `{CODIGOS_DIR}` e reimporta (o mesmo que "
                       "`python atualizar_mensal.py` sem `--api`). Demora bem mais que a "
                       "API; útil só para refazer a base inteira a partir dos CSVs.")
            pular_download = st.checkbox(
                "Pular download (só reimportar os CSVs já baixados)",
                key="atualizar_mensal_pular_download",
            )
            if st.button("Rodar pelo caminho antigo (CSVs)", use_container_width=True):
                from atualizar_mensal import executar
                from core.config import DADOS_REAIS_DB

                saida = io.StringIO()
                with st.spinner("Atualizando pelos CSVs — pode levar vários minutos..."):
                    with redirect_stdout(saida):
                        codigo = executar(pular_download=pular_download)
                    if codigo == 0 and drive_sync.esta_configurado():
                        drive_sync.enviar_arquivo(DADOS_REAIS_DB)
                st.session_state["atualizacao_desfecho"] = dict(
                    codigo=codigo, log=saida.getvalue(), recalculado=False)
                st.rerun()


def pagina_inicio():
    st.title("📊 Ferramenta de Projeção de Orçamento 2026")
    st.markdown("""
Motor de **projeção de fechamento de despesa e receita 2026** do CFC, alimentado
por dados reais da API de dados abertos do CFC (ver `Orcamento2026.md`).

Use o menu à esquerda para acessar **Fechamento 2026** — a tela de projeção de
despesa/receita, com tabela por natureza e conta, curva mensal de
desembolso/arrecadação, configuração de método por conta e exportação em
Excel/PDF.
""")
    st.divider()
    _secao_atualizacao()

    st.divider()
    st.subheader("Status dos arquivos de dados")
    if drive_sync.esta_configurado():
        st.caption("🔄 Sincronização com o Google Drive **ativa** — os arquivos enviados "
                   "abaixo são salvos na pasta Data do Drive e restaurados automaticamente "
                   "a cada reinicialização do servidor.")
        col_texto, col_botao = st.columns([3, 1])
        with col_texto:
            st.caption("Rodou `importar_dados.py` ou trocou um arquivo direto na pasta "
                       "`data/` local? Use o botão para reenviar o que está no disco agora "
                       "para o Drive, sem precisar reenviar pela caixa de upload.")
        with col_botao:
            if st.button("📤 Atualizar Google Drive agora", use_container_width=True):
                from core.config import (BASES_XLSX, ORCAMENTO_HISTORICO_XLSX,
                                         ORCAMENTO_2026_DB, DADOS_REAIS_DB, PROJECAO_DB)
                arquivos = [BASES_XLSX, ORCAMENTO_HISTORICO_XLSX, ORCAMENTO_2026_DB,
                           DADOS_REAIS_DB, PROJECAO_DB]
                with st.spinner("Enviando arquivos para o Google Drive..."):
                    for arquivo in arquivos:
                        if arquivo.exists():
                            drive_sync.enviar_arquivo(arquivo)
                st.success("Arquivos locais enviados para a pasta Data do Google Drive.")
    else:
        st.caption("Envie aqui os arquivos necessários para o app funcionar — em especial "
                   "depois de publicar na nuvem, onde os arquivos enviados por upload não "
                   "persistem entre reinicializações do servidor (sincronização com o "
                   "Google Drive não configurada — ver `CONFIGURAR_GOOGLE_DRIVE.md`).")
    from core.config import (BASES_XLSX, ORCAMENTO_HISTORICO_XLSX,
                             ORCAMENTO_2026_DB, DADOS_REAIS_DB, PROJECAO_DB)

    _upload_arquivo("Dados reais do CFC (dados_reais.db)", DADOS_REAIS_DB, ["db"],
                    "dados_reais",
                    "Necessário para a tela Fechamento 2026. Normalmente é atualizado "
                    "pelo botão **Atualizar dados agora** acima; o upload serve para "
                    "restaurar um banco gerado em outro ambiente.")
    _upload_arquivo("Configuração da projeção (projecao.db)", PROJECAO_DB, ["db"],
                    "projecao",
                    "Métodos por conta, \"Fechamento Manual\" e a última projeção "
                    "calculada. Só envie para restaurar configuração feita em outro "
                    "ambiente — normalmente é sincronizado sozinho pelo Drive.")
    _upload_arquivo("Bases fixas (bases.xlsx)", BASES_XLSX, ["xlsx"], "bases")
    _upload_arquivo("Orçamento histórico (orcamento_historico.xlsx)",
                    ORCAMENTO_HISTORICO_XLSX, ["xlsx"], "historico")
    _upload_arquivo("Banco de lançamentos 2026 (orcamento2026.db)", ORCAMENTO_2026_DB,
                    ["db"], "orcamento2026",
                    "Criado vazio automaticamente pelo app — só envie para restaurar "
                    "lançamentos já feitos em outro ambiente.")


inicio = st.Page(pagina_inicio, title="Início", icon="🏠", default=True)
fechamento = st.Page("pages/fechamento.py", title="Fechamento 2026", icon="🎯")

# As telas do sistema original de lançamento manual (Projeção Orçamento 2026,
# Resumo, Memória de Cálculo, PCA 2026) foram removidas do menu — não têm
# nenhuma relação de dados com o motor de projeção (core/projecao_engine.py
# só lê data/dados_reais.db; aquelas telas só leem bases.xlsx/
# orcamento_historico.xlsx/orcamento2026.db, com dados de teste). Os arquivos
# em pages/ e core/ continuam no repositório, apenas fora da navegação.

pg = st.navigation([inicio, fechamento])
pg.run()
