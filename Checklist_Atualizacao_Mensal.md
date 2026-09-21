# Checklist — Atualização Mensal dos Dados (Projeção Orçamento 2026)

> Rotina para incluir novos meses de execução no `dados_reais.db` sem erro.
> Tempo típico: **cerca de 10 segundos** pelo caminho recomendado.

## Caminho recomendado (um clique)

1. Abra o app (local ou publicado) na tela **Início**.
2. Confira a linha **"Dados atuais"** — mostra até que dia vai o Diário do
   ano corrente e qual é o último mês completo que a projeção considera.
3. Deixe marcado **"Recalcular a projeção (despesa e receita) logo após
   atualizar"** e o ano corrente em **"Anos a buscar na API"**.
4. Clique em **🔄 Atualizar dados agora**.

O botão busca direto na **API de dados abertos do CFC** só o conselho
projetado (CFC) e só o ano marcado — Diário completo, Orçamento Atualizado e
Plano de Contas —, reimporta para `dados_reais.db` **preservando os anos não
marcados**, roda a reconciliação Diário × Realizado, recalcula a projeção dos
dois ramos e, se a sincronização estiver configurada, reenvia
`dados_reais.db` e `projecao.db` ao Google Drive. O log completo fica num
expansor logo abaixo do botão; a mensagem final diz até que data o Diário
foi e qual passou a ser o mês de corte.

- **Verde** → tudo OK, projeção já recalculada — vá em **Fechamento 2026**.
- **Amarelo** → importou, mas a reconciliação acusou divergência —
  **revisar a tabela `reconciliacao` antes de usar**.
- **Vermelho** → a API não respondeu; **nada foi importado** (o banco
  anterior continua intacto). Tente de novo em alguns minutos.

Equivalente em linha de comando (na pasta `orcamento_app`):

```
python atualizar_mensal.py --api          # só o ano corrente
python importar_dados.py --api --anos 2022 2023 2024 2025 2026   # refazer tudo
```

Pelo CLI a projeção **não** é recalculada — abra **Fechamento 2026** e clique
em **Recalcular** (ou use o botão da tela Início, que já faz isso).

Seus overrides, métodos por conta e o reajuste da folha **continuam valendo**
em qualquer caminho — o importador nunca toca no `projecao.db`.

---

## Caminho antigo — scripts `baixar_*.py` + CSVs (só onde a pasta Códigos existe)

Baixa **27 conselhos × 5 anos** (~700 MB de CSV) para depois descartar 26/27
no primeiro filtro. Continua funcionando, mas só faz sentido para refazer a
base inteira a partir dos CSVs ou para conferir o caminho novo:

```
python atualizar_mensal.py                 # baixa + importa + reconcilia
python atualizar_mensal.py --pular-download # só reimporta os CSVs já baixados
```

Na tela Início, o mesmo fica no expansor **"Caminho antigo"** (aparece só
quando a pasta `Códigos` existe no computador). Passo a passo manual:

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
  na projeção, o Diário dele precisa estar completo — a linha "Dados atuais"
  da tela Início mostra os dois (data máxima do Diário e mês de corte).

- **Anos fechados não precisam ser rebaixados.** 2022–2025 alimentam só o
  perfil sazonal e não mudam mais; por isso o padrão do botão é buscar apenas
  o ano corrente. Marque mais anos só para refazer a base (ex.: banco novo
  num ambiente vazio — nesse caso o app já sugere todos os anos).

- **Overrides não se perdem ao reimportar — de fato, não só por convenção.**
  Métodos por conta, "Fechamento Manual" e a última projeção calculada ficam
  num banco à parte, `data/projecao.db` (ver `core/projecao_engine.py`), que o
  importador nunca toca. O `dados_reais.db` é dados-base, descartável; o
  `projecao.db` só muda quando você configura uma conta ou recalcula. Isso
  também protege contra um `git restore`/`checkout` acidental no banco de
  dados-base: como os dois arquivos são fisicamente separados, reverter um
  nunca apaga o outro.

- **Onde o banco mora (crucial na nuvem).** Rodando local, os bancos
  atualizados ficam em `data/` e o app lê direto. Rodando publicado
  (Streamlit Cloud), o disco do container é efêmero — por isso o botão
  **Atualizar dados agora** reenvia `dados_reais.db` (e `projecao.db`, se
  recalculou) para a pasta Data do Google Drive quando a sincronização está
  configurada (ver `orcamento_app/CONFIGURAR_GOOGLE_DRIVE.md`); o app
  publicado passa a puxar as versões mais novas a cada reinício. Clicar em
  **Recalcular** na tela Fechamento reenvia só o `projecao.db`; o botão
  "Atualizar Google Drive agora" reenvia todos de uma vez.

- **Backup rápido antes de reimportar (opcional):** copie `data/dados_reais.db`
  para um `.bak`. Como a API entrega o ano inteiro em segundos, hoje o backup
  só importa se a API sair do ar logo depois de uma importação com problema.
