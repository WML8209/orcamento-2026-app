import io
from contextlib import redirect_stdout

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
    st.subheader("Atualização mensal dos dados reais")
    from core.config import CODIGOS_DIR

    if not CODIGOS_DIR.exists():
        st.caption("Baixa os CSVs mais recentes da API do CFC, reimporta para "
                   "`dados_reais.db` e roda a reconciliação Diário × Realizado (ver "
                   "`Checklist_Atualizacao_Mensal.md`).")
        st.info(f"🔒 Indisponível neste ambiente — depende da pasta `Códigos` do seu "
                f"computador (`{CODIGOS_DIR}`), que não existe aqui. Rode "
                f"`python atualizar_mensal.py` localmente e, se a sincronização com o "
                f"Google Drive estiver configurada, o app publicado passa a puxar os "
                f"dados novos sozinho.")
    else:
        st.caption("Baixa os CSVs mais recentes da API do CFC, reimporta para "
                   "`dados_reais.db` e roda a reconciliação Diário × Realizado — o mesmo "
                   "que `python atualizar_mensal.py` (ver `Checklist_Atualizacao_Mensal.md`"
                   "). Seus overrides e métodos por conta não são apagados.")
        pular_download = st.checkbox(
            "Pular download (só reimportar os CSVs já baixados)",
            key="atualizar_mensal_pular_download",
        )
        if st.button("🔄 Rodar atualização mensal agora", use_container_width=True):
            from atualizar_mensal import executar
            from core.config import DADOS_REAIS_DB

            saida = io.StringIO()
            with st.spinner("Atualizando dados mensais — pode levar alguns minutos..."):
                with redirect_stdout(saida):
                    codigo = executar(pular_download=pular_download)
                if codigo == 0 and drive_sync.esta_configurado():
                    drive_sync.enviar_arquivo(DADOS_REAIS_DB)

            with st.expander("Log da atualização", expanded=codigo != 0):
                st.code(saida.getvalue() or "(sem saída)")

            if codigo == 0:
                st.success("✔ Dados atualizados e reconciliação 100% OK. Vá em "
                            "**Fechamento 2026** e clique em **Recalcular**.")
            elif codigo == 2:
                st.warning("⚠ Importou, mas a reconciliação acusou divergência — revise "
                           "a tabela `reconciliacao` no banco antes de usar a projeção.")
            else:
                st.error(f"✗ Falhou (código {codigo}). Veja o log acima.")

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
                                         ORCAMENTO_2026_DB, DADOS_REAIS_DB)
                arquivos = [BASES_XLSX, ORCAMENTO_HISTORICO_XLSX, ORCAMENTO_2026_DB, DADOS_REAIS_DB]
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
                             ORCAMENTO_2026_DB, DADOS_REAIS_DB)

    _upload_arquivo("Dados reais do CFC (dados_reais.db)", DADOS_REAIS_DB, ["db"],
                    "dados_reais",
                    "Necessário para a tela Fechamento 2026. Gerado localmente por "
                    "`python importar_dados.py` (ver Orcamento2026.md).")
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
