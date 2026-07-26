"""
Importa os dados reais da API de dados abertos do CFC (CSVs em DECONT/Códigos)
para o banco compacto data/dados_reais.db. Ver Orcamento2026.md.

Uso (nesta pasta):
    python importar_dados.py
    python importar_dados.py --conselho CFC
    python importar_dados.py --codigos-dir "C:\\caminho\\para\\Códigos"
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Importar dados reais (CSV -> dados_reais.db)")
    parser.add_argument("--conselho", default=None, help="Sigla do conselho (padrão: CFC)")
    parser.add_argument("--codigos-dir", default=None,
                        help="Pasta com os CSVs baixados (padrão: DECONT/Códigos)")
    args = parser.parse_args()

    if args.codigos_dir:
        os.environ["ORCAMENTO_CODIGOS_DIR"] = args.codigos_dir

    # import depois de ajustar a env var, pois config.py a lê na importação
    from core import dados_reais
    from core.config import CONSELHO_PADRAO

    conselho = args.conselho or CONSELHO_PADRAO
    resultado = dados_reais.importar_tudo(conselho=conselho)

    if resultado["reconciliacao_divergencias"]:
        print(f"\nATENÇÃO: {resultado['reconciliacao_divergencias']} conta(s) com divergência "
              "entre Diário e Realizado oficial — ver tabela 'reconciliacao' no banco.")
        sys.exit(2)
    print("\nReconciliação 100% OK — executado do Diário bate com o Realizado oficial.")


if __name__ == "__main__":
    main()
