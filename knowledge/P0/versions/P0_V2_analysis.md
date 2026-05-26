# Análise MQL5 — P0_V2

## Objetivo deste relatório

Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.

## Fonte

- Família: `P0`
- Versão: `P0_V2`
- Arquivo: `Hedge_P0_V2-RangeAumentoLot-NaoFunciona2EAS.mq5`
- Linhas: `304`
- Gerado em UTC: `2026-05-26T18:50:44.248814+00:00`

## Properties

- Linha 5: `copyright` = `"xAI"`
- Linha 6: `link` = `""`
- Linha 7: `version` = `"1.11"`
- Linha 8: `strict` = ``
- Linha 9: `description` = `"Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"`

## Includes

- Linha 11: `<Trade\Trade.mqh>`

## Inputs detectados

| linha | tipo | nome | default | comentário |
|---:|---|---|---|---|
| 16 | `double` | `HedgeSmallLot` | `0.03` | Lote inicial small hedge |
| 17 | `double` | `HedgeLargeLot` | `0.04` | Lote inicial large hedge |
| 18 | `double` | `DirectionalLot` | `0.02` | Lote direcional base (fixo fallback) |
| 19 | `double` | `LotIncrease` | `0.01` | Incremento padrão por nível |
| 20 | `double` | `ExtraLotWhenFar` | `0.01` | Extra lot se range isolating > FarRangePts |
| 21 | `int` | `FarRangePts` | `400` | Threshold range pts para extra lot |
| 22 | `double` | `StopThresholdUSD` | `-8.0` | Limite USD para stop |
| 23 | `string` | `TriggerMode` | `"usd"` | "pts" ou "usd" |
| 24 | `double` | `TriggerValue` | `10.0` | Valor do trigger |
| 25 | `int` | `MagicBase` | `12345` | Magic base |
| 26 | `double` | `MaxSpread` | `50.0` | Spread max |
| 27 | `bool` | `IgnoreSpreadOnReset` | `true` |  |
| 28 | `bool` | `ForceInitialHedge` | `false` |  |
| 29 | `bool` | `ResetStateOnStart` | `false` |  |
| 32 | `string` | `BotaoCloseReset` | `"Close_All_Reset"` |  |
| 33 | `int` | `BotaoPosX` | `30` |  |
| 34 | `int` | `BotaoPosY` | `30` |  |
| 35 | `int` | `BotaoLargura` | `160` |  |
| 36 | `int` | `BotaoAltura` | `40` |  |
| 37 | `color` | `CorBotao` | `clrRed` |  |
| 38 | `color` | `CorTextoBotao` | `clrWhite` |  |

## Funções detectadas

| linha | função | retorno | evento MQL5 |
|---:|---|---|---|
| 62 | `PositionExists` | `bool` | não |
| 64 | `GetProfit` | `double` | não |
| 69 | `GetPointsProfit` | `double` | não |
| 77 | `IsTriggered` | `bool` | não |
| 86 | `OpenPosition` | `ulong` | não |
| 114 | `ClosePosition` | `bool` | não |
| 120 | `CountOurPositions` | `int` | não |
| 132 | `CloseAllOurPositionsAndReset` | `void` | não |
| 154 | `OnInit` | `int` | sim |
| 191 | `OnChartEvent` | `void` | sim |
| 199 | `OnTick` | `void` | sim |
| 302 | `OnDeinit` | `void` | sim |

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
- `trade_keyword_hits`: `{'CTrade': 1, 'trade.Buy': 1, 'trade.Sell': 1, 'PositionSelect': 3, 'PositionSelectByTicket': 3, 'PositionsTotal': 3, 'PositionClose': 1}`
- `lot_keyword_hits`: `{'lot': 15, 'Lot': 62, 'HedgeSmallLot': 5, 'HedgeLargeLot': 5, 'DirectionalLot': 3, 'LotIncrease': 2}`
- `hedge_keyword_hits`: `{'hedge': 3, 'Hedge': 16, 'small': 7, 'Small': 64, 'large': 17, 'Large': 69, 'directional': 4, 'Directional': 17, 'direcional': 1, 'isolating': 11, 'Isolating': 2, 'base': 2, 'Base': 11}`
- `risk_keyword_hits`: `{'StopThreshold': 2, 'MaxSpread': 4, 'stop': 1, 'Stop': 2}`

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
- |                    HedgeEA_Progressivo_v111.mq5                  |
- |                          xAI - Hedge Progressivo v1.11           |
- +------------------------------------------------------------------+
- --- Inputs ---
- Lote inicial small hedge
- Lote inicial large hedge
- Lote direcional base (fixo fallback)
- Incremento padrão por nível
- Extra lot se range isolating > FarRangePts
- Threshold range pts para extra lot
- Limite USD para stop
- "pts" ou "usd"
- Valor do trigger
- Magic base
- Spread max
- --- Botão ---
- --- Magics ---
- --- Globais ---
- Funções auxiliares
- +------------------------------------------------------------------+
- dinâmico
