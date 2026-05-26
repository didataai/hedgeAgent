# Análise MQL5 — P0_V4

## Objetivo deste relatório

Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.

## Fonte

- Família: `P0`
- Versão: `P0_V4`
- Arquivo: `Hedge_P0_V4.mq5`
- Linhas: `541`
- Gerado em UTC: `2026-05-26T18:57:51.624103+00:00`

## Properties

- Linha 5: `copyright` = `"xAI"`
- Linha 6: `link` = `""`
- Linha 7: `version` = `"1.17"`
- Linha 8: `strict` = ``
- Linha 9: `description` = `"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"`

## Includes

- Linha 11: `<Trade\Trade.mqh>`

## Inputs detectados

| linha | tipo | nome | default | comentário |
|---:|---|---|---|---|
| 16 | `double` | `HedgeSmallLot` | `0.03` | Lote inicial small hedge |
| 17 | `double` | `HedgeLargeLot` | `0.04` | Lote inicial large hedge |
| 18 | `double` | `LotIncrease` | `0.01` | Incremento normal por nível + net direcional fixed |
| 19 | `double` | `ExtraLotIncreaseOnRange` | `0.01` | Extra se range > threshold |
| 20 | `int` | `RangeThresholdPts` | `400` | Range em pts para extra increase |
| 21 | `double` | `StopThresholdUSD` | `-8.0` | Limite USD para stop (net small + directional) |
| 22 | `string` | `TriggerMode` | `"usd"` | "pts" ou "usd" |
| 23 | `double` | `TriggerValue` | `10.0` | Valor do trigger (pts ou net USD) |
| 24 | `int` | `MagicBase` | `12345` | Magic base (mude para cada instância!) |
| 25 | `string` | `EA_InstanceSuffix` | `"p0-1"` | Sufixo único no INÍCIO dos comentários |
| 26 | `double` | `MaxSpread` | `50.0` | Spread max em points |
| 27 | `bool` | `IgnoreSpreadOnReset` | `true` | Ignora spread após reset ou botão |
| 28 | `bool` | `ForceInitialHedge` | `false` | Força abertura mesmo com posições |
| 29 | `bool` | `ResetStateOnStart` | `false` | RESET ao iniciar |
| 32 | `color` | `CorBuy` | `clrGreen` |  |
| 33 | `color` | `CorSell` | `clrRed` |  |
| 34 | `color` | `CorNet` | `clrBlueViolet` |  |
| 35 | `color` | `CorLucro` | `clrBlue` |  |
| 36 | `int` | `TamanhoFonte` | `12` |  |
| 37 | `int` | `PosX` | `90` |  |
| 38 | `int` | `PosY` | `20` |  |
| 39 | `int` | `Espacamento` | `18` |  |
| 42 | `string` | `BotaoCloseReset` | `"Close_All_Reset"` |  |
| 43 | `int` | `BotaoPosX` | `20` |  |
| 44 | `int` | `BotaoPosY` | `20` |  |
| 45 | `int` | `BotaoLargura` | `140` |  |
| 46 | `int` | `BotaoAltura` | `30` |  |
| 47 | `color` | `CorBotao` | `clrRed` |  |
| 48 | `color` | `CorTextoBotao` | `clrWhite` |  |

## Funções detectadas

| linha | função | retorno | evento MQL5 |
|---:|---|---|---|
| 81 | `PositionExists` | `bool` | não |
| 83 | `GetProfit` | `double` | não |
| 88 | `GetPointsProfit` | `double` | não |
| 96 | `IsTriggered` | `bool` | não |
| 110 | `OpenPosition` | `ulong` | não |
| 166 | `ClosePosition` | `bool` | não |
| 177 | `CountOurPositions` | `int` | não |
| 188 | `AtualizarResumoNoGrafico` | `void` | não |
| 218 | `CloseAllOurPositionsAndReset` | `void` | não |
| 261 | `OnInit` | `int` | sim |
| 363 | `OnChartEvent` | `void` | sim |
| 374 | `OnTick` | `void` | sim |
| 533 | `OnDeinit` | `void` | sim |

## Pistas de lógica

- `has_magic_number`: `True`
- `has_spread_filter`: `True`
- `has_initial_hedge_cue`: `True`
- `has_directional_cue`: `True`
- `has_lot_increase_cue`: `True`
- `has_no_lot_increase_cue`: `False`
- `has_pending_order_cue`: `False`
- `has_recovery_cue`: `False`
- `has_close_all_button_cue`: `True`
- `has_reset_state_cue`: `True`
- `has_timer_event`: `False`
- `has_tick_event`: `True`
- `has_chart_event`: `True`
- `trade_keyword_hits`: `{'CTrade': 1, 'trade.Buy': 1, 'trade.Sell': 1, 'PositionSelect': 1, 'PositionSelectByTicket': 1, 'PositionsTotal': 4, 'PositionClose': 1}`
- `lot_keyword_hits`: `{'lot': 16, 'Lot': 73, 'lote': 1, 'HedgeSmallLot': 6, 'HedgeLargeLot': 6, 'LotIncrease': 7}`
- `hedge_keyword_hits`: `{'hedge': 6, 'Hedge': 25, 'small': 17, 'Small': 70, 'large': 20, 'Large': 75, 'directional': 7, 'Directional': 14, 'direcional': 3, 'isolating': 7, 'Isolating': 1, 'base': 3, 'Base': 17}`
- `risk_keyword_hits`: `{'StopThreshold': 3, 'MaxSpread': 4, 'DD': 1, 'stop': 2, 'Stop': 5, 'margin': 6}`

## Pontos fortes candidatos

- (medium) Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA.
- (medium) Possui pista de filtro de spread, útil para evitar entradas em condição ruim.
- (low) Possui pistas de estrutura hedge small/large ou travamento inicial.
- (medium) Possui pista de botão/rotina de fechamento ou reset operacional.

## Pontos fracos / riscos candidatos

- (medium) Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

## Pontos desconhecidos

- Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

## Amostra de comentários

- +------------------------------------------------------------------+
- |                    HedgeEA_Progressivo_v117.mq5                  |
- |                          xAI - Hedge Progressivo v1.17           |
- +------------------------------------------------------------------+
- --- Inputs ---
- Lote inicial small hedge
- Lote inicial large hedge
- Incremento normal por nível + net direcional fixed
- Extra se range > threshold
- Range em pts para extra increase
- Limite USD para stop (net small + directional)
- "pts" ou "usd"
- Valor do trigger (pts ou net USD)
- Magic base (mude para cada instância!)
- Sufixo único no INÍCIO dos comentários
- Spread max em points
- Ignora spread após reset ou botão
- Força abertura mesmo com posições
- RESET ao iniciar
- --- Resumo gráfico ---
- --- Botão ---
- --- Magics ---
- --- Prefixo globals ---
- --- Labels gráficos ---
- --- Globais persistentes ---
- --- Funções auxiliares ---
- +------------------------------------------------------------------+
- | Expert initialization                                            |
- +------------------------------------------------------------------+
- Cria labels do resumo
- Botão
- +------------------------------------------------------------------+
- | Chart Event                                                      |
- +------------------------------------------------------------------+
- +------------------------------------------------------------------+
- | Expert tick function                                             |
- +------------------------------------------------------------------+
- Trigger eliminação
- Calcula direcional para net 0.01
- Calcula direcional para net 0.01
