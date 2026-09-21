"""
Busca dos dados reais direto na API de dados abertos do CFC.

Por que existe: até aqui o único caminho para atualizar a base era rodar os
scripts `baixar_*.py` (pasta DECONT/Códigos), que varrem os **27 conselhos** e
**5 anos** e gravam CSVs de ~150 MB por ano — depois lidos em blocos pelo
importador. Para a projeção do CFC isso é trabalho jogado fora: 26/27 dos
dados baixados são descartados logo no primeiro filtro (`Conselho == 'CFC'`).

Este módulo pede à mesma API **só o conselho que a solução projeta** e devolve
DataFrames já no formato das colunas dos CSVs — o importador
(`core/dados_reais.py`) trata as duas fontes pelo mesmo caminho, sem duplicar
a lógica de agregação nem a de reconciliação. Resultado prático: o Diário do
CFC/2026 inteiro sai em ~7 s e ~25 MB, contra dezenas de minutos e ~700 MB da
varredura completa. É o que torna viável um botão "Atualizar Dados" na tela —
inclusive no app publicado, onde a pasta `Códigos` não existe.

Independente do Streamlit: usado pelo importador (CLI) e pelas telas.
"""
from datetime import datetime
import time

import pandas as pd
import requests

URL_BASE = "https://www3.cfc.org.br/spw/API_SPW/dadosAbertos/"

ENDPOINTS = {
    "diario": "DiarioCompleto/",
    "orcamento": "orcamento/",
    "plano_contas": "planoContas/",
}

TIMEOUT_PADRAO = 300      # s — o Diário de um ano cheio é o pedido mais pesado
TENTATIVAS_PADRAO = 3     # a API do CFC falha por rede de vez em quando
ESPERA_ENTRE_TENTATIVAS = 3.0   # s, multiplicado pelo número da tentativa
PAUSA_ENTRE_PEDIDOS = 0.2       # s — mesma gentileza dos scripts baixar_*.py

# Anos que a projeção usa: 2022-2025 alimentam o perfil sazonal
# (projecao_engine.ANOS_HISTORICO) e 2026 é o ano projetado.
ANOS_PADRAO = [2022, 2023, 2024, 2025, 2026]


class ErroAPI(RuntimeError):
    """Falha ao obter dados da API — o chamador deve abortar a importação.

    Existe como exceção própria para o importador nunca gravar meia base: um
    ano que não veio é erro fatal, não "um ano a menos" (ver o cuidado com
    linhas 'Erro em' descrito em Checklist_Atualizacao_Mensal.md)."""


def _pedir(recurso: str, conselho: str, ano: int, log,
           timeout: int = TIMEOUT_PADRAO,
           tentativas: int = TENTATIVAS_PADRAO) -> list[dict]:
    """GET num recurso da API para (conselho, ano), com novas tentativas.

    A API recebe conselho/ano por **cabeçalho**, não por query string — é
    assim que os scripts `baixar_*.py` a consultam."""
    url = URL_BASE + ENDPOINTS[recurso]
    cabecalhos = {"conselho": conselho, "ano": str(ano)}
    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(url, headers=cabecalhos, timeout=timeout)
            resposta.raise_for_status()
            dados = resposta.json()
            return dados or []
        except (requests.exceptions.RequestException, ValueError) as e:
            # ValueError cobre o JSON inválido que a API devolve quando
            # responde 200 com uma página de erro do servidor.
            ultimo_erro = e
            if tentativa < tentativas:
                espera = ESPERA_ENTRE_TENTATIVAS * tentativa
                log(f"    ! {recurso} {conselho}/{ano}: {e} — nova tentativa "
                    f"em {espera:.0f}s ({tentativa}/{tentativas - 1})")
                time.sleep(espera)

    raise ErroAPI(f"{recurso} {conselho}/{ano}: falhou em {tentativas} tentativas "
                  f"({ultimo_erro}).")


def _para_numero(serie: pd.Series) -> pd.Series:
    """'1.234,56' (pt-BR, como a API devolve) -> 1234.56.

    Mesma normalização dos scripts `baixar_*.py`, para os números baterem
    dígito a dígito com o que os CSVs produziriam."""
    return pd.to_numeric(
        serie.astype(str).str.strip()
             .str.replace("R$", "", regex=False)
             .str.replace(" ", "", regex=False)
             .str.replace(".", "", regex=False)
             .str.replace(",", ".", regex=False),
        errors="coerce",
    )


def baixar_diario(conselho: str, ano: int, log=print) -> pd.DataFrame:
    """Diário completo de um ano, nas colunas que o importador lê do CSV."""
    inicio = time.time()
    registros = _pedir("diario", conselho, ano, log)
    if not registros:
        log(f"  Diário {conselho}/{ano}: sem dados.")
        return pd.DataFrame(columns=["Conselho", "Conta", "D/C",
                                     "Data Lançamento", "Soma de Valor"])

    df = pd.DataFrame(registros)
    df = df.rename(columns={
        "dataLancamento": "Data Lançamento",
        "dc": "D/C",
        "identificacaoContaContabil": "Conta",
        "valorLancamento": "Soma de Valor",
    })
    df["Conselho"] = conselho
    df["Conta"] = df["Conta"].astype(str).str.strip()
    df["Soma de Valor"] = _para_numero(df["Soma de Valor"])
    # A API entrega a data como texto dd/mm/aaaa; o formato explícito evita a
    # inferência do pandas trocar dia por mês em datas ambíguas (05/03/2026).
    df["Data Lançamento"] = pd.to_datetime(df["Data Lançamento"],
                                           format="%d/%m/%Y", errors="coerce")

    df = df[["Conselho", "Conta", "D/C", "Data Lançamento", "Soma de Valor"]]
    dmax = df["Data Lançamento"].max()
    log(f"  Diário {conselho}/{ano}: {len(df):,} lançamentos"
        + (f", até {dmax:%d/%m/%Y}" if pd.notna(dmax) else "")
        + f" ({time.time() - inicio:.0f}s)")
    time.sleep(PAUSA_ENTRE_PEDIDOS)
    return df


def baixar_orcamento(conselho: str, anos: list[int], log=print) -> pd.DataFrame:
    """Orçamento (orçado x realizado oficial) dos anos pedidos."""
    partes = []
    for ano in anos:
        registros = _pedir("orcamento", conselho, ano, log)
        if not registros:
            log(f"  Orçamento {conselho}/{ano}: sem dados.")
            continue
        df = pd.DataFrame(registros)
        df["Conselho"] = conselho
        partes.append(df)
        log(f"  Orçamento {conselho}/{ano}: {len(df)} contas")
        time.sleep(PAUSA_ENTRE_PEDIDOS)

    if not partes:
        raise ErroAPI(f"Orçamento: a API não devolveu nada para {conselho} "
                      f"nos anos {anos}.")

    df = pd.concat(partes, ignore_index=True)
    df = df.rename(columns={
        "ano": "Ano",
        "codigoConta": "Conta",
        "descricaoConta": "Descrição",
        "valorOrcado": "Orçamento Inicial",
        "valorRealizado": "Realizado",
    })
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype("Int64")
    df["Conta"] = df["Conta"].astype(str).str.strip()
    df["Orçamento Inicial"] = _para_numero(df["Orçamento Inicial"])
    df["Realizado"] = _para_numero(df["Realizado"])
    return df[["Ano", "Conselho", "Conta", "Descrição",
               "Orçamento Inicial", "Realizado"]]


def baixar_plano_contas(conselho: str, anos: list[int], log=print) -> pd.DataFrame:
    """Plano de contas dos anos pedidos (para descrições e hierarquia).

    A API não devolve a hierarquia de grupos (só ano, conta, descrição e
    conta superior) — as colunas grupo2/3/4 ficam ausentes de propósito e o
    importador já as trata como opcionais."""
    partes = []
    for ano in anos:
        registros = _pedir("plano_contas", conselho, ano, log)
        if not registros:
            log(f"  Plano de contas {conselho}/{ano}: sem dados.")
            continue
        df = pd.DataFrame(registros)
        df["Conselho"] = conselho
        partes.append(df)
        log(f"  Plano de contas {conselho}/{ano}: {len(df)} contas")
        time.sleep(PAUSA_ENTRE_PEDIDOS)

    if not partes:
        raise ErroAPI(f"Plano de contas: a API não devolveu nada para "
                      f"{conselho} nos anos {anos}.")

    df = pd.concat(partes, ignore_index=True)
    df = df.rename(columns={"ano": "Ano", "numeroConta": "Conta",
                            "nomeConta": "Descrição"})
    df["Conta"] = df["Conta"].astype(str).str.strip()
    return df[["Ano", "Conselho", "Conta", "Descrição"]]


def testar_conexao(conselho: str, ano: int | None = None,
                   timeout: int = 30) -> tuple[bool, str]:
    """Checagem barata de que a API responde, para a tela decidir se oferece
    o botão de atualização. Usa o orçamento (poucos KB), nunca o Diário."""
    ano = ano or datetime.now().year
    try:
        resposta = requests.get(URL_BASE + ENDPOINTS["orcamento"],
                                headers={"conselho": conselho, "ano": str(ano)},
                                timeout=timeout)
        resposta.raise_for_status()
        dados = resposta.json()
        if not dados:
            return False, f"A API respondeu, mas sem dados para {conselho}/{ano}."
        return True, f"API respondendo — {len(dados)} contas em {conselho}/{ano}."
    except Exception as e:  # rede, HTTP, JSON inválido: tudo vira "indisponível"
        return False, f"API indisponível: {e}"
