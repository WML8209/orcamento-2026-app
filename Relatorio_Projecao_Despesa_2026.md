# Relatório de Projeção de Fechamento da Despesa 2026 — Por Conta Contábil

**Ferramenta**: Ferramenta de Projeção de Orçamento 2026 · **Conselho**: CFC · **Ano**: 2026 · **Ramo**: 6.3 (Execução da Despesa)

**Gerado em**: 2026-07-26 17:44:34 · **Diário disponível até**: 2026-06-17 · **Último mês completo (corte)**: Mai/2026


Este relatório documenta, conta por conta, como o sistema projetou o fechamento do orçamento de despesa de 2026. Cada conta mostra: o método aplicado e por quê, o valor já realizado (YTD), a projeção para os meses restantes, o fechamento total projetado (modelo oficial M3), a conferência independente (modelo M2, sazonal puro) e a **memória de cálculo completa** — a mesma fórmula que o sistema usou internamente, reproduzida aqui.

## Sumário executivo

- **Orçamento total 2026 (despesa)**: R$ 132.578.920,00
- **Realizado até Mai**: R$ 39.646.681,44 (29,9% do orçamento)
- **Fechamento projetado (M3, modelo oficial)**: R$ 113.040.391,74 (85,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 118.406.886,28 (89,3% do orçamento)
- **Diferença M3 vs M2**: R$ -5.366.494,54 (-4,5%)
- **Total de contas analisadas**: 92
- **Contas com configuração manual (override/reajuste específico)**: 0

**Distribuição por método:**

| Método | Nº contas | Fechamento projetado (M3) |
|---|---:|---:|
| Run-rate (média dos últimos meses completos) | 32 | R$ 35.193.955,07 |
| Sazonal (perfil histórico 2022–2025) | 44 | R$ 39.331.054,61 |
| Sazonal + reajuste de data-base (Pessoal) | 16 | R$ 38.515.382,05 |

**Distribuição por nível de confiança:**

| Confiança | Nº contas | Fechamento projetado (M3) |
|---|---:|---:|
| alta | 67 | R$ 94.267.092,61 |
| media | 11 | R$ 12.770.311,33 |
| baixa | 14 | R$ 6.002.987,79 |

- **Contas com divergência material M3×M2 (> 10,0%)**: 16
- **Contas com confiança baixa**: 14

## Metodologia por natureza de despesa

As 92 contas foram classificadas em 6 naturezas (pelo prefixo do código contábil), cada uma com o método de projeção mais adequado ao seu comportamento:

### Pessoal e Encargos

Contas de folha, encargos e benefícios (prefixo 6.3.1.1). Método: perfil sazonal histórico 2022–2025 (razão YTD ÷ % acumulado até o mês de corte), com reajuste de data-base aplicado globalmente a partir do mês parametrizado (ver seção de parâmetros abaixo). Racional: folha de pagamento segue um padrão mensal muito regular ano a ano (13º salário e férias concentram-se em meses previsíveis), então a curva histórica é o melhor preditor disponível.

### Contratos e Serviços

Contratos e serviços continuados (prefixo 6.3.1.3.02.01 — TI, terceirização, locações, representações, assessoria etc.). Método: run-rate — média dos últimos 3 meses completos de execução, projetada para os meses restantes (com reajuste contratual opcional, configurável por conta). Racional: contratos vigentes têm valor mensal relativamente estável no curto prazo; a média recente capta melhor o patamar atual do que uma curva histórica de anos anteriores, que pode não refletir reajustes ou trocas de fornecedor recentes.

### Diárias e Passagens

Diárias e passagens de conselheiros/colaboradores (prefixo 6.3.1.3.02.03 e 6.3.1.3.02.04). Método: sazonal histórico. Racional: o calendário de reuniões e plenárias se repete de forma similar ano a ano, então o perfil histórico é um bom preditor da distribuição ao longo do ano.

### Eventos e Exames

Organização/aplicação do Exame de Suficiência (conta 6.3.1.3.02.01.011, tratada como exceção de natureza por ter perfil de despesa muito distinto de um contrato comum). Método: sazonal histórico. Racional: os exames ocorrem em datas fixas no calendário (tipicamente 2 aplicações/ano), concentrando a despesa em meses específicos que se repetem ano a ano.

### Despesas de Capital

Despesas de capital — obras, equipamentos, investimentos (prefixo 6.3.2). Método: sazonal histórico, mas com confiança sempre rebaixada para 'baixa'. Racional: despesa de capital é por natureza "grumosa" (depende de decisões pontuais de compra/obra, não de um fluxo recorrente) — a estatística histórica é o melhor palpite disponível, mas não substitui o cronograma real de aquisições, que deve ser informado via override manual quando conhecido.

### Demais Despesas Correntes

Demais despesas correntes não classificadas nas naturezas acima. Método: sazonal histórico. Racional: método padrão quando não há característica especial que justifique run-rate ou tratamento determinístico.


**Cadeia de fallback do método sazonal** (usada por Pessoal, Diárias, Eventos, Capital e Demais): se a conta tem histórico e o perfil acumulado até o mês de corte é robusto (≥ 20% do total anual), usa-se a razão `YTD ÷ % acumulado histórico`. Se o perfil histórico é concentrado no fim do ano (ex.: 13º salário, que satura o método da razão), usa-se a média nominal dos meses restantes em 2024–2025, ajustada por um fator de crescimento do grupo (limitado a 0,8–1,3×). Se não há histórico, mas há YTD, projeta-se proporcionalmente ao tempo decorrido no ano. Se não há histórico nem YTD, usa-se 90,0% do orçamento como estimativa conservadora. Cada conta abaixo indica exatamente qual desses casos foi aplicado, na sua própria memória de cálculo.

## Detalhamento por conta

Contas agrupadas por natureza e ordenadas por fechamento projetado (maior para o menor). Cada bloco traz a memória de cálculo **verbatim** — o texto exato gerado pelo motor (`core/projecao_engine.py`) no momento do cálculo.

### Pessoal e Encargos — 16 conta(s)

Subtotal: Orçamento R$ 36.067.030,75 | Realizado YTD R$ 15.095.847,15 | Fechamento M3 R$ 38.515.382,05 (106,8%) | Conferência M2 R$ 38.515.382,05

#### `6.3.1.1.01.01.001` — SALÁRIOS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 15.300.000,00
- **Realizado até Mai**: R$ 6.579.688,38
- **Projeção meses restantes**: R$ 10.261.243,94
- **Fechamento projetado (M3)**: R$ 16.840.932,32 (110,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 16.840.932,32
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 6.579.688,38; perfil [2022, 2023, 2024, 2025] acumula 39.1% até o mês 5; fechamento = 6.579.688,38 / 0.3907 = R$ 16.840.932,32.

#### `6.3.1.1.01.02.001` — INSS ENTIDADE

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 5.184.305,75
- **Realizado até Mai**: R$ 2.168.178,12
- **Projeção meses restantes**: R$ 3.313.092,19
- **Fechamento projetado (M3)**: R$ 5.481.270,31 (105,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.481.270,31
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 2.168.178,12; perfil [2022, 2023, 2024, 2025] acumula 39.6% até o mês 5; fechamento = 2.168.178,12 / 0.3956 = R$ 5.481.270,31.

#### `6.3.1.1.01.01.003` — GRATIFICAÇÃO POR EXERCÍCIO DE CARGOS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 3.773.000,00
- **Realizado até Mai**: R$ 1.713.017,94
- **Projeção meses restantes**: R$ 2.724.087,28
- **Fechamento projetado (M3)**: R$ 4.437.105,22 (117,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 4.437.105,22
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.713.017,94; perfil [2022, 2023, 2024, 2025] acumula 38.6% até o mês 5; fechamento = 1.713.017,94 / 0.3861 = R$ 4.437.105,22.

#### `6.3.1.1.01.03.002` — PROGRAMA DE ALIMENT. AO TRABALHADOR-PAT

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.277.000,00
- **Realizado até Mai**: R$ 916.678,32
- **Projeção meses restantes**: R$ 1.505.944,99
- **Fechamento projetado (M3)**: R$ 2.422.623,31 (106,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.422.623,31
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 916.678,32; perfil [2022, 2023, 2024, 2025] acumula 37.8% até o mês 5; fechamento = 916.678,32 / 0.3784 = R$ 2.422.623,31.

#### `6.3.1.1.01.01.005` — FÉRIAS  

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.253.000,00
- **Realizado até Mai**: R$ 880.112,20
- **Projeção meses restantes**: R$ 1.180.412,85
- **Fechamento projetado (M3)**: R$ 2.060.525,05 (91,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.060.525,05
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 880.112,20; perfil [2022, 2023, 2024, 2025] acumula 42.7% até o mês 5; fechamento = 880.112,20 / 0.4271 = R$ 2.060.525,05.

#### `6.3.1.1.01.02.002` — FGTS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.929.044,00
- **Realizado até Mai**: R$ 838.093,65
- **Projeção meses restantes**: R$ 1.183.265,91
- **Fechamento projetado (M3)**: R$ 2.021.359,56 (104,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.021.359,56
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 838.093,65; perfil [2022, 2023, 2024, 2025] acumula 41.5% até o mês 5; fechamento = 838.093,65 / 0.4146 = R$ 2.021.359,56.

#### `6.3.1.1.01.03.003` — PLANO DE SAÚDE

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.000.000,00
- **Realizado até Mai**: R$ 803.263,40
- **Projeção meses restantes**: R$ 1.184.020,96
- **Fechamento projetado (M3)**: R$ 1.987.284,36 (99,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.987.284,36
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 803.263,40; perfil [2022, 2023, 2024, 2025] acumula 40.4% até o mês 5; fechamento = 803.263,40 / 0.4042 = R$ 1.987.284,36.

#### `6.3.1.1.01.01.004` — GRATIFICAÇÃO DE NATAL - 13º SALÁRIO

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.846.000,00
- **Realizado até Mai**: R$ 765.519,51
- **Projeção meses restantes**: R$ 1.098.780,18
- **Fechamento projetado (M3)**: R$ 1.864.299,69 (101,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.864.299,69
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 765.519,51; perfil [2022, 2023, 2024, 2025] acumula 41.1% até o mês 5; fechamento = 765.519,51 / 0.4106 = R$ 1.864.299,69.

#### `6.3.1.1.01.01.010` — INDENIZAÇÕES TRABALHISTAS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: media
- **Orçamento 2026**: R$ 497.500,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 420.248,75
- **Fechamento projetado (M3)**: R$ 420.248,75 (84,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 420.248,75
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 0,00; perfil histórico concentrado após o mês 5 (acum. 42.3%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.03 = R$ 420.248,75; fechamento = R$ 420.248,75.

#### `6.3.1.1.01.01.006` — ABONO PECUNIÁRIO DE FÉRIAS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 510.000,00
- **Realizado até Mai**: R$ 207.950,92
- **Projeção meses restantes**: R$ 192.405,33
- **Fechamento projetado (M3)**: R$ 400.356,25 (78,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 400.356,25
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 207.950,92; perfil [2022, 2023, 2024, 2025] acumula 51.9% até o mês 5; fechamento = 207.950,92 / 0.5194 = R$ 400.356,25.

#### `6.3.1.1.01.01.008` — SUBSTITUIÇÕES

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 200.000,00
- **Realizado até Mai**: R$ 100.680,61
- **Projeção meses restantes**: R$ 163.631,00
- **Fechamento projetado (M3)**: R$ 264.311,61 (132,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 264.311,61
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 100.680,61; perfil [2022, 2023, 2024, 2025] acumula 38.1% até o mês 5; fechamento = 100.680,61 / 0.3809 = R$ 264.311,61.

#### `6.3.1.1.01.02.003` — PIS SOBRE FOLHA DE PAGAMENTO

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 241.131,00
- **Realizado até Mai**: R$ 100.197,37
- **Projeção meses restantes**: R$ 152.945,52
- **Fechamento projetado (M3)**: R$ 253.142,89 (105,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 253.142,89
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 100.197,37; perfil [2022, 2023, 2024, 2025] acumula 39.6% até o mês 5; fechamento = 100.197,37 / 0.3958 = R$ 253.142,89.

#### `6.3.1.1.01.01.007` — HORAS EXTRAS

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 31.000,00
- **Realizado até Mai**: R$ 16.229,81
- **Projeção meses restantes**: R$ 32.671,11
- **Fechamento projetado (M3)**: R$ 48.900,92 (157,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 48.900,92
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 16.229,81; perfil [2022, 2023, 2024, 2025] acumula 33.2% até o mês 5; fechamento = 16.229,81 / 0.3319 = R$ 48.900,92.

#### `6.3.1.1.01.03.004` — PLANO ODONTOLÓGICO

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 15.000,00
- **Realizado até Mai**: R$ 3.337,82
- **Projeção meses restantes**: R$ 3.976,58
- **Fechamento projetado (M3)**: R$ 7.314,40 (48,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 7.314,40
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 3.337,82; perfil [2022, 2023, 2024, 2025] acumula 45.6% até o mês 5; fechamento = 3.337,82 / 0.4563 = R$ 7.314,40.

#### `6.3.1.1.01.03.001` — VALE TRANSPORTE

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: alta
- **Orçamento 2026**: R$ 10.000,00
- **Realizado até Mai**: R$ 2.899,10
- **Projeção meses restantes**: R$ 2.763,31
- **Fechamento projetado (M3)**: R$ 5.662,41 (56,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.662,41
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 2.899,10; perfil [2022, 2023, 2024, 2025] acumula 51.2% até o mês 5; fechamento = 2.899,10 / 0.5120 = R$ 5.662,41.

#### `6.3.1.1.01.01.009` — ADICIONAL NOTURNO 🔻 *(confiança baixa)*

- **Método**: Sazonal + reajuste de data-base (Pessoal)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 50,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 45,00
- **Fechamento projetado (M3)**: R$ 45,00 (90,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 45,00
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sem histórico e sem execução: orçamento R$ 50,00 x taxa de execução padrão 90% = R$ 45,00.

### Contratos e Serviços — 32 conta(s)

Subtotal: Orçamento R$ 53.873.729,40 | Realizado YTD R$ 12.074.302,34 | Fechamento M3 R$ 35.193.955,07 (65,3%) | Conferência M2 R$ 40.560.449,61

#### `6.3.1.3.02.01.005` — SERVIÇOS DE TECNOLOGIA DA INFORMAÇÃO ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 30.595.616,00
- **Realizado até Mai**: R$ 4.409.903,18
- **Projeção meses restantes**: R$ 8.941.024,91
- **Fechamento projetado (M3)**: R$ 13.350.928,09 (43,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 16.306.090,31
- **Divergência M3 vs M2**: 18,1%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 1.277.289,27; YTD R$ 4.409.903,18 + 7 meses x base = R$ 13.350.928,09.

#### `6.3.1.3.02.01.048` — SERVIÇOS DECORRENTES DE CONTRATOS DE TERCEIRIZAÇÃO ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 4.273.609,00
- **Realizado até Mai**: R$ 1.727.968,77
- **Projeção meses restantes**: R$ 2.759.604,52
- **Fechamento projetado (M3)**: R$ 4.487.573,29 (105,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 6.105.993,95
- **Divergência M3 vs M2**: 26,5%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 394.229,22; YTD R$ 1.727.968,77 + 7 meses x base = R$ 4.487.573,29.

#### `6.3.1.3.02.01.020` — SERVIÇOS DE REPRESENTAÇÕES ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 4.751.750,00
- **Realizado até Mai**: R$ 1.113.346,50
- **Projeção meses restantes**: R$ 2.597.808,50
- **Fechamento projetado (M3)**: R$ 3.711.155,00 (78,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.755.431,62
- **Divergência M3 vs M2**: 111,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 371.115,50; YTD R$ 1.113.346,50 + 7 meses x base = R$ 3.711.155,00.

#### `6.3.1.3.02.01.022` — DEMAIS SERVIÇOS PROFISSIONAIS ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 992.625,00
- **Realizado até Mai**: R$ 893.838,99
- **Projeção meses restantes**: R$ 2.085.624,31
- **Fechamento projetado (M3)**: R$ 2.979.463,30 (300,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.403.144,54
- **Divergência M3 vs M2**: 24,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 297.946,33; YTD R$ 893.838,99 + 7 meses x base = R$ 2.979.463,30.

#### `6.3.1.3.02.01.009` — SERV. DE SEGURANÇA PREDIAL E PREVENTIVA

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.674.263,00
- **Realizado até Mai**: R$ 688.971,46
- **Projeção meses restantes**: R$ 1.075.167,80
- **Fechamento projetado (M3)**: R$ 1.764.139,26 (105,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.784.620,39
- **Divergência M3 vs M2**: 1,1%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 153.595,40; YTD R$ 688.971,46 + 7 meses x base = R$ 1.764.139,26.

#### `6.3.1.3.02.01.040` — PUBLICAÇÕES TÉCNICAS

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.260.000,00
- **Realizado até Mai**: R$ 496.618,12
- **Projeção meses restantes**: R$ 1.076.834,99
- **Fechamento projetado (M3)**: R$ 1.573.453,11 (124,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.616.173,63
- **Divergência M3 vs M2**: 2,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 153.833,57; YTD R$ 496.618,12 + 7 meses x base = R$ 1.573.453,11.

#### `6.3.1.3.02.01.002` — SERVIÇO DE ASSESSORIA E CONSULTORIA ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.082.091,00
- **Realizado até Mai**: R$ 547.994,03
- **Projeção meses restantes**: R$ 1.005.512,95
- **Fechamento projetado (M3)**: R$ 1.553.506,98 (143,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.348.103,67
- **Divergência M3 vs M2**: 33,8%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 143.644,71; YTD R$ 547.994,03 + 7 meses x base = R$ 1.553.506,98.

#### `6.3.1.3.02.01.018` — SERVIÇO DE DIVULGAÇÃO INSTITUCIONAL ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 3.500.000,00
- **Realizado até Mai**: R$ 446.723,97
- **Projeção meses restantes**: R$ 1.042.355,93
- **Fechamento projetado (M3)**: R$ 1.489.079,90 (42,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 935.353,25
- **Divergência M3 vs M2**: 59,2%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 148.907,99; YTD R$ 446.723,97 + 7 meses x base = R$ 1.489.079,90.

#### `6.3.1.3.02.01.013` — ESTAGIOS

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 1.000.000,00
- **Realizado até Mai**: R$ 299.346,77
- **Projeção meses restantes**: R$ 410.522,19
- **Fechamento projetado (M3)**: R$ 709.868,96 (71,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 766.657,97
- **Divergência M3 vs M2**: 7,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 58.646,03; YTD R$ 299.346,77 + 7 meses x base = R$ 709.868,96.

#### `6.3.1.3.02.01.008` — SERV.DE LIMPEZA, CONSERV. E JARDINAGEM ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 929.000,00
- **Realizado até Mai**: R$ 244.050,30
- **Projeção meses restantes**: R$ 449.715,16
- **Fechamento projetado (M3)**: R$ 693.765,46 (74,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 609.032,67
- **Divergência M3 vs M2**: 13,9%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 64.245,02; YTD R$ 244.050,30 + 7 meses x base = R$ 693.765,46.

#### `6.3.1.3.02.01.032` — SERVIÇOS DE ENERGIA ELÉTRICA

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 661.200,00
- **Realizado até Mai**: R$ 266.655,18
- **Projeção meses restantes**: R$ 369.326,67
- **Fechamento projetado (M3)**: R$ 635.981,85 (96,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 626.407,41
- **Divergência M3 vs M2**: 1,5%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 52.760,95; YTD R$ 266.655,18 + 7 meses x base = R$ 635.981,85.

#### `6.3.1.3.02.01.004` — SERVIÇOS DE INSTRUTORES ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 208.800,00
- **Realizado até Mai**: R$ 150.436,23
- **Projeção meses restantes**: R$ 351.017,87
- **Fechamento projetado (M3)**: R$ 501.454,10 (240,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 370.241,10
- **Divergência M3 vs M2**: 35,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 50.145,41; YTD R$ 150.436,23 + 7 meses x base = R$ 501.454,10.

#### `6.3.1.3.02.01.030` — MANUTENÇÃO E CONSERV. DOS BENS IMÓVEIS ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 290.072,00
- **Realizado até Mai**: R$ 90.999,79
- **Projeção meses restantes**: R$ 159.412,70
- **Fechamento projetado (M3)**: R$ 250.412,49 (86,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 179.438,20
- **Divergência M3 vs M2**: 39,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 22.773,24; YTD R$ 90.999,79 + 7 meses x base = R$ 250.412,49.

#### `6.3.1.3.02.01.027` — LOCAÇÃO DE BENS IMÓVEIS ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 231.500,00
- **Realizado até Mai**: R$ 221.674,07
- **Projeção meses restantes**: R$ 26.253,50
- **Fechamento projetado (M3)**: R$ 247.927,57 (107,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 649.638,30
- **Divergência M3 vs M2**: 61,8%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 3.750,50; YTD R$ 221.674,07 + 7 meses x base = R$ 247.927,57.

#### `6.3.1.3.02.01.021` — SERVIÇOS DE APOIO ADMINISTRATIVO E OPERACIONAL

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 317.041,00
- **Realizado até Mai**: R$ 89.634,07
- **Projeção meses restantes**: R$ 155.670,08
- **Fechamento projetado (M3)**: R$ 245.304,15 (77,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 224.780,20
- **Divergência M3 vs M2**: 9,1%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 22.238,58; YTD R$ 89.634,07 + 7 meses x base = R$ 245.304,15.

#### `6.3.1.3.02.01.003` — SERVIÇOS ADVOCATÍCIOS ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 177.430,00
- **Realizado até Mai**: R$ 78.715,00
- **Projeção meses restantes**: R$ 110.201,00
- **Fechamento projetado (M3)**: R$ 188.916,00 (106,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 169.523,43
- **Divergência M3 vs M2**: 11,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 15.743,00; YTD R$ 78.715,00 + 7 meses x base = R$ 188.916,00.

#### `6.3.1.3.02.01.026` — LOC. DE BENS MÓVEIS, MÁQUINAS E EQUIP. ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 813.922,00
- **Realizado até Mai**: R$ 65.163,69
- **Projeção meses restantes**: R$ 98.141,52
- **Fechamento projetado (M3)**: R$ 163.305,21 (20,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 3.015.029,45
- **Divergência M3 vs M2**: 94,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 14.020,22; YTD R$ 65.163,69 + 7 meses x base = R$ 163.305,21.

#### `6.3.1.3.02.01.033` — SERVIÇOS DE ÁGUA E ESGOTO ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 160.000,00
- **Realizado até Mai**: R$ 56.781,90
- **Projeção meses restantes**: R$ 85.973,30
- **Fechamento projetado (M3)**: R$ 142.755,20 (89,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 162.186,78
- **Divergência M3 vs M2**: 12,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 12.281,90; YTD R$ 56.781,90 + 7 meses x base = R$ 142.755,20.

#### `6.3.1.3.02.01.035` — POST.DE CORRESPONDÊNCIA INSTITUCIONAL ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 100.000,00
- **Realizado até Mai**: R$ 45.209,95
- **Projeção meses restantes**: R$ 92.952,58
- **Fechamento projetado (M3)**: R$ 138.162,53 (138,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 106.805,16
- **Divergência M3 vs M2**: 29,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 13.278,94; YTD R$ 45.209,95 + 7 meses x base = R$ 138.162,53.

#### `6.3.1.3.02.01.007` — SERVIÇOS DE COPA E COZINHA 

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 105.000,00
- **Realizado até Mai**: R$ 32.994,30
- **Projeção meses restantes**: R$ 55.316,47
- **Fechamento projetado (M3)**: R$ 88.310,77 (84,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 81.019,78
- **Divergência M3 vs M2**: 9,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 7.902,35; YTD R$ 32.994,30 + 7 meses x base = R$ 88.310,77.

#### `6.3.1.3.02.01.017` — SERVIÇOS FOTOGRÁFICOS E VÍDEOS ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 35.984,00
- **Realizado até Mai**: R$ 23.882,00
- **Projeção meses restantes**: R$ 42.200,67
- **Fechamento projetado (M3)**: R$ 66.082,67 (183,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 98.114,94
- **Divergência M3 vs M2**: 32,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 6.028,67; YTD R$ 23.882,00 + 7 meses x base = R$ 66.082,67.

#### `6.3.1.3.02.01.029` — MANUTENÇÃO E CONSERVAÇÃO BENS MÓVEIS  ⚠️ *(divergência material M3×M2)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 274.198,00
- **Realizado até Mai**: R$ 19.637,81
- **Projeção meses restantes**: R$ 32.595,43
- **Fechamento projetado (M3)**: R$ 52.233,24 (19,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 46.423,61
- **Divergência M3 vs M2**: 12,5%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 4.656,49; YTD R$ 19.637,81 + 7 meses x base = R$ 52.233,24.

#### `6.3.1.3.02.01.010` — SERVIÇOS DE MEDICINA DO TRABALHO

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 149.664,00
- **Realizado até Mai**: R$ 15.818,70
- **Projeção meses restantes**: R$ 27.306,25
- **Fechamento projetado (M3)**: R$ 43.124,95 (28,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 30.181,84
- **Divergência M3 vs M2**: 42,9%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 3.900,89; YTD R$ 15.818,70 + 7 meses x base = R$ 43.124,95.

#### `6.3.1.3.02.01.037` — SERVIÇOS DE INTERNET

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 38.426,00
- **Realizado até Mai**: R$ 12.589,94
- **Projeção meses restantes**: R$ 20.366,01
- **Fechamento projetado (M3)**: R$ 32.955,95 (85,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 35.355,98
- **Divergência M3 vs M2**: 6,8%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 2.909,43; YTD R$ 12.589,94 + 7 meses x base = R$ 32.955,95.

#### `6.3.1.3.02.01.012` — SERVIÇOS DE INTERMEDIAÇÃO DE ESTAGIOS/APRENDIZES

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 51.815,40
- **Realizado até Mai**: R$ 9.506,34
- **Projeção meses restantes**: R$ 13.421,52
- **Fechamento projetado (M3)**: R$ 22.927,86 (44,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 24.853,30
- **Divergência M3 vs M2**: 7,7%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 1.917,36; YTD R$ 9.506,34 + 7 meses x base = R$ 22.927,86.

#### `6.3.1.3.02.01.036` — SERVIÇOS DE TELECOMUNICAÇÕES

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 27.800,00
- **Realizado até Mai**: R$ 8.922,10
- **Projeção meses restantes**: R$ 13.096,07
- **Fechamento projetado (M3)**: R$ 22.018,17 (79,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 20.457,43
- **Divergência M3 vs M2**: 7,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 1.870,87; YTD R$ 8.922,10 + 7 meses x base = R$ 22.018,17.

#### `6.3.1.3.02.01.039` — ASSINATURAS

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 58.500,00
- **Realizado até Mai**: R$ 10.120,48
- **Projeção meses restantes**: R$ 10.668,40
- **Fechamento projetado (M3)**: R$ 20.788,88 (35,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 49.948,40
- **Divergência M3 vs M2**: 58,4%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 1.524,06; YTD R$ 10.120,48 + 7 meses x base = R$ 20.788,88.

#### `6.3.1.3.02.01.045` — CÓPIAS E MICROFILMAGEM DE DOCUMENTOS

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 21.000,00
- **Realizado até Mai**: R$ 5.596,69
- **Projeção meses restantes**: R$ 9.363,41
- **Fechamento projetado (M3)**: R$ 14.960,10 (71,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 13.528,25
- **Divergência M3 vs M2**: 10,6%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 1.337,63; YTD R$ 5.596,69 + 7 meses x base = R$ 14.960,10.

#### `6.3.1.3.02.01.031` — MANUTENÇÃO E CONSERVAÇÃO DE VEÍCULOS

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: alta
- **Orçamento 2026**: R$ 12.423,00
- **Realizado até Mai**: R$ 1.202,01
- **Projeção meses restantes**: R$ 2.198,02
- **Fechamento projetado (M3)**: R$ 3.400,03 (27,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.512,30
- **Divergência M3 vs M2**: 35,3%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 314,00; YTD R$ 1.202,01 + 7 meses x base = R$ 3.400,03.

#### `6.3.1.3.02.01.001` — SERVIÇO DE AUDITORIA E PERÍCIA 🔻 *(confiança baixa)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 70.000,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 0,00
- **Fechamento projetado (M3)**: R$ 0,00 (0,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 16.016,43
- **Divergência M3 vs M2**: 100,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 0,00; YTD R$ 0,00 + 7 meses x base = R$ 0,00.

#### `6.3.1.3.02.01.024` — SEGUROS DE BENS IMÓVEIS 🔻 *(confiança baixa)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 5.000,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 0,00
- **Fechamento projetado (M3)**: R$ 0,00 (0,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 3.382,41
- **Divergência M3 vs M2**: 100,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 0,00; YTD R$ 0,00 + 7 meses x base = R$ 0,00.

#### `6.3.1.3.02.01.023` — SEGUROS DE BENS MÓVEIS 🔻 *(confiança baixa)*

- **Método**: Run-rate (média dos últimos meses completos)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 5.000,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 0,00
- **Fechamento projetado (M3)**: R$ 0,00 (0,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 4.002,93
- **Divergência M3 vs M2**: 100,0%
- **Memória de cálculo**:

  > Run-rate: média mensal dos meses 3-5 = R$ 0,00; YTD R$ 0,00 + 7 meses x base = R$ 0,00.

### Diárias e Passagens — 6 conta(s)

Subtotal: Orçamento R$ 10.712.081,00 | Realizado YTD R$ 7.133.225,92 | Fechamento M3 R$ 19.699.533,86 (183,9%) | Conferência M2 R$ 19.699.533,86

#### `6.3.1.3.02.03.002` — CONSELHEIROS - DIÁRIAS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.465.727,50
- **Realizado até Mai**: R$ 1.787.308,75
- **Projeção meses restantes**: R$ 3.656.137,42
- **Fechamento projetado (M3)**: R$ 5.443.446,17 (220,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.443.446,17
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.787.308,75; perfil [2022, 2023, 2024, 2025] acumula 32.8% até o mês 5; fechamento = 1.787.308,75 / 0.3283 = R$ 5.443.446,17.

#### `6.3.1.3.02.04.003` — COLABORADORES - PASSAGENS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.871.000,00
- **Realizado até Mai**: R$ 2.152.968,95
- **Projeção meses restantes**: R$ 2.866.918,95
- **Fechamento projetado (M3)**: R$ 5.019.887,90 (174,8% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.019.887,90
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 2.152.968,95; perfil [2022, 2023, 2024, 2025] acumula 42.9% até o mês 5; fechamento = 2.152.968,95 / 0.4289 = R$ 5.019.887,90.

#### `6.3.1.3.02.03.003` — COLABORADORES - DIÁRIAS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.124.620,50
- **Realizado até Mai**: R$ 1.250.021,11
- **Projeção meses restantes**: R$ 2.963.151,03
- **Fechamento projetado (M3)**: R$ 4.213.172,14 (198,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 4.213.172,14
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.250.021,11; perfil [2022, 2023, 2024, 2025] acumula 29.7% até o mês 5; fechamento = 1.250.021,11 / 0.2967 = R$ 4.213.172,14.

#### `6.3.1.3.02.04.002` — CONSELHEIROS - PASSAGENS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 2.351.776,00
- **Realizado até Mai**: R$ 1.357.887,69
- **Projeção meses restantes**: R$ 1.868.760,74
- **Fechamento projetado (M3)**: R$ 3.226.648,43 (137,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 3.226.648,43
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.357.887,69; perfil [2022, 2023, 2024, 2025] acumula 42.1% até o mês 5; fechamento = 1.357.887,69 / 0.4208 = R$ 3.226.648,43.

#### `6.3.1.3.02.03.001` — FUNCIONÁRIOS - DIÁRIAS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 492.457,00
- **Realizado até Mai**: R$ 288.443,62
- **Projeção meses restantes**: R$ 673.551,32
- **Fechamento projetado (M3)**: R$ 961.994,94 (195,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 961.994,94
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 288.443,62; perfil [2022, 2023, 2024, 2025] acumula 30.0% até o mês 5; fechamento = 288.443,62 / 0.2998 = R$ 961.994,94.

#### `6.3.1.3.02.04.001` — FUNCIONÁRIOS - PASSAGENS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 406.500,00
- **Realizado até Mai**: R$ 296.595,80
- **Projeção meses restantes**: R$ 537.788,49
- **Fechamento projetado (M3)**: R$ 834.384,29 (205,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 834.384,29
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 296.595,80; perfil [2022, 2023, 2024, 2025] acumula 35.5% até o mês 5; fechamento = 296.595,80 / 0.3555 = R$ 834.384,29.

### Eventos e Exames — 1 conta(s)

Subtotal: Orçamento R$ 13.373.500,00 | Realizado YTD R$ 1.461.550,37 | Fechamento M3 R$ 8.214.440,75 (61,4%) | Conferência M2 R$ 8.214.440,75

#### `6.3.1.3.02.01.011` — SELEÇÃO, TREINAMENTO E ORG/APLICAÇÃO DE EXAMES

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 13.373.500,00
- **Realizado até Mai**: R$ 1.461.550,37
- **Projeção meses restantes**: R$ 6.752.890,38
- **Fechamento projetado (M3)**: R$ 8.214.440,75 (61,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 8.214.440,75
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 1.461.550,37; perfil histórico concentrado após o mês 5 (acum. 19.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.80 = R$ 6.752.890,38; fechamento = R$ 8.214.440,75.

### Despesas de Capital — 8 conta(s)

Subtotal: Orçamento R$ 11.417.256,00 | Realizado YTD R$ 1.731.264,89 | Fechamento M3 R$ 5.945.261,29 (52,1%) | Conferência M2 R$ 5.945.261,29

#### `6.3.2.4.01.01.001` — AUXÍLIOS 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 4.211.170,00
- **Realizado até Mai**: R$ 1.337.179,46
- **Projeção meses restantes**: R$ 3.974.574,30
- **Fechamento projetado (M3)**: R$ 5.311.753,76 (126,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.311.753,76
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.337.179,46; perfil [2022, 2023, 2024, 2025] acumula 25.2% até o mês 5; fechamento = 1.337.179,46 / 0.2517 = R$ 5.311.753,76. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.03.01.003` — INSTALAÇÕES 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 4.890.000,00
- **Realizado até Mai**: R$ 288.521,16
- **Projeção meses restantes**: R$ 41.208,65
- **Fechamento projetado (M3)**: R$ 329.729,81 (6,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 329.729,81
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 288.521,16; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.30 = R$ 41.208,65; fechamento = R$ 329.729,81. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.01.01.004` — ESTUDOS E PROJETOS 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 1.840.000,00
- **Realizado até Mai**: R$ 73.850,00
- **Projeção meses restantes**: R$ 157.950,00
- **Fechamento projetado (M3)**: R$ 231.800,00 (12,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 231.800,00
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 73.850,00; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.30 = R$ 157.950,00; fechamento = R$ 231.800,00. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.03.01.002` — MÁQUINAS E EQUIPAMENTOS 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 382.700,00
- **Realizado até Mai**: R$ 17.839,55
- **Projeção meses restantes**: R$ 16.644,84
- **Fechamento projetado (M3)**: R$ 34.484,39 (9,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 34.484,39
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 17.839,55; perfil [2022, 2023, 2024, 2025] acumula 51.7% até o mês 5; fechamento = 17.839,55 / 0.5173 = R$ 34.484,39. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.03.01.008` — BIBLIOTECA 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 40.000,00
- **Realizado até Mai**: R$ 5.067,91
- **Projeção meses restantes**: R$ 13.994,62
- **Fechamento projetado (M3)**: R$ 19.062,53 (47,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 19.062,53
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 5.067,91; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.30 = R$ 13.994,62; fechamento = R$ 19.062,53. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.03.01.004` — UTENSÍLIOS DE COPA E COZINHA 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 15.000,00
- **Realizado até Mai**: R$ 8.806,81
- **Projeção meses restantes**: R$ 624,00
- **Fechamento projetado (M3)**: R$ 9.430,81 (62,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 9.430,81
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 8.806,81; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.30 = R$ 624,00; fechamento = R$ 9.430,81. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.01.01.001` — OBRAS E INSTALAÇÕES 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 10.000,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 9.000,00
- **Fechamento projetado (M3)**: R$ 9.000,00 (90,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 9.000,00
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sem histórico e sem execução: orçamento R$ 10.000,00 x taxa de execução padrão 90% = R$ 9.000,00. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

#### `6.3.2.1.05.01.002` — SOFTWARES 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 28.386,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 0,00
- **Fechamento projetado (M3)**: R$ 0,00 (0,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 0,00
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 0,00; perfil histórico concentrado após o mês 5 (acum. 94.7%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 1.30 = R$ 0,00; fechamento = R$ 0,00. [CAPITAL: projeção estatística é frágil — informar cronograma via override.]

### Demais Despesas Correntes — 29 conta(s)

Subtotal: Orçamento R$ 7.135.322,85 | Realizado YTD R$ 2.150.490,77 | Fechamento M3 R$ 5.471.818,71 (76,7%) | Conferência M2 R$ 5.471.818,71

#### `6.3.1.5.01.01.001` — SUBVENÇÕES

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 3.490.000,00
- **Realizado até Mai**: R$ 1.056.915,45
- **Projeção meses restantes**: R$ 1.730.213,28
- **Fechamento projetado (M3)**: R$ 2.787.128,73 (79,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.787.128,73
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 1.056.915,45; perfil histórico concentrado após o mês 5 (acum. 15.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 1.730.213,28; fechamento = R$ 2.787.128,73.

#### `6.3.1.3.02.06.001` — AUXÍLIO DESLOCAMENTO

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 202.920,00
- **Realizado até Mai**: R$ 150.238,37
- **Projeção meses restantes**: R$ 539.802,35
- **Fechamento projetado (M3)**: R$ 690.040,72 (340,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 690.040,72
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 150.238,37; perfil [2022, 2023, 2024, 2025] acumula 21.8% até o mês 5; fechamento = 150.238,37 / 0.2177 = R$ 690.040,72.

#### `6.3.1.9.01.01.003` — DESPESAS DE EXERCÍCIOS ANTERIORES

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 1.340.000,00
- **Realizado até Mai**: R$ 475.987,99
- **Projeção meses restantes**: R$ 180.895,24
- **Fechamento projetado (M3)**: R$ 656.883,23 (49,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 656.883,23
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 475.987,99; perfil histórico concentrado após o mês 5 (acum. 1.8%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 180.895,24; fechamento = R$ 656.883,23.

#### `6.3.1.9.01.01.006` — REEMBOLSO DE DESPESA COM COBRANÇA

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 150.000,00
- **Realizado até Mai**: R$ 67.429,44
- **Projeção meses restantes**: R$ 401.210,03
- **Fechamento projetado (M3)**: R$ 468.639,47 (312,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 468.639,47
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 67.429,44; perfil histórico concentrado após o mês 5 (acum. 17.4%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 401.210,03; fechamento = R$ 468.639,47.

#### `6.3.1.3.01.01.004` — CARTEIRAS DE IDENTIFICAÇÃO PROFISSIONAL

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 330.000,00
- **Realizado até Mai**: R$ 40.749,28
- **Projeção meses restantes**: R$ 121.470,35
- **Fechamento projetado (M3)**: R$ 162.219,63 (49,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 162.219,63
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 40.749,28; perfil histórico concentrado após o mês 5 (acum. 9.1%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 121.470,35; fechamento = R$ 162.219,63.

#### `6.3.1.4.01.02.002` — DESPESAS COM COBRANÇA

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 300.000,00
- **Realizado até Mai**: R$ 97.539,46
- **Projeção meses restantes**: R$ 61.547,71
- **Fechamento projetado (M3)**: R$ 159.087,17 (53,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 159.087,17
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 97.539,46; perfil [2022, 2023, 2024, 2025] acumula 61.3% até o mês 5; fechamento = 97.539,46 / 0.6131 = R$ 159.087,17.

#### `6.3.1.6.01.01.002` — IMPOSTOS E TAXAS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 126.500,00
- **Realizado até Mai**: R$ 80.793,15
- **Projeção meses restantes**: R$ 52.026,51
- **Fechamento projetado (M3)**: R$ 132.819,66 (105,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 132.819,66
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 80.793,15; perfil [2022, 2023, 2024, 2025] acumula 60.8% até o mês 5; fechamento = 80.793,15 / 0.6083 = R$ 132.819,66.

#### `6.3.1.2.01.01.002` — AUXÍLIO CRECHE 

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 123.441,85
- **Realizado até Mai**: R$ 46.168,30
- **Projeção meses restantes**: R$ 64.359,19
- **Fechamento projetado (M3)**: R$ 110.527,49 (89,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 110.527,49
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 46.168,30; perfil [2022, 2023, 2024, 2025] acumula 41.8% até o mês 5; fechamento = 46.168,30 / 0.4177 = R$ 110.527,49.

#### `6.3.1.3.01.01.018` — MATERIAIS DE DISTRIBUIÇÃO GRATUITA 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 375.070,00
- **Realizado até Mai**: R$ 22.216,50
- **Projeção meses restantes**: R$ 31.103,10
- **Fechamento projetado (M3)**: R$ 53.319,60 (14,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 53.319,60
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sem histórico: projeção uniforme — YTD R$ 22.216,50 ÷ (5/12) = R$ 53.319,60.

#### `6.3.1.3.01.01.017` — BENS MÓVEIS NÃO ATIVAVEIS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 27.990,00
- **Realizado até Mai**: R$ 18.350,75
- **Projeção meses restantes**: R$ 22.761,81
- **Fechamento projetado (M3)**: R$ 41.112,56 (146,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 41.112,56
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 18.350,75; perfil [2022, 2023, 2024, 2025] acumula 44.6% até o mês 5; fechamento = 18.350,75 / 0.4464 = R$ 41.112,56.

#### `6.3.1.4.01.02.001` — TAXA SOBRE SERVIÇOS BANCÁRIOS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 38.000,00
- **Realizado até Mai**: R$ 12.381,59
- **Projeção meses restantes**: R$ 19.655,57
- **Fechamento projetado (M3)**: R$ 32.037,16 (84,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 32.037,16
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 12.381,59; perfil [2022, 2023, 2024, 2025] acumula 38.6% até o mês 5; fechamento = 12.381,59 / 0.3865 = R$ 32.037,16.

#### `6.3.1.2.01.01.001` — AUXÍLIO EDUCAÇÃO

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 75.000,00
- **Realizado até Mai**: R$ 13.107,40
- **Projeção meses restantes**: R$ 18.361,92
- **Fechamento projetado (M3)**: R$ 31.469,32 (42,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 31.469,32
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 13.107,40; perfil [2022, 2023, 2024, 2025] acumula 41.7% até o mês 5; fechamento = 13.107,40 / 0.4165 = R$ 31.469,32.

#### `6.3.1.3.01.01.016` — MAT. DE HIGIENE, LIMPEZA E CONSERVAÇÃO

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 96.000,00
- **Realizado até Mai**: R$ 31.127,57
- **Projeção meses restantes**: R$ 302,74
- **Fechamento projetado (M3)**: R$ 31.430,31 (32,7% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 31.430,31
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 31.127,57; perfil histórico concentrado após o mês 5 (acum. 16.2%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 302,74; fechamento = R$ 31.430,31.

#### `6.3.1.3.01.02.001` — COMBUSTÍVEIS E LUBRIFICANTES

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 45.579,00
- **Realizado até Mai**: R$ 12.330,78
- **Projeção meses restantes**: R$ 15.657,73
- **Fechamento projetado (M3)**: R$ 27.988,51 (61,4% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 27.988,51
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 12.330,78; perfil [2022, 2023, 2024, 2025] acumula 44.1% até o mês 5; fechamento = 12.330,78 / 0.4406 = R$ 27.988,51.

#### `6.3.1.3.01.01.014` — UNIFORMES, TECIDOS E AVIAMENTOS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 30.000,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 25.295,78
- **Fechamento projetado (M3)**: R$ 25.295,78 (84,3% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 25.295,78
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 0,00; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 25.295,78; fechamento = R$ 25.295,78.

#### `6.3.1.3.01.09.001` — OUTROS MATERIAIS DE CONSUMO

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 14.500,00
- **Realizado até Mai**: R$ 4.568,72
- **Projeção meses restantes**: R$ 10.145,89
- **Fechamento projetado (M3)**: R$ 14.714,61 (101,5% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 14.714,61
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 4.568,72; perfil [2022, 2023, 2024, 2025] acumula 31.0% até o mês 5; fechamento = 4.568,72 / 0.3105 = R$ 14.714,61.

#### `6.3.1.3.01.01.015` — GÊNEROS DE ALIMENTAÇÃO

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 76.000,00
- **Realizado até Mai**: R$ 6.434,66
- **Projeção meses restantes**: R$ 7.165,22
- **Fechamento projetado (M3)**: R$ 13.599,88 (17,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 13.599,88
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 6.434,66; perfil [2022, 2023, 2024, 2025] acumula 47.3% até o mês 5; fechamento = 6.434,66 / 0.4731 = R$ 13.599,88.

#### `6.3.1.3.01.01.012` — MATERIAIS PARA MANUT. DE BENS IMÓVEIS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 48.300,00
- **Realizado até Mai**: R$ 4.129,91
- **Projeção meses restantes**: R$ 4.119,58
- **Fechamento projetado (M3)**: R$ 8.249,49 (17,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 8.249,49
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 4.129,91; perfil [2022, 2023, 2024, 2025] acumula 50.1% até o mês 5; fechamento = 4.129,91 / 0.5006 = R$ 8.249,49.

#### `6.3.1.3.01.01.013` — MATERIAL DE COPA E COZINHA

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 23.850,00
- **Realizado até Mai**: R$ 1.754,00
- **Projeção meses restantes**: R$ 3.994,10
- **Fechamento projetado (M3)**: R$ 5.748,10 (24,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.748,10
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.754,00; perfil [2022, 2023, 2024, 2025] acumula 30.5% até o mês 5; fechamento = 1.754,00 / 0.3051 = R$ 5.748,10.

#### `6.3.1.3.01.01.001` — MATERIAIS DE EXPEDIENTE

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 44.200,00
- **Realizado até Mai**: R$ 1.737,00
- **Projeção meses restantes**: R$ 3.996,55
- **Fechamento projetado (M3)**: R$ 5.733,55 (13,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 5.733,55
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.737,00; perfil [2022, 2023, 2024, 2025] acumula 30.3% até o mês 5; fechamento = 1.737,00 / 0.3030 = R$ 5.733,55.

#### `6.3.1.9.01.01.001` — SENTENÇAS JUDICIAIS 🔻 *(confiança baixa)*

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: baixa
- **Orçamento 2026**: R$ 15.000,00
- **Realizado até Mai**: R$ 1.817,46
- **Projeção meses restantes**: R$ 2.544,44
- **Fechamento projetado (M3)**: R$ 4.361,90 (29,1% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 4.361,90
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sem histórico: projeção uniforme — YTD R$ 1.817,46 ÷ (5/12) = R$ 4.361,90.

#### `6.3.1.3.01.01.005` — BANDEIRAS, FLÂMULAS E PLACAS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 6.500,00
- **Realizado até Mai**: R$ 1.522,00
- **Projeção meses restantes**: R$ 1.340,80
- **Fechamento projetado (M3)**: R$ 2.862,80 (44,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.862,80
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 1.522,00; perfil histórico concentrado após o mês 5 (acum. 0.0%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 1.340,80; fechamento = R$ 2.862,80.

#### `6.3.1.9.01.01.002` — INDENIZAÇÕES, RESTITUIÇÕES E REPOSIÇÕES

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 5.500,00
- **Realizado até Mai**: R$ 1.625,03
- **Projeção meses restantes**: R$ 474,73
- **Fechamento projetado (M3)**: R$ 2.099,76 (38,2% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 2.099,76
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 1.625,03; perfil [2022, 2023, 2024, 2025] acumula 77.4% até o mês 5; fechamento = 1.625,03 / 0.7739 = R$ 2.099,76.

#### `6.3.1.3.01.02.002` — PEÇAS E ACESSÓRIOS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 8.350,00
- **Realizado até Mai**: R$ 756,00
- **Projeção meses restantes**: R$ 745,70
- **Fechamento projetado (M3)**: R$ 1.501,70 (18,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 1.501,70
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 756,00; perfil [2022, 2023, 2024, 2025] acumula 50.3% até o mês 5; fechamento = 756,00 / 0.5034 = R$ 1.501,70.

#### `6.3.1.3.01.01.011` — MATERIAIS PARA MANUT. DE BENS MÓVEIS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 39.122,00
- **Realizado até Mai**: R$ 18,90
- **Projeção meses restantes**: R$ 718,34
- **Fechamento projetado (M3)**: R$ 737,24 (1,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 737,24
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 18,90; perfil histórico concentrado após o mês 5 (acum. 16.6%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 718,34; fechamento = R$ 737,24.

#### `6.3.1.3.01.01.008` — MATERIAIS DE INFORMÁTICA

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 35.500,00
- **Realizado até Mai**: R$ 372,42
- **Projeção meses restantes**: R$ 288,17
- **Fechamento projetado (M3)**: R$ 660,59 (1,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 660,59
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 372,42; perfil [2022, 2023, 2024, 2025] acumula 56.4% até o mês 5; fechamento = 372,42 / 0.5638 = R$ 660,59.

#### `6.3.1.3.01.01.010` — MATERIAIS ELÉTRICOS E DE TELEFONIA

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 37.500,00
- **Realizado até Mai**: R$ 202,11
- **Projeção meses restantes**: R$ 391,89
- **Fechamento projetado (M3)**: R$ 594,00 (1,6% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 594,00
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 202,11; perfil [2022, 2023, 2024, 2025] acumula 34.0% até o mês 5; fechamento = 202,11 / 0.3403 = R$ 594,00.

#### `6.3.1.6.01.01.003` — DESPESAS JUDICIAIS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: alta
- **Orçamento 2026**: R$ 28.000,00
- **Realizado até Mai**: R$ 216,53
- **Projeção meses restantes**: R$ 314,59
- **Fechamento projetado (M3)**: R$ 531,12 (1,9% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 531,12
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (razão): YTD jan-05 = R$ 216,53; perfil [2022, 2023, 2024, 2025] acumula 40.8% até o mês 5; fechamento = 216,53 / 0.4077 = R$ 531,12.

#### `6.3.1.3.01.01.002` — IMPRESSOS, FORMULÁRIOS E PAPÉIS

- **Método**: Sazonal (perfil histórico 2022–2025)
- **Confiança**: media
- **Orçamento 2026**: R$ 2.500,00
- **Realizado até Mai**: R$ 0,00
- **Projeção meses restantes**: R$ 424,64
- **Fechamento projetado (M3)**: R$ 424,64 (17,0% do orçamento)
- **Conferência (M2, sazonal puro)**: R$ 424,64
- **Divergência M3 vs M2**: 0,0%
- **Memória de cálculo**:

  > Sazonal (aditivo): YTD = R$ 0,00; perfil histórico concentrado após o mês 5 (acum. 34.7%) — usa média nominal [2024, 2025] dos meses restantes x fator do grupo 0.88 = R$ 424,64; fechamento = R$ 424,64.
