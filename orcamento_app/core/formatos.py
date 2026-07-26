"""Formatação de números e datas no padrão brasileiro."""
from datetime import date, datetime


def fmt_num_br(v, casas=2) -> str:
    if v is None:
        return ""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{v:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_brl(v) -> str:
    if v is None:
        return ""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return "R$ " + fmt_num_br(v)


def parse_valor_br(texto: str):
    """Converte '100.023,00' ou '100023,00' ou '100023.00' em float. Retorna None se vazio/ inválido."""
    if texto is None:
        return None
    texto = str(texto).strip()
    if not texto:
        return None
    texto = texto.replace(" ", "")
    if "," in texto:
        # formato BR: ponto = milhar, vírgula = decimal
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def fmt_data_br(v) -> str:
    """Aceita date/datetime/str ISO ('2026-01-01') e devolve 'dd/mm/aaaa'. String vazia se não der para converter."""
    if v is None or v == "":
        return ""
    if isinstance(v, (date, datetime)):
        return v.strftime("%d/%m/%Y")
    texto = str(v).strip()
    for fmt_in in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto[:10], fmt_in).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return texto


MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


def mes_pt(numero) -> str:
    try:
        return MESES_PT.get(int(numero), "")
    except (TypeError, ValueError):
        return str(numero) if numero else ""
