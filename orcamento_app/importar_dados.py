"""
Importa os dados reais do CFC para o banco compacto data/dados_reais.db.
Ver Orcamento2026.md.

Duas fontes (core/dados_reais.py):
  - padrão: CSVs baixados pelos scripts baixar_*.py em DECONT/Códigos;
  - --api : busca direto na API de dados abertos do CFC, só o conselho
            projetado e só os anos pedidos (padrão: o ano do orçamento) —
            o mesmo que o botão "Atualizar dados" da tela Início.

Uso (nesta pasta):
    python importar_dados.py
    python importar_dados.py --conselho CFC
    python importar_dados.py --codigos-dir "C:\\caminho\\para\\Códigos"
    python importar_dados.py --api                      # só o ano corrente
    python importar_dados.py --api --anos 2022 2023 2024 2025 2026
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Importar dados reais (CSV -> dados_reais.db)")
    parser.add_argument("--conselho", default=None, help="Sigla do conselho (padrão: CFC)")
    parser.add_argument("--codigos-dir", default=None,
                        help="Pasta com os CSVs baixados (padrão: DECONT/Códigos)")
    parser.add_argument("--api", action="store_true",
                        help="Busca direto na API do CFC em vez de ler os CSVs")
    parser.add_argument("--anos", type=int, nargs="+", default=None,
                        help="Anos a atualizar via --api (padrão: o ano do orçamento)")
    args = parser.parse_args()

    if args.codigos_dir:
        os.environ["ORCAMENTO_CODIGOS_DIR"] = args.codigos_dir

    # import depois de ajustar a env var, pois config.py a lê na importação
    from core import dados_reais
    from core.config import CONSELHO_PADRAO, ANO_ORCAMENTO

    conselho = args.conselho or CONSELHO_PADRAO
    if args.api:
        resultado = dados_reais.importar_da_api(conselho=conselho,
                                                anos=args.anos or [ANO_ORCAMENTO])
    elif args.anos:
        parser.error("--anos só vale com --api (os CSVs sempre trazem todos os anos).")
    else:
        resultado = dados_reais.importar_tudo(conselho=conselho)

    if resultado["reconciliacao_divergencias"]:
        print(f"\nATENÇÃO: {resultado['reconciliacao_divergencias']} conta(s) com divergência "
              "entre Diário e Realizado oficial — ver tabela 'reconciliacao' no banco.")
        sys.exit(2)
    print("\nReconciliação 100% OK — executado do Diário bate com o Realizado oficial.")


if __name__ == "__main__":
    main()
