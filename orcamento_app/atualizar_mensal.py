"""
Atualização mensal dos dados reais do CFC — um comando só.

Faz, em sequência e com trava de segurança:
  1. Baixa os CSVs da API (scripts baixar_*.py, cada um na sua subpasta).
  2. Confere o log de cada download por linhas "Erro em" (falha silenciosa de
     rede que NÃO interrompe o script, mas pode deixar um ano sem dados) e
     PARA na hora se encontrar — para nunca importar dado pela metade.
  3. Se todos os downloads vierem limpos, roda importar_dados.py, que regera
     data/dados_reais.db e faz a reconciliação Diário × Realizado oficial.
  4. Imprime um resumo final e devolve um código de saída claro:
        0 = tudo OK
        1 = falha em algum download (nada foi importado)
        2 = importou, mas a reconciliação acusou divergência (revisar!)

Uso (na pasta orcamento_app, a mesma do importar_dados.py):
    python atualizar_mensal.py
    python atualizar_mensal.py --pular-download          # só reimporta os CSVs já baixados
    python atualizar_mensal.py --codigos-dir "C:\\...\\Códigos"

Seus overrides, métodos por conta e o reajuste da folha NÃO são apagados por
este processo — o importador só substitui as tabelas de dados-base. Depois de
rodar, é só recalcular a projeção na tela Fechamento 2026.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# No Windows, o console usa o codepage local (ex.: cp1252) por padrão. Se
# algum log capturado tiver caracteres fora dele (inclusive os U+FFFD que
# aparecem quando um processo filho não escreveu em UTF-8), o print() comum
# derruba o script com UnicodeEncodeError bem no meio da atualização.
# Reconfigurar para UTF-8 com "replace" garante que ISSO NUNCA interrompa a
# atualização mensal — na pior hipótese, um caractere estranho vira "?".
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# --- O que baixar. Edite esta lista se precisar. Cada item é (subpasta, script) ---
# Rotina mensal: só o Diário costuma mudar todo mês; o Orçamento Atualizado
# muda quando há crédito adicional. Plano de Contas e Saldo Inicial mudam
# pouco — deixe comentados e rode sob demanda (confirme o nome exato da
# subpasta/script antes de habilitar).
DOWNLOADS = [
    ("Diário", "baixar_diario.py"),
    ("OrçamentoAtualizado", "baixar_orçamentoatualizado.py"),
    # ("PlanoContas", "baixar_plano_contas.py"),
    # ("SaldoInicial", "baixar_saldoinicial.py"),
]

# Padrões que indicam falha mesmo com o script "terminando normal".
PADROES_ERRO = [re.compile(r"erro\s+em", re.IGNORECASE)]


def cabecalho(txt):
    print("\n" + "=" * 70)
    print(txt)
    print("=" * 70)


def rodar(cmd, cwd):
    """Roda um comando capturando saída (decodifica de forma tolerante) e
    devolve (returncode, texto_da_saida)."""
    # Força o processo filho a escrever em UTF-8 mesmo no console do Windows
    # (que por padrão usa o codepage local, ex.: cp1252) — sem isso, qualquer
    # acento que o filho imprima vira lixo ao ser decodificado como UTF-8 aqui.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, env=env)
    texto = proc.stdout.decode("utf-8", errors="replace")
    print(texto, end="" if texto.endswith("\n") else "\n")
    return proc.returncode, texto


def tem_erro_no_log(texto):
    return any(p.search(texto) for p in PADROES_ERRO)


def executar(pular_download: bool = False, codigos_dir: str | None = None) -> int:
    """Roda a atualização mensal (downloads + importação + reconciliação) e
    devolve o código de saída (0/1/2 — ver docstring do módulo), sem chamar
    sys.exit. Toda a narração do processo sai por print(), para quem chamar
    poder capturá-la (ex.: redirect_stdout) ou deixá-la ir direto pro
    terminal. Reaproveitada tanto pelo CLI (main, abaixo) quanto pelo botão
    "Rodar atualização mensal agora" da tela Início (Home.py)."""
    if codigos_dir:
        os.environ["ORCAMENTO_CODIGOS_DIR"] = codigos_dir

    # Importa a config DEPOIS de ajustar a env var, para pegar o mesmo
    # CODIGOS_DIR que o importar_dados.py vai usar.
    aqui = Path(__file__).resolve().parent
    if str(aqui) not in sys.path:
        sys.path.insert(0, str(aqui))
    from core.config import CODIGOS_DIR  # noqa: E402

    py = sys.executable  # usa o mesmo Python que está rodando este script

    if not CODIGOS_DIR.exists():
        cabecalho("PAROU: pasta de códigos não encontrada neste ambiente.")
        print(f"  {CODIGOS_DIR} não existe aqui.")
        print("  Downloads e importação dependem da pasta 'Códigos' do seu computador "
              "(ver Orcamento2026.md) — por isso essa rotina só funciona rodando local, "
              "não no app publicado na nuvem.")
        return 1

    # ---------- 1 e 2: downloads + conferência do log ----------
    if pular_download:
        print("Pulando os downloads (--pular-download): usando os CSVs já baixados.")
    else:
        cabecalho(f"1) BAIXANDO OS CSVs — origem: {CODIGOS_DIR}")
        for subpasta, script in DOWNLOADS:
            pasta = CODIGOS_DIR / subpasta
            caminho_script = CODIGOS_DIR / script
            print(f"\n--- {subpasta}: python {script} (em {pasta}) ---")
            if not pasta.exists():
                print(f"  ✗ Subpasta não encontrada: {pasta}")
                print("    Confira o nome da subpasta em DOWNLOADS ou o --codigos-dir.")
                return 1
            if not caminho_script.exists():
                print(f"  ✗ Script não encontrado: {caminho_script}")
                return 1
            # equivale a: cd <subpasta> && python ../<script>
            rc, log = rodar([py, str(caminho_script)], cwd=pasta)
            if rc != 0 or tem_erro_no_log(log):
                motivo = "código de saída != 0" if rc != 0 else "linha 'Erro em' no log"
                cabecalho("PAROU: falha no download — NADA foi importado.")
                print(f"  Origem: {subpasta}  ·  Motivo: {motivo}")
                print("  Rode o download de novo (pode ter sido falha isolada de rede)")
                print("  e só então repita este comando.")
                return 1
            print(f"  ✔ {subpasta}: download sem erros.")

    # ---------- 3: importar (regera dados_reais.db + reconciliação) ----------
    cabecalho("2) IMPORTANDO PARA data/dados_reais.db (com reconciliação)")
    rc_imp, _ = rodar([py, str(aqui / "importar_dados.py")], cwd=aqui)

    # importar_dados.py sai com 2 quando há divergência na reconciliação.
    cabecalho("RESUMO")
    if rc_imp == 2:
        print("  ⚠ Importou, MAS a reconciliação acusou divergência.")
        print("    Revise a tabela 'reconciliacao' no banco antes de usar a projeção.")
        return 2
    if rc_imp != 0:
        print(f"  ✗ Importação falhou (código {rc_imp}). Veja o log acima.")
        return rc_imp
    print("  ✔ Dados atualizados e reconciliação 100% OK.")
    print("  → Próximo passo: abra a tela Fechamento 2026 e RECALCULE a projeção")
    print("    (seus overrides e métodos por conta continuam valendo).")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Atualização mensal dos dados reais do CFC")
    ap.add_argument("--pular-download", action="store_true",
                    help="Não baixa nada; só reimporta os CSVs já presentes.")
    ap.add_argument("--codigos-dir", default=None,
                    help="Pasta com os CSVs (padrão: a mesma que o importador usa).")
    args = ap.parse_args()
    sys.exit(executar(pular_download=args.pular_download, codigos_dir=args.codigos_dir))


if __name__ == "__main__":
    main()
