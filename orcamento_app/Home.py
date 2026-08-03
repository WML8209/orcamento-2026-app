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
    st.subheader("Status dos arquivos de dados")
    if drive_sync.esta_configurado():
        st.caption("🔄 Sincronização com o Google Drive **ativa** — os arquivos enviados "
                   "abaixo são salvos na pasta Data do Drive e restaurados automaticamente "
                   "a cada reinicialização do servidor.")
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
