"""
Sincronização da pasta "Data" no Google Drive do usuário, via OAuth2 —
existe porque o disco do container no Streamlit Cloud é efêmero: um upload
feito ao vivo pela tela Início (ver Home.py) some no próximo
reinício/redeploy se não tiver sido commitado no git. Com isso configurado,
o Drive passa a ser a fonte da verdade dos arquivos de dados.

Usa OAuth2 (não Service Account) porque contas de serviço não têm cota de
armazenamento própria em contas Google pessoais — só em Shared Drives do
Google Workspace (pago). O escopo usado é drive.file, o mais restrito
possível: com ele o app só enxerga arquivos que ele mesmo criou, então a
pasta "Data" é criada pelo próprio app na primeira sincronização (não uma
pasta pré-existente escolhida à mão).

Configuração opcional: se st.secrets["gdrive"] não existir, todas as
funções abaixo viram no-op e o app funciona exatamente como antes (só
disco local). Ver CONFIGURAR_GOOGLE_DRIVE.md para o passo a passo de setup
do cliente OAuth e do refresh token.
"""
import io
from pathlib import Path

import streamlit as st

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
NOME_PASTA = "Data"

# Os arquivos que a tela Início permite enviar/substituir — ver core/config.py
# (BASES_XLSX, ORCAMENTO_HISTORICO_XLSX, ORCAMENTO_2026_DB, DADOS_REAIS_DB,
# PROJECAO_DB), todos dentro de DATA_DIR.
ARQUIVOS_SINCRONIZADOS = [
    "bases.xlsx",
    "orcamento_historico.xlsx",
    "orcamento2026.db",
    "dados_reais.db",
    "projecao.db",
]


def esta_configurado() -> bool:
    return "gdrive" in st.secrets


def _obter_pasta_data(service) -> str:
    """Localiza a pasta Data criada pelo app; cria na primeira vez."""
    query = (
        f"name = '{NOME_PASTA}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resp = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    pastas = resp.get("files", [])
    if pastas:
        return pastas[0]["id"]
    metadata = {"name": NOME_PASTA, "mimeType": "application/vnd.google-apps.folder"}
    pasta = service.files().create(body=metadata, fields="id").execute()
    return pasta["id"]


@st.cache_resource(show_spinner=False)
def _service():
    """Cliente do Drive + id da pasta Data, montado uma vez por processo."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    info = st.secrets["gdrive"]
    creds = Credentials(
        token=None,
        refresh_token=info["refresh_token"],
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    servico = build("drive", "v3", credentials=creds, cache_discovery=False)
    folder_id = _obter_pasta_data(servico)
    return servico, folder_id


def _localizar(nome: str, service, folder_id: str):
    query = f"name = '{nome}' and '{folder_id}' in parents and trashed = false"
    resp = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    arquivos = resp.get("files", [])
    return arquivos[0]["id"] if arquivos else None


def enviar_arquivo(path: Path, _conexao=None):
    """Sobe (cria ou atualiza, por nome) um arquivo local para a pasta Data
    do Drive. Sem efeito se a sincronização não estiver configurada; se a
    chamada à API falhar, mostra um aviso não-fatal (o app continua
    funcionando só com o disco local)."""
    if not esta_configurado() or not path.exists():
        return
    try:
        from googleapiclient.http import MediaFileUpload

        service, folder_id = _conexao or _service()
        file_id = _localizar(path.name, service, folder_id)
        media = MediaFileUpload(str(path), resumable=False)
        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            metadata = {"name": path.name, "parents": [folder_id]}
            service.files().create(body=metadata, media_body=media).execute()
    except Exception as exc:
        st.warning(f"Não foi possível sincronizar '{path.name}' com o Google Drive: {exc}")


def _baixar_arquivo(nome: str, path: Path, service, folder_id: str) -> bool:
    from googleapiclient.http import MediaIoBaseDownload

    file_id = _localizar(nome, service, folder_id)
    if not file_id:
        return False
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    concluido = False
    while not concluido:
        _, concluido = downloader.next_chunk()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buffer.getvalue())
    return True


@st.cache_resource(show_spinner="Sincronizando dados com o Google Drive...")
def sincronizar_inicial():
    """Roda uma única vez por processo (um novo container = cache limpo =
    roda de novo). Para cada arquivo esperado: se já existe no Drive, baixa
    por cima da cópia local (Drive manda); se não existe ainda no Drive mas
    existe localmente, sobe a cópia local para inicializar a pasta."""
    if not esta_configurado():
        return
    from core.config import DATA_DIR

    try:
        conexao = _service()
        service, folder_id = conexao
        for nome in ARQUIVOS_SINCRONIZADOS:
            path = DATA_DIR / nome
            baixou = _baixar_arquivo(nome, path, service, folder_id)
            if not baixou and path.exists():
                enviar_arquivo(path, _conexao=conexao)
    except Exception as exc:
        st.warning(f"Não foi possível conectar ao Google Drive na inicialização: {exc}")
