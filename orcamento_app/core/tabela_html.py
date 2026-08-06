"""
Gera a tabela dinâmica da Projeção Orçamento como uma tabela HTML de verdade
(com linhas de grade, cabeçalho de ano mesclado via colspan, e
expandir/recolher via clique em JS) — st.columns não dá conta de nenhuma
dessas três coisas.
"""
import html
from core.formatos import fmt_num_br


def _cel(v):
    return fmt_num_br(v) if v else ""


def gerar_html_tabela_simples(colunas: list, linhas: list, alinhar_direita: set = None) -> str:
    """
    Tabela HTML "chapada" (sem hierarquia/colapso), com o mesmo visual da
    tabela dinâmica — usada em Lançamentos de 2026, Resumo e PCA 2026.
    'colunas' é lista de (chave, rótulo). 'linhas' é lista de dicts.
    'alinhar_direita' é o conjunto de chaves de colunas numéricas.
    """
    alinhar_direita = alinhar_direita or set()
    ths = "".join(f'<th>{html.escape(str(rotulo))}</th>' for _, rotulo in colunas)
    trs = []
    for linha in linhas:
        tds = []
        for chave, _ in colunas:
            valor = linha.get(chave, "")
            classe = ' class="num"' if chave in alinhar_direita else ""
            tds.append(f'<td{classe}>{html.escape(str(valor)) if valor is not None else ""}</td>')
        trs.append(f"<tr>{''.join(tds)}</tr>")

    return f"""
<style>
  .tabela-simples-wrap {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; overflow-x: auto; }}
  table.tabela-simples {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  table.tabela-simples th, table.tabela-simples td {{ border: 1px solid #d5dbe3; padding: 6px 10px; }}
  table.tabela-simples thead th {{ background: #1f4e8c; color: white; text-align: left; font-weight: 700; }}
  table.tabela-simples td.num, table.tabela-simples th.num {{ text-align: right; }}
  table.tabela-simples tbody tr:nth-child(even) {{ background: #f7f9fb; }}
</style>
<div class="tabela-simples-wrap">
<table class="tabela-simples">
  <thead><tr>{ths}</tr></thead>
  <tbody>{"".join(trs)}</tbody>
</table>
</div>
"""


def montar_arvore_resumo(completo, coordenadoria: str, ano: int) -> dict:
    """
    Árvore Projeto > SubProjeto > Conta com uma coluna só de Valor —
    equivalente à aba Resumo, no mesmo formato visual/colapsável da Projeção.
    """
    df = completo[(completo["Coordenadoria"] == coordenadoria) & (completo["Ano"] == ano)].copy()
    arvore = {"projetos": [], "total": 0.0}
    if df.empty:
        return arvore
    for proj_cod, df_proj in df.groupby("Projeto"):
        descricao_proj = df_proj["ProjetoLabel"].iloc[0] if "ProjetoLabel" in df_proj.columns and df_proj["ProjetoLabel"].notna().any() else proj_cod
        subprojetos = []
        for sub_cod, df_sub in df_proj.groupby("SubProjeto"):
            nome_sub = df_sub["Nome"].iloc[0] if "Nome" in df_sub.columns and df_sub["Nome"].notna().any() else sub_cod
            contas = (
                df_sub.groupby(["ContaDescricao", "Descrição"], dropna=False)["Valor"].sum().reset_index()
                .rename(columns={"ContaDescricao": "conta", "Descrição": "descricao", "Valor": "valor"})
            )
            subtotal = float(contas["valor"].sum())
            subprojetos.append({
                "subprojeto": sub_cod, "nome": nome_sub,
                "contas": contas.to_dict("records"), "subtotal": subtotal,
            })
        subtotal_proj = sum(s["subtotal"] for s in subprojetos)
        arvore["projetos"].append({
            "projeto": proj_cod, "descricao": descricao_proj,
            "subprojetos": subprojetos, "subtotal": subtotal_proj,
        })
    arvore["total"] = sum(p["subtotal"] for p in arvore["projetos"])
    return arvore


def gerar_html_arvore_resumo(arvore: dict) -> str:
    """Mesmo visual/colapso da tabela dinâmica, mas com 1 coluna de Valor (Projeto/SubProjeto/Descrição/Conta/Valor)."""
    linhas_corpo = []
    for pi, proj in enumerate(arvore["projetos"]):
        proj_id = f"r{pi}"
        desc = html.escape(str(proj["descricao"]))
        linhas_corpo.append(
            f'<tr id="{proj_id}" class="row-projeto" onclick="toggle(\'{proj_id}\')">'
            f'<td colspan="3"><span class="icon" data-toggle-icon="{proj_id}">−</span> {desc}</td>'
            f'<td class="num">{_cel(proj["subtotal"])}</td></tr>'
        )
        for si, sub in enumerate(proj["subprojetos"]):
            sub_id = f"{proj_id}s{si}"
            nome_sub = html.escape(f"{sub['subprojeto']} - {sub['nome']}")
            linhas_corpo.append(
                f'<tr id="{sub_id}" class="row-subprojeto" data-parent="{proj_id}" data-root="{proj_id}" '
                f'onclick="toggle(\'{sub_id}\')">'
                f'<td class="indent1" colspan="3"><span class="icon" data-toggle-icon="{sub_id}">−</span> {nome_sub}</td>'
                f'<td class="num">{_cel(sub["subtotal"])}</td></tr>'
            )
            for conta in sub["contas"]:
                nome_conta = html.escape(str(conta["conta"]))
                descricao_lanc = html.escape(str(conta.get("descricao") or ""))
                linhas_corpo.append(
                    f'<tr class="row-conta" data-parent="{sub_id}" data-root="{proj_id}">'
                    f'<td class="indent2">{html.escape(str(proj["descricao"]))}</td>'
                    f'<td>{html.escape(str(sub["subprojeto"]))} - {html.escape(str(sub["nome"]))}</td>'
                    f'<td>{descricao_lanc} — {nome_conta}</td>'
                    f'<td class="num">{_cel(conta["valor"])}</td></tr>'
                )

    return f"""
<style>
  .pivot-wrap {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; overflow-x: auto; }}
  table.pivot {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  table.pivot th, table.pivot td {{ border: 1px solid #d5dbe3; padding: 6px 10px; }}
  table.pivot thead th {{ background: #1f4e8c; color: white; text-align: left; font-weight: 700; }}
  table.pivot td.num, table.pivot th.num {{ text-align: right; }}
  tr.row-projeto {{ background: #eef2f7; font-weight: 700; cursor: pointer; }}
  tr.row-subprojeto {{ background: #f7f9fb; font-weight: 600; cursor: pointer; }}
  tr.row-conta td {{ font-weight: 400; }}
  td.indent1 {{ padding-left: 28px; }}
  td.indent2 {{ padding-left: 10px; }}
  .icon {{ display: inline-block; width: 14px; font-weight: 700; }}
  tr.row-total {{ background: #dfe6ee; font-weight: 700; }}
</style>
<div class="pivot-wrap">
<table class="pivot">
  <thead><tr><th>Projeto</th><th>SubProjeto</th><th>Descrição / Conta</th><th class="num">Valor</th></tr></thead>
  <tbody>
    {"".join(linhas_corpo)}
    <tr class="row-total"><td colspan="3">TOTAL</td><td class="num">{_cel(arvore["total"])}</td></tr>
  </tbody>
</table>
</div>
<script>
  const estadosResumo = {{}};
  function toggle(id) {{
    estadosResumo[id] = !(estadosResumo[id] === undefined ? true : estadosResumo[id]);
    atualizarResumo();
  }}
  function atualizarResumo() {{
    document.querySelectorAll('tr[data-parent]').forEach(function(tr) {{
      const pai = tr.getAttribute('data-parent');
      const raiz = tr.getAttribute('data-root');
      const paiExpandido = estadosResumo[pai] === undefined ? true : estadosResumo[pai];
      const raizExpandida = raiz ? (estadosResumo[raiz] === undefined ? true : estadosResumo[raiz]) : true;
      tr.style.display = (paiExpandido && raizExpandida) ? '' : 'none';
    }});
    document.querySelectorAll('[data-toggle-icon]').forEach(function(span) {{
      const id = span.getAttribute('data-toggle-icon');
      const expandido = estadosResumo[id] === undefined ? true : estadosResumo[id];
      span.textContent = expandido ? '−' : '+';
    }});
  }}
  atualizarResumo();
</script>
"""


def gerar_html_curva_mensal(linhas: list, mes_corte: int, rotulos_mes: dict) -> str:
    """
    Matriz mensal (linhas = natureza ou conta; colunas = Jan..Dez + Total).
    Meses após `mes_corte` são projetados: cabeçalho marcado com * e células
    sombreadas. 'linhas' = [{rotulo, valores: {1..12: float}, total, eh_total}].
    """
    ths = ['<th class="col-label">Natureza / Conta</th>']
    for m in range(1, 13):
        proj = m > mes_corte
        ths.append(f'<th class="num{" proj" if proj else ""}">{rotulos_mes[m]}{"*" if proj else ""}</th>')
    ths.append('<th class="num">Total</th>')

    trs = []
    for linha in linhas:
        classe_tr = ' class="row-total"' if linha.get("eh_total") else ""
        tds = [f'<td>{html.escape(str(linha["rotulo"]))}</td>']
        for m in range(1, 13):
            proj = m > mes_corte
            tds.append(f'<td class="num{" proj" if proj else ""}">{_cel(linha["valores"].get(m))}</td>')
        tds.append(f'<td class="num">{_cel(linha["total"])}</td>')
        trs.append(f"<tr{classe_tr}>{''.join(tds)}</tr>")

    return f"""
<style>
  .curva-wrap {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; overflow-x: auto; }}
  table.curva {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
  table.curva th, table.curva td {{ border: 1px solid #d5dbe3; padding: 4px 6px; white-space: nowrap; }}
  table.curva thead th {{ background: #1f4e8c; color: white; text-align: right; font-weight: 700; }}
  table.curva thead th.col-label {{ text-align: left; }}
  table.curva thead th.proj {{ background: #3fa0c8; }}
  table.curva td.num {{ text-align: right; }}
  table.curva td.proj {{ background: #eef7fb; }}
  tr.row-total {{ background: #dfe6ee; font-weight: 700; }}
</style>
<div class="curva-wrap">
<table class="curva">
  <thead><tr>{"".join(ths)}</tr></thead>
  <tbody>{"".join(trs)}</tbody>
</table>
</div>
<p style="font-size:11px;color:#6b7787;font-family:-apple-system,'Segoe UI',Arial,sans-serif;">
* meses projetados (após o mês de corte). Meses realizados vêm do Diário contábil.</p>
"""


def gerar_html_fechamento(grupos: list, total: dict) -> str:
    """
    Tabela da Projeção de Fechamento: Natureza (grupo colapsável) > Conta,
    colunas Orçamento | Acumulado | Projeção | Acumulado + Projeção | % Exec |
    Conferência M2 | Diverg. | Confiança. 'grupos' e 'total' já vêm com valores formatados;
    flags 'pct_alerta', 'div_alerta' e 'confianca' controlam o destaque visual.
    """
    linhas_corpo = []
    for gi, g in enumerate(grupos):
        gid = f"n{gi}"
        linhas_corpo.append(
            f'<tr id="{gid}" class="row-projeto" onclick="toggle(\'{gid}\')">'
            f'<td><span class="icon" data-toggle-icon="{gid}">−</span> {html.escape(str(g["rotulo"]))}'
            f' <span class="qtd">({len(g["contas"])})</span></td>'
            f'<td></td>'
            f'<td class="num">{g["orcamento"]}</td><td class="num">{g["ytd"]}</td>'
            f'<td class="num">{g["projecao"]}</td>'
            f'<td class="num">{g["m3"]}</td>'
            f'<td class="num{" pct-alto" if g.get("pct_alerta") else ""}">{g["pct"]}</td>'
            f'<td class="num">{g["m2"]}</td><td></td><td></td></tr>'
        )
        for c in g["contas"]:
            conf = str(c.get("confianca") or "")
            classe_conf = {"alta": "conf-alta", "media": "conf-media", "baixa": "conf-baixa"}.get(conf, "")
            linhas_corpo.append(
                f'<tr class="row-conta" data-parent="{gid}">'
                f'<td class="indent1">{html.escape(str(c["conta"]))} — {html.escape(str(c["descricao"]))}</td>'
                f'<td class="metodo">{html.escape(str(c.get("metodo") or ""))}</td>'
                f'<td class="num">{c["orcamento"]}</td><td class="num">{c["ytd"]}</td>'
                f'<td class="num">{c["projecao"]}</td>'
                f'<td class="num">{c["m3"]}</td>'
                f'<td class="num{" pct-alto" if c.get("pct_alerta") else ""}">{c["pct"]}</td>'
                f'<td class="num">{c["m2"]}</td>'
                f'<td class="num{" div-alerta" if c.get("div_alerta") else ""}">{c["div"]}</td>'
                f'<td class="{classe_conf}">{conf}</td></tr>'
            )

    return f"""
<style>
  .pivot-wrap {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; overflow-x: auto; }}
  table.pivot {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  table.pivot th, table.pivot td {{ border: 1px solid #d5dbe3; padding: 5px 8px; }}
  table.pivot thead th {{ background: #1f4e8c; color: white; text-align: left; font-weight: 700; }}
  table.pivot thead th.num {{ text-align: right; }}
  table.pivot td.num {{ text-align: right; white-space: nowrap; }}
  tr.row-projeto {{ background: #eef2f7; font-weight: 700; cursor: pointer; }}
  tr.row-conta td {{ font-weight: 400; }}
  td.indent1 {{ padding-left: 26px; }}
  td.metodo {{ color: #6b7787; font-size: 11px; }}
  td.pct-alto {{ color: #b00020; font-weight: 700; }}
  td.div-alerta {{ background: #fdf0d5; font-weight: 600; }}
  td.conf-baixa {{ color: #b00020; font-weight: 600; }}
  td.conf-media {{ color: #9a6700; }}
  td.conf-alta {{ color: #1a7f37; }}
  span.qtd {{ font-weight: 400; color: #6b7787; }}
  .icon {{ display: inline-block; width: 14px; font-weight: 700; }}
  tr.row-total {{ background: #dfe6ee; font-weight: 700; }}
</style>
<div class="pivot-wrap">
<table class="pivot">
  <thead><tr>
    <th>Natureza / Conta</th><th>Método</th>
    <th class="num">Orçamento</th><th class="num">Realizado Acumulado</th>
    <th class="num">Projeção</th>
    <th class="num">Acumulado + Projeção</th><th class="num">% Exec</th>
    <th class="num">Conferência M2</th><th class="num">Diverg.</th><th>Conf.</th>
  </tr></thead>
  <tbody>
    {"".join(linhas_corpo)}
    <tr class="row-total"><td>TOTAL</td><td></td>
      <td class="num">{total["orcamento"]}</td><td class="num">{total["ytd"]}</td>
      <td class="num">{total["projecao"]}</td>
      <td class="num">{total["m3"]}</td>
      <td class="num{" pct-alto" if total.get("pct_alerta") else ""}">{total["pct"]}</td>
      <td class="num">{total["m2"]}</td><td></td><td></td></tr>
  </tbody>
</table>
</div>
<script>
  const estadosFech = {{}};
  function toggle(id) {{
    estadosFech[id] = !(estadosFech[id] === undefined ? true : estadosFech[id]);
    atualizarFech();
  }}
  function atualizarFech() {{
    document.querySelectorAll('tr[data-parent]').forEach(function(tr) {{
      const pai = tr.getAttribute('data-parent');
      const paiExpandido = estadosFech[pai] === undefined ? true : estadosFech[pai];
      tr.style.display = paiExpandido ? '' : 'none';
    }});
    document.querySelectorAll('[data-toggle-icon]').forEach(function(span) {{
      const id = span.getAttribute('data-toggle-icon');
      const expandido = estadosFech[id] === undefined ? true : estadosFech[id];
      span.textContent = expandido ? '−' : '+';
    }});
  }}
  atualizarFech();
</script>
"""


def gerar_html_tabela_dinamica(arvore: dict, ano_atual: int) -> str:
    anos = arvore["anos"]
    if not anos:
        return "<p>Sem dados.</p>"

    def n_cols(ano):
        return 1 if ano == ano_atual else 2

    # --- Cabeçalho ---
    linha1 = ['<th rowspan="2" class="col-label">Projeto / SubProjeto / Conta</th>']
    linha2 = []
    for ano in anos:
        classe_ano = " col-atual" if ano == ano_atual else ""
        linha1.append(f'<th colspan="{n_cols(ano)}" class="year-header{classe_ano}">{ano}</th>')
        linha2.append(f'<th class="subheader{classe_ano}">Orçamento Atualizado</th>')
        if n_cols(ano) == 2:
            linha2.append(f'<th class="subheader{classe_ano}">Executado</th>')

    linhas_corpo = []

    def linha_dados(valores_por_ano):
        celulas = []
        for ano in anos:
            classe_ano = " col-atual" if ano == ano_atual else ""
            v = valores_por_ano.get(ano, {"orcamento": 0.0, "execucao": 0.0})
            celulas.append(f'<td class="num{classe_ano}">{_cel(v["orcamento"])}</td>')
            if n_cols(ano) == 2:
                celulas.append(f'<td class="num{classe_ano}">{_cel(v["execucao"])}</td>')
        return "".join(celulas)

    for pi, proj in enumerate(arvore["projetos"]):
        proj_id = f"p{pi}"
        desc = html.escape(str(proj["descricao"]))
        linhas_corpo.append(
            f'<tr id="{proj_id}" class="row-projeto" onclick="toggle(\'{proj_id}\')">'
            f'<td><span class="icon" data-toggle-icon="{proj_id}">−</span> {desc}</td>'
            f'{linha_dados(proj["totais"])}</tr>'
        )
        for si, sub in enumerate(proj["subprojetos"]):
            sub_id = f"{proj_id}s{si}"
            nome_sub = html.escape(f"{sub['subprojeto']} - {sub['nome']}")
            linhas_corpo.append(
                f'<tr id="{sub_id}" class="row-subprojeto" data-parent="{proj_id}" data-root="{proj_id}" '
                f'onclick="toggle(\'{sub_id}\')">'
                f'<td class="indent1"><span class="icon" data-toggle-icon="{sub_id}">−</span> {nome_sub}</td>'
                f'{linha_dados(sub["totais"])}</tr>'
            )
            for conta in sub["contas"]:
                nome_conta = html.escape(str(conta["conta"]))
                linhas_corpo.append(
                    f'<tr class="row-conta" data-parent="{sub_id}" data-root="{proj_id}">'
                    f'<td class="indent2">{nome_conta}</td>'
                    f'{linha_dados(conta["valores"])}</tr>'
                )

    # --- Total geral ---
    linha_total = linha_dados(arvore["totais"])

    n_data_cols = sum(n_cols(a) for a in anos)

    return f"""
<style>
  .pivot-wrap {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; overflow-x: auto; }}
  table.pivot {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  table.pivot th, table.pivot td {{ border: 1px solid #d5dbe3; padding: 6px 10px; }}
  table.pivot thead th.col-label {{ background: #1f4e8c; color: white; text-align: left; vertical-align: bottom; }}
  table.pivot thead th.year-header {{ background: #1f4e8c; color: white; text-align: center; font-weight: 700; }}
  table.pivot thead th.year-header.col-atual {{ background: #b8862b; }}
  table.pivot thead th.subheader {{ background: #eef2f7; color: #1f2d3d; text-align: center; font-weight: 600; font-size: 12px; }}
  table.pivot thead th.subheader.col-atual {{ background: #fbe9cf; }}
  table.pivot td.num, table.pivot th.subheader {{ text-align: right; }}
  table.pivot td.num.col-atual {{ background: #fdf3e3; }}
  tr.row-projeto {{ background: #eef2f7; font-weight: 700; cursor: pointer; }}
  tr.row-projeto td.num.col-atual {{ background: #f6e6c8; }}
  tr.row-subprojeto {{ background: #f7f9fb; font-weight: 600; cursor: pointer; }}
  tr.row-subprojeto td.num.col-atual {{ background: #faedd4; }}
  tr.row-conta td {{ font-weight: 400; }}
  td.indent1 {{ padding-left: 28px; }}
  td.indent2 {{ padding-left: 48px; }}
  .icon {{ display: inline-block; width: 14px; font-weight: 700; }}
  tr.row-total {{ background: #dfe6ee; font-weight: 700; }}
</style>
<div class="pivot-wrap">
<table class="pivot">
  <thead>
    <tr>{"".join(linha1)}</tr>
    <tr>{"".join(linha2)}</tr>
  </thead>
  <tbody>
    {"".join(linhas_corpo)}
    <tr class="row-total"><td>TOTAL</td>{linha_total}</tr>
  </tbody>
</table>
</div>
<script>
  const estados = {{}};
  function toggle(id) {{
    estados[id] = !(estados[id] === undefined ? true : estados[id]);
    atualizar();
  }}
  function atualizar() {{
    document.querySelectorAll('tr[data-parent]').forEach(function(tr) {{
      const pai = tr.getAttribute('data-parent');
      const raiz = tr.getAttribute('data-root');
      const paiExpandido = estados[pai] === undefined ? true : estados[pai];
      const raizExpandida = raiz ? (estados[raiz] === undefined ? true : estados[raiz]) : true;
      tr.style.display = (paiExpandido && raizExpandida) ? '' : 'none';
    }});
    document.querySelectorAll('[data-toggle-icon]').forEach(function(span) {{
      const id = span.getAttribute('data-toggle-icon');
      const expandido = estados[id] === undefined ? true : estados[id];
      span.textContent = expandido ? '−' : '+';
    }});
  }}
  atualizar();
</script>
"""
