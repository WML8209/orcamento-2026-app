# Análise Técnica — Ferramenta de Projeção de Orçamento 2026 (CFC)

**Repositório analisado:** `WML8209/orcamento-2026-app` · **Corte da projeção:** junho/2026 (dados do Diário até 21/07/2026, mês parcial recuado para jun) · **Escopo:** forma do projeto, adequação dos dados, adequação das métricas e tratamento das distorções apontadas.

---

## 1. Sumário executivo

O projeto é **sólido na engenharia e na integridade dos dados**, mas tem uma **fragilidade metodológica concentrada na atribuição automática de método por natureza** — é exatamente daí que nascem quase todas as distorções relatadas. Nenhuma delas é erro de dado; são consequências previsíveis de aplicar run-rate (média móvel) ou sazonal puro a contas cujo comportamento econômico não é nem run-rate nem sazonal.

As oito distorções se resolvem com os mecanismos que a própria ferramenta já oferece (override manual com justificativa, troca de método por conta, reclassificação de natureza) — **não exigem reescrever o motor**. Duas, porém, apontam para *bugs* que valem correção no código: o fechamento negativo de despesa (Softwares) e a ausência de piso/teto de sanidade nas projeções.

**Efeito agregado das correções:** puxam a **receita para baixo** em ~R$ 6,2 mi (zerar Fundo para Investimento, alinhar Juros e Amortizações ao orçado) e mexem na despesa em direções opostas. Como o resultado projetado hoje já é um **déficit de ~R$ 1,11 mi**, as correções de receita tendem a **ampliar o déficit** — conclusão relevante que precisa ser fechada com o valor de override de "Demais Serviços Profissionais" antes de reconsolidar.

---

## 2. Verificação da forma

### 2.1 Arquitetura — adequada e bem separada
- Separação limpa entre **ingestão** (`importar_dados.py` → `core/dados_reais.py`, CLI fora do Streamlit), **motor** (`core/projecao_engine.py`, sem dependência de UI) e **apresentação** (`pages/fechamento.py`, `core/exportar.py`, `core/tabela_html.py`). Isso permite testar e rodar a projeção pelo terminal (`projetar_fechamento.py`) sem subir a interface — boa prática.
- O app **não lê os CSVs brutos** (~630 MB): consome só o SQLite agregado `dados_reais.db`. Decisão correta de desempenho e de reprodutibilidade.
- `orcamento_historico.xlsx`, `bases.xlsx` e as telas do sistema manual antigo estão **fora da navegação** e explicitamente marcados como legado. Não interferem no motor, mas **poluem o repositório** — recomendo removê-los ou movê-los para uma pasta `legado/` para não induzir a erro quem for auditar.

### 2.2 Rastreabilidade — ponto forte
- Toda projeção carrega **memória de cálculo** (método, parâmetros, números e *fallback* usado). Isso é o que torna a ferramenta auditável e é o principal diferencial dela frente a uma planilha.
- Overrides manuais exigem **justificativa** registrada. Governança adequada para um órgão de controle.
- A documentação (`Orcamento2026.md`) registra decisões, bugs corrigidos e incidentes (inclusive uma perda silenciosa de dados evitada em CFC/2022). Nível de documentação acima da média.

### 2.3 Pontos de atenção de forma
- **Caminhos absolutos** de máquina pessoal gravados no banco (`C:\Users\wandney\...`) e em `config.py`. Funciona, mas amarra a reprodução ao ambiente de origem; idealmente parametrizar 100% por variável de ambiente.
- **Persistência em nuvem:** o `Home.py` avisa que uploads não sobrevivem a reinício no Streamlit Cloud. Para uso institucional recorrente, vale um armazenamento persistente (volume, banco gerenciado ou pasta sincronizada) em vez de re-upload manual.
- **Ausência de testes automatizados versionados** no repositório. A documentação cita verificações ("conferido ao centavo", "AppTest"), mas não há uma suíte de testes rodável. Para um motor que embasa decisão orçamentária, testes de regressão dos métodos seriam desejáveis.

---

## 3. Adequação dos dados

**Veredito: dados adequados e de alta integridade.**

- **Reconciliação Diário × Realizado oficial: 100%.** Todas as 597 contas-folha (6.2/6.3) dos quatro exercícios fechados (2022–2025) batem, **zero divergências**. Este é o teste mais importante de confiabilidade da base e ele passa integralmente.
- **Histórico suficiente para sazonalidade:** 4 anos completos (2022–2025) mais 2026 até junho. É o mínimo saudável para estimar perfil mensal — com a ressalva de que 4 pontos ainda deixam o perfil sensível a anos atípicos (ver §4).
- **Regra de sinal validada:** despesa = ΣD − ΣC; receita = ΣC − ΣD, sempre na conta-folha. Correta e documentada.
- **Corte automático robusto:** o mês parcial (jul/2026, dados só até o dia 21) é corretamente recuado para junho, evitando tratar um mês incompleto como fechado. **Consequência a registrar:** projeta-se **metade do ano** (jul–dez). Quanto mais cedo o corte, maior a incerteza — o fechamento de dezembro carrega 6 meses de projeção, não 1 ou 2.

**Limitação de dado, não de código:** o motor usa `orcamento_inicial`. Contas cujo orçamento foi alterado por crédito adicional durante o exercício (caso clássico do "Fundo para Investimento", que executa sem orçamento inicial) aparecem distorcidas na coluna de execução % e disparam projeções sem âncora orçamentária. Isso é origem direta de duas das distorções.

---

## 4. Adequação das métricas (núcleo da análise)

O motor atribui **um método por natureza** (M3, oficial) e roda **sazonal puro como conferência** (M2). O desenho conceitual é bom — inclusive o par M3/M2 com alerta de divergência acima de 10% é uma salvaguarda inteligente. O problema está nos **casos em que a natureza não determina o comportamento**:

| Método | Onde acerta | Onde erra (e por quê) |
|---|---|---|
| **Run-rate** (média dos últimos 3 meses × meses restantes) — usado em todos os `CONTRATOS` e nas receitas financeiras/capital | Contas **estáveis e recorrentes** (energia elétrica, terceirização mensal) | Contas **irregulares/episódicas**: extrapola um trimestre atípico para o ano inteiro. É o que estoura Representações (6,4 mi vs ~3 mi histórico) e as amortizações de CRC. |
| **Sazonal razão** (YTD ÷ % historicamente executado até o corte) | Contas com **perfil mensal estável entre anos** | Contas em **tendência forte** (TI cresce 1,6→16,5 mi em 4 anos: o perfil médio não captura a trajetória) ou com **gasto não recorrente** no YTD (Demais Serviços Profissionais, inflado por evento). |
| **Sazonal aditivo** (*fallback* com média nominal dos meses restantes) | Contas sem acúmulo relevante até o corte | **Não tem piso em zero:** meses históricos negativos (estornos/anulações em D−C) produzem **fechamento de despesa negativo** — ver Softwares. |

**Três lacunas de método a corrigir:**

1. **Ausência de piso/teto de sanidade.** Nenhuma projeção é limitada por `[0, +∞)` (despesa) nem ancorada a uma banda em torno do histórico ou do orçado. Um único trimestre atípico vira tendência anual sem freio. Recomendo, no mínimo, `fechamento_despesa = max(fechamento, ytd)` (não se "desgasta") e um alerta quando o fechamento sair de, digamos, ±30% da faixa histórica anual da conta.
2. **Run-rate cego a sazonalidade e a lumpiness.** Para contas de natureza "Contratos", vale testar se a conta é *recorrente-estável* (baixo desvio mensal → run-rate) ou *episódica* (alto desvio → sazonal ou média histórica anual). Hoje é run-rate para todas por padrão.
3. **Perfil sazonal frágil com 4 anos.** Um ano atípico entra no perfil médio com peso de 25%. Vale prever descarte de *outlier* anual ou uso de mediana em vez de média no perfil.

Nada disso invalida o motor — o M2 de conferência já sinaliza a maioria desses casos (as divergências de 15% a 137% que aparecem nas contas problemáticas são o próprio sistema pedimdo revisão humana). O motor está **funcionando como projetado**; o que falta é fechar o laço da revisão com regras e overrides.

---

## 5. Análise das distorções apontadas

Cada item abaixo traz a conta, a causa-raiz, o número atual e a correção recomendada (todas executáveis na tela **Fechamento 2026**, sem mexer no código, salvo onde indicado).

### RECEITAS

**5.1 Fundo para Investimento — `6.2.1.1.03.01.001` → zerar**
Orçamento inicial R$ 0 · YTD R$ 1.136.474 · **M3 = M2 = R$ 5.460.836**.
*Causa:* a conta executa por reflexo do Repasse do Fundo de Investimento em Tecnologia, mas o REDAM entrou como Cota-Parte durante o exercício — ou seja, **já está contado** na Cota-Parte. Como não tem orçamento inicial, o motor extrapolou o YTD pelo perfil sazonal e criou uma receita fantasma de R$ 5,46 mi (dupla contagem). A própria documentação do projeto (§14) já sinalizou "Demais Contribuições realizando sem orçamento".
*Correção:* **override de fechamento = 0**, justificativa "reflexo já considerado na Cota-Parte (REDAM)". Impacto: **−R$ 5.460.836 na receita**.

**5.2 Juros sobre Empréstimos e Receitas de Capital → igualar ao orçamento inicial**
- Juros sobre Empréstimos `6.2.1.3.01.01.001`: orçado R$ 1.041.789 · **M3 = R$ 1.192.254** (run-rate) · M2 R$ 752.647.
- Amortizações de CRC `6.2.2.4.01.02.*` (BA, MA, PE, PI, RO, RS): orçado **R$ 1.913.351** · **M3 = R$ 2.543.354** (run-rate).
*Causa:* juros e amortizações seguem **cronograma contratual**, não run-rate. O run-rate extrapola pagamentos concentrados (ex.: CRC-RO 68 mil → 204 mil; CRC-BA 689 mil → 1 mi). São exatamente as "6 divergências materiais" já citadas na §14 do projeto.
*Correção:* trocar o método dessas contas para **override = orçamento inicial** (ou método sazonal, se houver perfil de pagamento confiável). Impacto: Juros **−R$ 150.465** e Capital **−R$ 630.003**.

*Subtotal receita das correções: aproximadamente **−R$ 6,24 mi**.*

### DESPESAS

**5.3 Serviços de Tecnologia da Informação — `6.3.1.3.02.01.005` → usar M2**
Orçado R$ 28.628.256 · YTD R$ 6.077.605 · M3 (run-rate) R$ 14.330.397 · **M2 (sazonal) R$ 16.805.278** · divergência 15%.
*Causa:* conta em **forte crescimento** (16,5 mi em 2025) e com desembolso **concentrado no 2º semestre**. O run-rate, tomado sobre um trimestre médio, subestima; o sazonal capta melhor o back-loading. A preferência do colaborador por M2 é a mais defensável.
*Correção:* mudar método da conta para **Sazonal** (adota M2 como fechamento). Impacto: **+R$ 2.474.881** vs M3.

**5.4 Serviços de Representações — `6.3.1.3.02.01.020` → média entre máximo e mínimo históricos**
Orçado R$ 3.291.750 · M3 (run-rate) **R$ 6.440.734** · M2 R$ 2.721.166 · divergência **137%**.
*Causa:* conta **episódica** (plenárias/reuniões) rodada como run-rate. A janela abr–jun pegou um pico (998k, 115k, 1.033k) e anualizou em 6,4 mi — o dobro de qualquer ano histórico. Histórico anual: 2022 R$ 2,67 mi · 2023 R$ 2,74 mi · 2024 R$ 3,09 mi · 2025 R$ 3,41 mi. **Média (máx+mín)/2 = R$ 3.039.769**, coerente também com o orçado (3,29 mi).
*Correção:* **override = R$ 3.039.769** (a sugestão do colaborador é a melhor âncora aqui), justificativa "conta episódica; média da faixa histórica 2022–2025". Impacto: **−R$ 3.400.965** vs M3.

**5.5 Demais Serviços Profissionais — `6.3.1.3.02.01.022` → depurar o evento não recorrente**
Orçado R$ 992.625 · YTD R$ 896.879 · M3 R$ 1.664.827 · M2 R$ 2.411.318 · divergência 31%.
*Causa:* histórico baixíssimo (34 mil–196 mil/ano), mas 2026 saltou por um **evento pontual** (m3 R$ 513 mil + m4 R$ 380 mil). Ambos os métodos superprojetam porque tratam um gasto não recorrente como base. Nenhuma métrica estatística resolve isso — é caso de **override de julgamento**.
*Correção:* **override** com o valor que a área entender recorrente + o resíduo já contratado do evento (definir com a área técnica), justificativa "expurgo de evento não recorrente de 2026". **Este é o item que falta para reconsolidar o resultado** — recomendo fixá-lo antes de fechar os números.

**5.6 Serviços de Energia Elétrica — `6.3.1.3.02.01.032` → manter M3**
Orçado R$ 661.200 · M3 (run-rate) **R$ 485.097** · M2 R$ 528.216 · divergência 8%.
*Causa/leitura:* conta **estável e recorrente** (~R$ 50 mil/mês), exatamente o caso em que o run-rate acerta. O colaborador confirma que M3 se aproxima mais da execução. **Nenhuma ação** — é o padrão correto, e serve de contraprova de que o run-rate é adequado *quando* a conta é estável.

**5.7 Auxílio Deslocamento — `6.3.1.3.02.06.001` → agrupar com Diárias e Passagens**
Natureza atual: `DEMAIS` (sufixo `.02.06` não casa com a regra de Diárias/Passagens, que só pega `.02.03` e `.02.04`). Método sazonal · M3 = M2 = R$ 468.385.
*Causa:* é uma **questão de classificação/apresentação**, não de valor: como `DEMAIS` e `DIÁRIAS_PASSAGENS` usam o mesmo método sazonal, o fechamento não muda — muda só em qual subtotal de natureza a conta entra no relatório.
*Correção:* incluir `6.3.1.3.02.06` na regra de `DIARIAS_PASSAGENS` em `natureza_da_conta()` (`core/projecao_engine.py`, linha ~148). **Pequena alteração de código**, sem efeito no total, só na consolidação por natureza.

**5.8 Seleção, Treinamento e Org/Aplicação de Exames — `6.3.1.3.02.01.011` → elevar ~50%**
Orçado R$ 14.516.860 · YTD R$ 1.461.550 · **M3 = M2 = R$ 5.849.345** · divergência 0%.
*Causa:* conta de **eventos com calendário próprio** (exames concentrados no 2º semestre). O perfil sazonal médio pode estar suavizando a concentração real do ano do exame — daí o fechamento sair "bem abaixo". Como M3 e M2 coincidem (ambos sazonais), a conferência não pega o problema; só o conhecimento do calendário pega.
*Correção:* **override** para ~R$ 8,77 mi (M3 + 50%) ou o valor do cronograma de aplicação de provas informado pela área, justificativa "calendário de exames do 2º semestre". Impacto: **≈ +R$ 2.924.673**. (Confirmar o percentual exato com a área de exames — "pelo menos 50%" é piso.)

**5.9 Softwares — `6.3.2.1.05.01.002` → fechamento negativo (bug)**
Orçado R$ 28.386 · YTD R$ 0 · **M3 = M2 = −R$ 2.663**.
*Causa (bug real):* sem execução em 2026 (YTD 0), o sazonal cai no *fallback* aditivo e usa a **média nominal dos meses restantes** de 2024/2025. Em 2024, set/out tiveram **D−C negativo** (estornos: −2.148 e −5.134), puxando a média para baixo do zero. **Despesa não pode fechar negativa.**
*Correção imediata:* override = R$ 0 (ou o valor do orçado, se houver aquisição prevista). *Correção estrutural:* aplicar **piso em zero** no fechamento de despesa e tratar meses de D−C negativo (estorno) como 0 no cálculo do perfil/média. É a lacuna nº 1 da §4.

---

## 6. Recomendações priorizadas

**Imediato (fecha os números de 2026, tudo pela tela, sem código):**
1. Override **Fundo para Investimento = 0** (§5.1).
2. Override/método **Juros e Amortizações de CRC = orçamento inicial** (§5.2).
3. Método **TI = Sazonal** (§5.3).
4. Override **Representações = R$ 3.039.769** (§5.4).
5. Override **Exames = +50%** conforme calendário (§5.8).
6. Override **Softwares = 0** (§5.9).
7. **Definir com a área o override de Demais Serviços Profissionais** (§5.5) — item que trava a reconsolidação.
8. Reconsolidar Receita − Despesa e reavaliar o déficit (as correções de receita, ~−6,2 mi, tendem a ampliá-lo).

**Estrutural (robustez do motor, requer código + teste):**
9. **Piso em zero** no fechamento de despesa e tratamento de estornos (D−C < 0) no perfil — elimina a classe de bug do Softwares.
10. **Banda de sanidade** por conta (alerta quando o fechamento sai de ±30% da faixa histórica anual), complementando a divergência M3×M2.
11. **Discriminar run-rate vs. sazonal dentro de "Contratos"** por estabilidade mensal da conta (desvio-padrão), em vez de run-rate para todas.
12. Reclassificar **Auxílio Deslocamento** para Diárias/Passagens (§5.7).

**Higiene de projeto:**
13. Suíte de **testes de regressão** versionada para os métodos e o sinal do executado.
14. Remover/isolar arquivos **legado** e eliminar caminhos absolutos de máquina.

---

## 7. Conclusão

A ferramenta está **apta a embasar a projeção de 2026**, com uma ressalva importante: ela é um **motor estatístico que exige a camada de revisão humana que ela mesma foi desenhada para suportar**. Todas as distorções relatadas são legítimas e, sem exceção, foram **antecipadas pelo próprio sistema** (via divergência M3×M2, confiança "baixa" ou já registradas na documentação) — o que é, na prática, um atestado de que o desenho de conferência funciona. O trabalho que resta não é refazer o motor, e sim **aplicar os overrides justificados e implementar os três freios de sanidade** que impedem que um método correto para a maioria das contas produza resultados absurdos na minoria episódica.
