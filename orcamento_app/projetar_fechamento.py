"""
Roda a Projeção de Fechamento (despesa 6.3) e imprime o relatório resumido.
Grava o detalhamento por conta na tabela projecao_resultado do dados_reais.db.

Uso (nesta pasta):
    python projetar_fechamento.py
    python projetar_fechamento.py --mes-corte 5
    python projetar_fechamento.py --detalhe          (lista todas as contas)
"""
import argparse
import sys


def _fmt(v):
    return f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def main():
    parser = argparse.ArgumentParser(description="Projeção de Fechamento 2026 (despesa/receita)")
    parser.add_argument("--conselho", default=None)
    parser.add_argument("--ano", type=int, default=None)
    parser.add_argument("--ramo", choices=["6.3", "6.2"], default="6.3",
                        help="6.3 = despesa (padrão), 6.2 = receita")
    parser.add_argument("--mes-corte", type=int, default=None,
                        help="Último mês completo a considerar (padrão: automático)")
    parser.add_argument("--detalhe", action="store_true", help="Lista todas as contas")
    args = parser.parse_args()

    from core import projecao_engine as eng
    from core.config import CONSELHO_PADRAO, ANO_ORCAMENTO

    conselho = args.conselho or CONSELHO_PADRAO
    ano = args.ano or ANO_ORCAMENTO

    conn = eng.get_conn()
    mes_corte = args.mes_corte or eng.mes_corte_padrao(conn, ano)
    data_max = eng._meta(conn, f"diario_{ano}_data_max", "?")
    conn.close()

    print(f"Projeção de Fechamento {ano} — {conselho} — {eng.RAMOS_ROTULOS[args.ramo]} ({args.ramo})")
    print(f"Diário disponível até {data_max}; último mês completo considerado: {mes_corte}\n")

    resultados = eng.projetar_fechamento(conselho=conselho, ano=ano, mes_corte=mes_corte,
                                         ramo=args.ramo)

    # --- Resumo por natureza ---
    agg = eng.resumo_por_natureza(resultados)
    larg = max(len(i) for i in agg.index) + 2
    print(f"{'Natureza':<{larg}}{'Orçamento':>18}{'Acumulado':>18}{'Fechamento M3':>18}{'Conferência M2':>18}{'% Exec':>9}")
    for nat, r in agg.iterrows():
        v = r["exec_projetada_pct"]
        pct = f"{v:.1%}" if v == v else "-"  # NaN se orçamento zero
        print(f"{nat:<{larg}}{_fmt(r['orcamento']):>18}{_fmt(r['ytd']):>18}"
              f"{_fmt(r['fechamento']):>18}{_fmt(r['m2']):>18}{pct:>9}")
    tot_orc = sum(r.orcamento for r in resultados)
    tot_ytd = sum(r.ytd for r in resultados)
    tot_m3 = sum(r.proj_fechamento for r in resultados)
    tot_m2 = sum(r.proj_m2 for r in resultados)
    print("-" * (larg + 81))
    print(f"{'TOTAL':<{larg}}{_fmt(tot_orc):>18}{_fmt(tot_ytd):>18}{_fmt(tot_m3):>18}"
          f"{_fmt(tot_m2):>18}{tot_m3 / tot_orc:>9.1%}")

    # --- Alertas ---
    divergentes = sorted([r for r in resultados
                          if r.divergencia_pct > eng.LIMIAR_DIVERGENCIA
                          and max(abs(r.proj_fechamento), abs(r.proj_m2)) > 50_000],
                         key=lambda r: -r.divergencia_pct)
    baixa_conf = [r for r in resultados if r.confianca == "baixa" and r.orcamento > 0]

    if divergentes:
        print(f"\nDivergências M3 x M2 acima de {eng.LIMIAR_DIVERGENCIA:.0%} (materiais):")
        for r in divergentes[:15]:
            print(f"  {r.conta}  {r.descricao[:45]:<45} M3 {_fmt(r.proj_fechamento):>15}"
                  f"  M2 {_fmt(r.proj_m2):>15}  ({r.divergencia_pct:.0%}, "
                  f"{eng.METODO_ROTULOS.get(r.metodo, r.metodo)})")
    if baixa_conf:
        print(f"\nContas com confiança BAIXA ({len(baixa_conf)}) — revisar/definir Fechamento Manual:")
        for r in baixa_conf[:15]:
            print(f"  {r.conta}  {r.descricao[:45]:<45} M3 {_fmt(r.proj_fechamento):>15}")

    if args.detalhe:
        print("\nDetalhe por conta:")
        for r in sorted(resultados, key=lambda x: -x.proj_fechamento):
            print(f"\n{r.conta} {r.descricao} [{r.natureza}/"
                  f"{eng.METODO_ROTULOS.get(r.metodo, r.metodo)}/conf.{r.confianca}]")
            print(f"  Orçamento {_fmt(r.orcamento)} | Acumulado {_fmt(r.ytd)} | "
                  f"M3 {_fmt(r.proj_fechamento)} | M2 {_fmt(r.proj_m2)}")
            print(f"  {r.memoria}")

    print(f"\nDetalhamento completo gravado em projecao_resultado ({len(resultados)} contas).")


if __name__ == "__main__":
    main()
