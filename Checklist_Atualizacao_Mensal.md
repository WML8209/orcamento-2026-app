# Checklist — Atualização Mensal dos Dados (Projeção Orçamento 2026)

> Rotina para incluir novos meses de execução no `dados_reais.db` sem erro.
> Faça sempre nesta ordem. Tempo típico: alguns minutos.

## Caminho rápido (um comando)

Na pasta `orcamento_app` (a mesma do `importar_dados.py`):

```
python atualizar_mensal.py
```

O script baixa os CSVs, **confere o log e para sozinho se achar "Erro em"**,
importa para o banco e roda a reconciliação. Ao final, o código de saída diz o
que aconteceu:

- **0** → tudo OK, pode recalcular a projeção.
- **1** → falhou um download; **nada foi importado** (rode de novo e repita).
- **2** → importou, mas a reconciliação acusou divergência — **revisar antes de usar**.

Depois: abra **Fechamento 2026** e clique em **recalcular**. Seus overrides,
métodos por conta e o reajuste da folha **continuam valendo** — o importador não
os apaga.

---

## Passo a passo manual (se preferir conferir cada etapa)

- [ ] **1. Baixar os CSVs** — rode cada script *de dentro* da sua subpasta,
      para o CSV cair no lugar certo:
      ```
      cd DECONT/Códigos/Diário              && python ../baixar_diario.py
      cd DECONT/Códigos/OrçamentoAtualizado && python ../baixar_orçamentoatualizado.py
      ```
      (Plano de Contas e Saldo Inicial mudam pouco — só quando necessário.)

- [ ] **2. Conferir o log** de cada download por linhas **"Erro em"**.
      Uma falha isolada de rede **não** interrompe o script, mas pode deixar um
      ano sem os dados do conselho (já aconteceu com o CFC/2022). Se aparecer
      "Erro em", **rode o download de novo** antes de seguir.

- [ ] **3. Importar** — na pasta `orcamento_app`:
      ```
      python importar_dados.py
      ```
      Deve terminar com **"Reconciliação 100% OK"**. Se acusar divergência,
      pare e investigue a tabela `reconciliacao` no banco.

- [ ] **4. Recalcular a projeção** na tela **Fechamento 2026**, para os números
      refletirem os meses novos.

---

## Pontos de atenção

- **Mês de corte é automático.** Se o último lançamento do mês cair antes do
  **dia 28**, o mês é tratado como parcial e recua um mês. Para "fechar" um mês
  na projeção, o Diário dele precisa estar completo.

- **Overrides não se perdem ao reimportar — de fato, não só por convenção.**
  Métodos por conta, "Fechamento Manual" e a última projeção calculada ficam
  num banco à parte, `data/projecao.db` (ver `core/projecao_engine.py`), que o
  importador nunca toca. O `dados_reais.db` é regenerado do zero a cada
  reimport (dados-base, descartável); o `projecao.db` só muda quando você
  configura uma conta ou clica em **Recalcular**. Isso também protege contra
  um `git restore`/`checkout` acidental no banco de dados-base: como os dois
  arquivos são fisicamente separados, reverter um nunca apaga o outro.

- **Onde o banco mora (crucial na nuvem).** Rodando local, os bancos
  regenerados/atualizados já ficam em `data/` e o app lê direto. Rodando
  publicado (Streamlit Cloud), o disco do container é efêmero — uploads
  feitos só ali **não sobreviveriam a um reinício** do servidor sozinhos. Se a
  sincronização com o Google Drive estiver configurada (ver
  `orcamento_app/CONFIGURAR_GOOGLE_DRIVE.md`), isso já não é problema, mas
  repare que cada ação sincroniza um arquivo diferente: clicar em
  **Recalcular** na tela Fechamento reenvia o `projecao.db`; rodar a
  atualização mensal pelo botão da tela Início reenvia o `dados_reais.db`; o
  botão "Atualizar Google Drive agora" reenvia todos de uma vez. O app
  publicado passa a puxar as versões mais novas a cada reinício.

- **Backup rápido antes de reimportar (opcional):** copie `data/dados_reais.db`
  para um `.bak`. Como ele guarda os dados-base (não os overrides — esses já
  estão protegidos em `data/projecao.db`), um backup evita ter que rebaixar
  os CSVs de novo se algo der errado no download.
