# Análise Técnica — Ferramenta de Projeção de Orçamento 2026 (CFC) — Atualização Julho/2026

**Repositório analisado:** `WML8209/orcamento-2026-app` (commit `6d87192`) · **Corte da projeção:** julho/2026 (Diário completo até 31/07/2026) · **Escopo:** revisão da análise de 26/07/2026 (`Analise_Projecao_Orcamento_2026.md`) à luz dos dados atualizados e dos ajustes já aplicados — o que foi resolvido, o que continua em aberto e o que mudou de figura com mais um mês de execução real.

---

## 1. Sumário executivo

Dos 8 itens da lista "Imediato" da análise de 26/07, **5 já estão resolvidos**: dois de receita (Fundo para Investimento, Juros sobre Empréstimos) tinham overrides aplicados por fora deste processo e seguem válidos; três de despesa foram fechados nesta revisão (Softwares = R$ 0,00, Auxílio Deslocamento reclassificado para Diárias e Passagens, Exame de Suficiência avaliado e **mantido sem override** — a tendência histórica não sustenta um valor acima do atual).

**Restam em aberto:** TI (ainda run-rate, divergência 18,7% contra o sazonal) e, principalmente, **Representações** — a recomendação original (override de R$ 3.039.769) ficou **inviável**: o realizado de abril a julho já soma R$ 3,18 milhões, mais que o próprio valor sugerido de override, então aplicá-lo forçaria o motor a projetar gasto negativo no segundo semestre. Amortizações de CRC também seguem sem correção (120,5% do orçado).

**Achado novo desta revisão:** a conta de receita "Indenizações" (`6.2.1.9.02.01.001`, orçado de apenas R$ 6.832) recebeu um lançamento isolado de R$ 1,3 milhão em julho — o método sazonal está extrapolando isso para um fechamento de R$ 4,74 milhões (694% do orçado). É a mesma classe de problema do Fundo para Investimento: evento não recorrente tratado como se fosse padrão sazonal.

**Achado estrutural (fora do escopo da análise original):** durante a atualização dos dados de julho, foi identificado e corrigido um bug real de infraestrutura — o app publicado sincroniza com o Google Drive a cada reinicialização e **o Drive sobrescreve os arquivos recém-atualizados via git**. Isso fez o app publicado continuar mostrando dados de junho por horas depois do push com os dados de julho já no repositório. Corrigido reenviando os arquivos certos ao Drive; ver §2.3.

**Resultado orçamentário projetado 2026:** Receita R$ 112.856.654,73 − Despesa R$ 119.689.522,98 = **déficit de R$ 6.832.868,25** — bem mais negativo que o déficit de R$ 2,37 milhões calculado em 09/08 com corte em junho. Um mês a mais de execução real (jul/2026) piorou a leitura em ~R$ 4,46 milhões, quase todo o efeito vindo do lado da despesa (Pessoal subiu para 110,6% do orçado, Diárias e Passagens para 149,4%).

---

## 2. Verificação da forma

### 2.1 O que mudou desde 26/07

- Os overrides de conta (`projecao_config`) agora persistem em `data/projecao.db`, **versionado no git** — antes da análise original isso já era assim, mas esta revisão confirmou na prática que o mecanismo funciona: os overrides de Fundo para Investimento e Juros sobreviveram à reimportação de dados de julho sem precisar ser refeitos (ver §5.1).
- Cada override aplicado carrega justificativa obrigatória, incluindo referência ao documento/seção que motivou a decisão — bom para auditoria futura.

### 2.2 Achado novo — sincronização com Google Drive sobrescreve dados atualizados

O `Home.py` roda `drive_sync.sincronizar_inicial()` a cada boot do container (`Home.py:8`), **antes** de qualquer outra coisa. A função (`core/drive_sync.py:125-144`) baixa do Drive e **sobrescreve a cópia local** de `dados_reais.db`/`projecao.db` sempre que o arquivo já existe lá — "Drive manda", segundo o próprio comentário do código.

Como a atualização de dados de julho foi feita via terminal local (`atualizar_mensal.py` + commit/push), e não pelo botão "🔄 Rodar atualização mensal agora" da tela Início (o único caminho que também sincroniza com o Drive automaticamente), o Drive continuou com a cópia de junho. Resultado: mesmo depois do push com os dados corretos, **todo reboot do app publicado restaurava os dados antigos por cima do clone novo do git**.

**Correção aplicada:** reenvio manual de `dados_reais.db` e `projecao.db` para a pasta "Data" do Drive (via API, mesma lógica de `enviar_arquivo()`) depois de cada atualização feita fora da tela Início. **Risco residual:** isso vai se repetir a cada atualização de dados feita por fora da interface — vale documentar no `Checklist_Atualizacao_Mensal.md` ou, melhor, sempre rodar a atualização mensal pelo botão da tela Início (que já teria evitado o problema).

### 2.3 Pontos de atenção já registrados em 26/07 (sem mudança)

Caminhos absolutos de máquina pessoal, ausência de suíte de testes automatizados versionada, e os arquivos de legado (`bases.xlsx`, `orcamento_historico.xlsx`) fora da navegação mas ainda no repositório — nada disso mudou nesta revisão.

---

## 3. Adequação dos dados

**Veredito: continua adequado e de alta integridade.**

- **Reconciliação Diário × Realizado oficial: 100%.** As mesmas 597 contas-folha (6.2/6.3) dos quatro exercícios fechados (2022–2025), zero divergências — reconfirmado após a reimportação de julho.
- **Mês de corte avançou de junho para julho.** O Diário está completo até 31/07/2026 (antes ia só até 21/07, mês parcial recuado para junho). Isso **reduz a janela de projeção de 6 para 5 meses** (ago–dez em vez de jul–dez) — um mês a menos de incerteza acumulada.
- **Consequência direta do mês a mais de dado real:** a Receita "Outras Receitas Correntes" e a conta "Indenizações" mudaram de patamar com um único lançamento de julho (ver §5.3) — ilustra bem por que o motor precisa ser revisado a cada atualização, não é uma foto única (o mesmo ponto já registrado no `Orcamento2026.md` §16 para a atualização de junho).

---

## 4. Adequação das métricas

Sem mudança na análise conceitual de 26/07 — o desenho do motor (M3 oficial por natureza + M2 sazonal de conferência) continua adequado, com as mesmas três lacunas de método já identificadas:

1. **Ausência de piso/teto de sanidade** — a correção pontual do Softwares (override manual) resolveu o sintoma numa conta, mas a lacuna estrutural (nenhuma projeção de despesa é limitada a `[0, +∞)` por padrão) **continua sem correção no motor**. O achado da conta "Indenizações" (§5.3) mostra que o mesmo tipo de problema (evento isolado extrapolado como recorrente) também ocorre do lado da receita, sem qualquer piso/teto automático.
2. **Run-rate cego a lumpiness** — ainda vale integralmente; é a causa raiz de Representações (§5.2) continuar piorando mês a mês em vez de se corrigir sozinho.
3. **Perfil sazonal frágil com poucos anos de histórico** — sem mudança; é a causa do "Indenizações" (§5.3) e, em menor grau, de "Demais Serviços Profissionais" continuar com M2 alto mesmo depois do M3 se autocorrigir.

---

## 5. Status das distorções apontadas (revisão julho/2026)

### 5.1 Itens resolvidos desde 26/07

| # | Item | Situação em 26/07 | Situação agora | Ação |
|---|---|---|---|---|
| 1 | Fundo para Investimento (`6.2.1.1.03.01.001`) | M3 = M2 = R$ 5.460.836 (fantasma) | **M3 = R$ 1.136.473,99** | Override já aplicado para o YTD, justificativa "Não há previsão de arrecadação para o exercício de 2026" — mais conservador que a sugestão original (zerar), mas resolve a dupla contagem |
| 2 | Juros sobre Empréstimos (`6.2.1.3.01.01.001`) | M3 R$ 1.192.254 (run-rate) | **M3 = R$ 1.041.789,00** | Override já aplicado = orçamento inicial, exatamente como recomendado |
| 6 | Softwares (`6.3.2.1.05.01.002`) | M3 = M2 = −R$ 2.663 (bug) | **M3 = R$ 0,00** | Override aplicado nesta revisão |
| 12 | Auxílio Deslocamento (`6.3.1.3.02.06.001`) | Natureza DEMAIS | **Natureza DIARIAS_PASSAGENS** | Reclassificado em `natureza_da_conta()` nesta revisão; valor projetado inalterado (R$ 445.062,40) |
| 5 | Exame de Suficiência (`6.3.1.3.02.01.011`) | M3 = M2 = R$ 5.849.345 (40,3% do orçado) | **M3 = M2 = R$ 14.334.036,25 (98,7% do orçado)** | Avaliado nesta revisão e **mantido sem override** — já é o maior valor histórico da conta e está alinhado com a tendência de execução (75%→89%→91%→97%→99%); a recomendação original de +50% ficou obsoleta com o dado de julho |

Os itens 1 e 2 não foram aplicados por este processo de análise — os overrides já existiam em `projecao.db` quando esta revisão começou, provavelmente configurados diretamente na tela Fechamento 2026 em algum momento entre 26/07 e agora. Ficam registrados aqui como confirmação de que continuam corretos.

### 5.2 Itens ainda em aberto

**Serviços de Tecnologia da Informação (`6.3.1.3.02.01.005`)** — sem mudança de fundo: orçado R$ 28.318.256 · YTD R$ 7.132.566,13 · M3 (run-rate) R$ 13.089.486,21 · M2 (sazonal) R$ 16.100.700,51 · divergência 18,7%. A recomendação de trocar para método Sazonal (§5.3 do documento original) segue válida e não foi aplicada.

**Serviços de Representações (`6.3.1.3.02.01.020`) — piorou e a recomendação original ficou inviável.** Histórico anual nunca passou de R$ 3,41 milhões (2022–2025); a recomendação de 26/07 era um override de R$ 3.039.769 (média da faixa histórica). Só que o realizado de 2026 (abril a julho, 4 meses seguidos de ~R$ 1 milhão cada: 998k / 115k / 1.034k / 1.034k) **já soma R$ 3.180.528,50** — mais que o próprio valor de override sugerido. Aplicá-lo faria o motor projetar gasto **negativo** em agosto–dezembro para compensar, o que não faz sentido. M3 atual (run-rate) já foi a R$ 6.817.559,33 (divergência de 90,9% contra o M2). Isto deixou de ser um "trimestre atípico" (a leitura de 26/07) e passou a ser um padrão sustentado de 4 meses — **recomendo tratar como item prioritário de revisão humana**, não como override mecânico: ou há uma razão institucional real (mais eventos/reuniões em 2026), ou há um problema de classificação/lançamento que vale investigar antes de qualquer ajuste numérico.

**Amortizações de CRC (`6.2.2.4.01.02.*`)** — segue sem override: subtotal orçado R$ 1.913.351 · M3 R$ 2.305.703,19 (120,5%). Contas individuais como `.021` (orçado R$ 68.051 → M3 R$ 181.470,13) e `.023` (orçado R$ 625.000 → M3 R$ 828.000,00) continuam com o run-rate extrapolando pagamentos concentrados. Recomendação original (override = orçamento inicial por conta) não aplicada.

**Serviços de Energia Elétrica (`6.3.1.3.02.01.032`)** — continua estável e sem necessidade de ação: orçado R$ 661.200 · M3 R$ 492.685,09 · M2 R$ 572.588,07 · divergência 14,0% (era 8% em 26/07; ainda dentro do esperado para uma conta recorrente).

**Demais Serviços Profissionais (`6.3.1.3.02.01.022`)** — o M3 se autocorrigiu sozinho: caiu de R$ 1.664.827 (26/07) para **R$ 903.195,66**, porque a janela de run-rate (últimos 3 meses completos) já não inclui mais o pico de março/abril do evento pontual. Hoje M3 está praticamente igual ao YTD (R$ 896.878,99) — não precisa mais de override de julgamento como sugerido originalmente. A divergência M3×M2 continua alta (62,5%) só porque o M2 (sazonal) ainda reflete o mesmo evento no perfil do ano — sem efeito prático, já que o M3 é o número oficial.

### 5.3 Achado novo — Indenizações (`6.2.1.9.02.01.001`, receita)

Orçado apenas R$ 6.832 — uma conta de controle, sem expectativa de movimento relevante. Histórico 2022–2024 nunca passou de R$ 17.001/ano (2025 sem lançamento). Em **julho/2026, um único lançamento de R$ 1.300.836,66** fez o YTD saltar para R$ 1.322.613,20. O método sazonal, aplicado sem qualquer piso/teto, está extrapolando isso para um **fechamento de R$ 4.738.263,51 — 694% do orçado**, puxando sozinho toda a natureza "Outras Receitas Correntes" para 5.449% do respectivo orçamento (R$ 87.410 orçados, R$ 4.762.725,65 projetados).

É exatamente a mesma classe de problema do Fundo para Investimento (§5.1, item 1): um evento sem orçamento equivalente, tratado pelo motor como se fosse um padrão recorrente que vai se repetir mês a mês. **Recomendação:** override para algo próximo do YTD (R$ 1.322.613,20), com justificativa condicionada a confirmar se o lançamento de julho é mesmo não recorrente (indenização judicial, seguro, ressarcimento pontual) — isso é informação que só a área financeira tem; não apliquei o override sem essa confirmação.

### 5.4 Outros sinais (não aprofundados nesta revisão)

- **Diárias e Passagens (grupo, despesa)** fecha em **149,4% do orçado** (R$ 18.713.364,00 projetado contra R$ 12.525.001,00 orçado — orçamento já inclui os R$ 352.920 do Auxílio Deslocamento reclassificado). Este é o mesmo sinal apontado na primeira rodada do motor, em maio/2026 (`Orcamento2026.md` §11: "Diárias e Passagens projetam 184% do orçamento... item prioritário de análise") — segue sem tratamento dedicado nas rodadas de override, mesmo tendo melhorado de 184% para 149% com mais dados reais.
- **15 contas de Contratos (run-rate) com divergência M3×M2 acima de 10%** (mesma ordem de grandeza que em 26/07, composição mudou): além de TI e Representações, aparecem agora com destaque Locação de Bens Imóveis (73,1%), Demais Serviços Profissionais (62,5%, ver §5.2), Serviços Fotográficos e Vídeos (56,1%), Assessoria e Consultoria (55,6%), Locação de Bens Móveis (41,7%), Publicações Técnicas (41,4%).
- **12 contas com confiança "baixa"** — majoritariamente Capital e contas sem histórico, mesmo padrão de 26/07 (cronogramas não informados via Fechamento Manual).

---

## 6. Recomendações priorizadas (revisão)

| # | Recomendação | Status |
|---|---|---|
| 1 | Override Fundo para Investimento | ✅ Já aplicado (fora deste processo) |
| 2 | Override Juros/Amortizações CRC (Juros) | ✅ Já aplicado (fora deste processo) — **Amortizações de CRC continuam pendentes**, ver §5.2 |
| 3 | Método TI = Sazonal | ⏳ Pendente |
| 4 | Override Representações | ❌ Inviável como formulado originalmente — precisa de nova decisão informada (ver §5.2), não é mais um ajuste mecânico |
| 5 | Override Exames +50% | ✅ Reavaliado e descartado — mantido sem override (ver §5.1) |
| 6 | Override Softwares = 0 | ✅ Aplicado nesta revisão |
| 7 | Override Demais Serviços Profissionais | ✅ Resolvido sozinho pela atualização de dados — não precisa mais de override (ver §5.2) |
| 8 | Reconsolidar Receita − Despesa | ✅ Feito — déficit de R$ 6.832.868,25 |
| 12 | Reclassificar Auxílio Deslocamento | ✅ Aplicado nesta revisão |
| **novo** | Override Indenizações (receita) | ⏳ Pendente confirmação da área financeira (ver §5.3) |
| **novo** | Corrigir sincronização Google Drive | ✅ Corrigido nesta revisão (reenvio manual); risco residual documentado em §2.2 |

**Itens estruturais e de higiene (9-11, 13-14 do documento original)** seguem todos pendentes — nenhum requer código além do que já foi tocado nesta revisão (a reclassificação do item 12 já estava nessa lista).

---

## 7. Conclusão

A atualização de julho confirmou o diagnóstico geral de 26/07: o motor está **funcionando como projetado**, e a maioria das distorções continua sendo antecipada pelo próprio sistema (divergência M3×M2, confiança baixa) ou resolvida sozinha conforme mais dados reais entram (Demais Serviços Profissionais, Exame de Suficiência). Dos 8 itens imediatos originais, 5 estão hoje resolvidos e 1 (Amortizações de CRC) segue pendente sem mudança de diagnóstico.

O ponto que merece atenção diferente de 26/07 é **Representações**: o que era lido como "um trimestre atípico" em junho se tornou um padrão sustentado de quatro meses em julho, e a saída simples (override para a média histórica) deixou de ser matematicamente válida. Isso é, por si, um sinal de que a conta pode estar refletindo uma mudança real de comportamento em 2026 — vale investigação com a área responsável antes de qualquer ajuste numérico, não outro cálculo automático.

O achado de infraestrutura (sincronização com Google Drive sobrescrevendo dados atualizados) não estava no escopo da análise original, mas é o tipo de problema que **invalidaria silenciosamente qualquer uma das correções acima** se não tivesse sido pego: por horas, o app publicado mostrou dados de junho mesmo depois do commit e push com os dados de julho corretos. Vale formalizar no processo de atualização mensal (`Checklist_Atualizacao_Mensal.md`) que toda atualização feita fora da tela Início precisa de reenvio manual ao Drive, ou migrar a rotina para sempre passar pelo botão da interface.
