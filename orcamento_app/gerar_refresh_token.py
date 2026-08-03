"""
CLI: gera o refresh_token do Google Drive usado por core/drive_sync.py.

Rode uma única vez (ou de novo, se precisar trocar de conta Google ou
revogar o acesso). Abre uma URL de autorização, você faz login/consentimento
na conta Google, e o token final aparece no terminal para colar em
.streamlit/secrets.toml — ver CONFIGURAR_GOOGLE_DRIVE.md para o passo a
passo completo (inclusive como obter client_id/client_secret antes disso).
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    client_id = input("Client ID (.apps.googleusercontent.com): ").strip()
    client_secret = input("Client secret (GOCSPX-...): ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8765, prompt="consent")

    print("\nAdicione isto ao seu .streamlit/secrets.toml, dentro de [gdrive]:\n")
    print(f'client_id = "{client_id}"')
    print(f'client_secret = "{client_secret}"')
    print(f'refresh_token = "{creds.refresh_token}"')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
