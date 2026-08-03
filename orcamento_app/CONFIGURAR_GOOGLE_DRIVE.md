# Configurar persistência no Google Drive

Resolve a ressalva registrada em `Analise_Projecao_Orcamento_2026.md` (§2.3):
no Streamlit Cloud o disco do container é efêmero — um upload feito ao vivo
pela tela **Início** (`bases.xlsx`, `orcamento_historico.xlsx`,
`orcamento2026.db`, `dados_reais.db`) some no próximo reinício/redeploy se
ninguém commitar o arquivo no git a tempo.

Com isso configurado, o app passa a guardar esses 4 arquivos numa pasta
**Data** no seu Google Drive (criada automaticamente pelo próprio app na
primeira sincronização): ao iniciar, baixa a versão mais recente de lá; a
cada upload pela tela Início, sobe a versão nova de volta. O Drive vira a
fonte da verdade — não depende mais de commit manual nem de reenviar o
arquivo depois de cada reinício.

Sem essa configuração o app continua funcionando exatamente como hoje (só
disco local / git) — a sincronização é 100% opcional.

## Por que OAuth2 e não Service Account

A primeira tentativa foi com uma *Service Account* (conta "de robô" do
Google Cloud) — mais simples de automatizar, mas **não funciona**: contas
de serviço não têm cota de armazenamento própria em contas Google
*pessoais* (a API retorna `storageQuotaExceeded` ao tentar criar qualquer
arquivo). Isso só funciona em *Shared Drives*, recurso exclusivo do Google
Workspace pago. Por isso a autenticação usada aqui é **OAuth2 com a sua
própria conta** — os arquivos passam a contar na sua cota pessoal do Drive
(15 GB grátis).

O escopo usado é `drive.file`, o mais restrito possível: com ele o app só
enxerga arquivos/pastas que ele mesmo cria — por isso a pasta **Data** é
criada automaticamente pelo app na primeira sincronização, e não uma pasta
escolhida à mão de antemão.

## 1. Criar o projeto e ativar a Google Drive API

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) com
   sua conta Google.
2. Crie um projeto novo (ou reaproveite um existente) — menu superior
   "Selecionar projeto" → "Novo Projeto". Nome sugerido: `orcamento-2026-cfc`.
3. Com o projeto selecionado, vá em **APIs e Serviços > Biblioteca**, procure
   por **Google Drive API** e clique em **Ativar**.

## 2. Configurar a tela de permissão OAuth

1. No menu, vá em **Google Auth Platform** (ou **APIs e Serviços > Tela de
   permissão OAuth**).
2. Preencha: nome do app (ex.: `Orcamento 2026 CFC`), e-mail de suporte
   (o seu), tipo de usuário **Externo**, e-mail de contato (o seu). Aceite a
   política de dados do usuário e crie.
3. Em **Acesso a dados**, clique em **Adicionar ou remover escopos**,
   filtre por `drive.file`, marque **Google Drive API — `.../auth/drive.file`**
   e confirme (**Atualizar**).
4. Em **Público-alvo**, clique em **Publicar app** e confirme "Enviar para
   produção". Isso é importante: enquanto o app estiver em modo "Testando",
   o Google expira o token de acesso automaticamente depois de 7 dias —
   publicado, ele não expira. Como o único escopo usado (`drive.file`) não é
   restrito, não é necessário passar pelo processo de verificação do Google
   para publicar.

## 3. Criar o cliente OAuth

1. Vá em **Clientes** → **Criar cliente**.
2. Tipo de aplicativo: **App para computador**.
3. Nome sugerido: `orcamento-2026-drive-sync`.
4. Clique em **Criar** — anote (ou copie) o **ID do cliente** e a
   **Chave secreta do cliente** exibidos. A chave secreta só aparece uma vez;
   se perder, é preciso gerar outra.

## 4. Gerar o refresh token

Esse é o token de longa duração que o app usa para renovar o acesso ao
Drive sozinho, sem pedir login de novo. Rode localmente:

```
python gerar_refresh_token.py
```

Vai pedir o `client_id` e o `client_secret` do passo 3, depois abre uma URL
de autorização no terminal — copie e cole no navegador (ou o próprio script
tenta abrir sozinho), faça login com a conta Google onde quer guardar os
dados, e confirme o acesso. O terminal imprime as três linhas prontas para
colar no `secrets.toml`.

## 5. Preencher os secrets

Copie `orcamento_app/.streamlit/secrets.toml.example` para
`orcamento_app/.streamlit/secrets.toml` e cole os três valores do passo
anterior (`client_id`, `client_secret`, `refresh_token`) dentro de
`[gdrive]`.

Esse `secrets.toml` **nunca deve ser commitado** (já está no `.gitignore` da
raiz do repositório) — ele contém uma credencial de acesso ao seu Drive.

### Local (seu computador)

Com o arquivo `orcamento_app/.streamlit/secrets.toml` preenchido, rode o app
normalmente (`streamlit run Home.py`) — a tela Início vai mostrar
"🔄 Sincronização com o Google Drive ativa".

### Streamlit Cloud

O arquivo `secrets.toml` não existe no servidor — os mesmos valores vão em:
**app publicado → menu (⋮) → Settings → Secrets**, colando o conteúdo do seu
`secrets.toml` local (mesmo formato TOML) na caixa de texto, e clicando em
**Save** (o app reinicia sozinho).

## 6. Primeira sincronização

Na primeira vez que o app rodar com a configuração ativa (local ou na
nuvem), ele cria a pasta **Data** no seu Drive (raiz do "Meu Drive") e sobe
os arquivos que já existem localmente (os que vieram do git) para
inicializá-la. Das próximas vezes em diante, o Drive manda: o app baixa de
lá a cada início.

## Sobre a falha de segurança relacionada

O `snapshots/2026-07-26/README.md` já registra que a URL pública do app
permite upload **sem autenticação** — qualquer pessoa com o link pode
substituir os dados ao vivo. A sincronização com o Drive **não resolve
isso** — ela só evita que uma substituição indevida (ou um upload legítimo)
seja perdida no próximo reinício; ao contrário, com o Drive como fonte da
verdade, uma substituição indevida passa a persistir de forma ainda mais
duradoura. Se o app expõe dados orçamentários institucionais, vale tratar
a ausência de autenticação na tela Início como item separado (ex.: senha via
`st.secrets`, ou restringir a URL).
