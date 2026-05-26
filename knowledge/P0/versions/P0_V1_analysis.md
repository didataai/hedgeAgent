# Análise MQL5 — P0_V1

## Objetivo deste relatório

Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.

## Fonte

- Família: `P0`
- Versão: `P0_V1`
- Arquivo: `Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5`
- Linhas: `643`
- Gerado em UTC: `2026-05-26T21:09:40.299275+00:00`

## Properties

- Linha 6: `strict` = ``
- Linha 7: `description` = `"Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."`

## Includes

- Linha 9: `<Trade/Trade.mqh>`

## Inputs detectados

| linha | tipo | nome | default | comentário |
|---:|---|---|---|---|
| 13 | `ulong` | `MagicNumber` | `20260206` |  |
| 14 | `string` | `CommentText` | `"P2_A"` |  |
| 15 | `bool` | `AutoStart` | `true` |  |
| 16 | `double` | `StartLot` | `0.02` |  |
| 17 | `int` | `RangePts` | `300` |  |
| 18 | `double` | `StepLot` | `0.01` |  |
| 19 | `double` | `HedgeExtraLot` | `0.01` |  |
| 20 | `int` | `DeviationPts` | `30` |  |
| 21 | `int` | `HedgeOffsetPts` | `30` |  |
| 22 | `double` | `MinLot` | `0.01` |  |
| 23 | `int` | `CooldownMs` | `800` |  |
| 24 | `int` | `TimerMs` | `1200` |  |
| 25 | `int` | `ReturnTolPts` | `5` |  |
| 28 | `color` | `CorBuy` | `clrLime` |  |
| 29 | `color` | `CorSell` | `clrTomato` |  |
| 30 | `color` | `CorNet` | `clrDeepSkyBlue` |  |
| 31 | `color` | `CorProfit` | `clrDodgerBlue` |  |
| 32 | `int` | `FonteUI` | `12` |  |
| 33 | `int` | `PosX_UI` | `90` |  |
| 34 | `int` | `PosY_UI` | `20` |  |
| 35 | `int` | `Esp_UI` | `18` |  |
| 38 | `string` | `BotaoCloseAll` | `"Close_All_EA"` |  |
| 39 | `int` | `BotaoPosX` | `20` |  |
| 40 | `int` | `BotaoPosY` | `20` |  |
| 41 | `int` | `BotaoW` | `120` |  |
| 42 | `int` | `BotaoH` | `30` |  |
| 43 | `color` | `CorBotao` | `clrRed` |  |
| 44 | `color` | `CorTxtBotao` | `clrWhite` |  |

## Funções detectadas

| linha | função | retorno | evento MQL5 |
|---:|---|---|---|
| 65 | `NormalizeLot` | `double` | não |
| 76 | `IsTradeAllowedNow` | `bool` | não |
| 84 | `IsMyPosByTicket` | `bool` | não |
| 93 | `IsMyOrderByTicket` | `bool` | não |
| 102 | `MyPositionsCount` | `int` | não |
| 113 | `CycleTag` | `string` | não |
| 115 | `Cmt` | `string` | não |
| 117 | `Prefix` | `string` | não |
| 119 | `FindTicketByExactComment` | `ulong` | não |
| 132 | `PrintState` | `void` | não |
| 146 | `CreateUI` | `void` | não |
| 210 | `UpdateUI` | `void` | não |
| 238 | `CloseAllByMagic` | `void` | não |
| 273 | `OpenStartHedge` | `bool` | não |
| 302 | `TriggerFromInitial` | `bool` | não |
| 340 | `OpenDirAndLockFromBase` | `bool` | não |
| 427 | `ResolveOnHedgeProfit` | `bool` | não |
| 517 | `TryTriggerFromSingleBase` | `bool` | não |
| 557 | `OnInit` | `int` | sim |
| 567 | `OnDeinit` | `void` | sim |
| 579 | `OnTimer` | `void` | sim |
| 584 | `OnChartEvent` | `void` | sim |
| 594 | `OnTick` | `void` | sim |

## Pistas de lógica

- `has_magic_number`: `True`
- `has_spread_filter`: `False`
- `has_initial_hedge_cue`: `False`
- `has_directional_cue`: `True`
- `has_lot_increase_cue`: `False`
- `has_no_lot_increase_cue`: `False`
- `has_pending_order_cue`: `True`
- `has_recovery_cue`: `True`
- `has_close_all_button_cue`: `True`
- `has_reset_state_cue`: `False`
- `has_timer_event`: `True`
- `has_tick_event`: `True`
- `has_chart_event`: `True`
- `trade_keyword_hits`: `{'CTrade': 1, 'trade.Buy': 2, 'trade.Sell': 2, 'PositionSelect': 12, 'PositionSelectByTicket': 12, 'PositionsTotal': 6, 'OrdersTotal': 2, 'PositionClose': 6, 'OrderDelete': 2}`
- `lot_keyword_hits`: `{'lot': 15, 'Lot': 33, 'StepLot': 2, 'MinLot': 4}`
- `hedge_keyword_hits`: `{'hedge': 33, 'Hedge': 12, 'base': 64, 'Base': 7}`
- `pending_keyword_hits`: `{'pending': 8, 'BUY_LIMIT': 2, 'SELL_LIMIT': 1, 'BUY_STOP': 1, 'SELL_STOP': 2}`

## Pontos fortes candidatos

- (medium) Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA.
- (medium) Possui pista de botão/rotina de fechamento ou reset operacional.

## Pontos fracos / riscos candidatos

- (low) Não foi detectada pista clara de filtro de spread nesta análise textual.

## Pontos desconhecidos

- Há pistas de ordens pendentes, mas a sequência exata de criação/renovação ainda precisa ser interpretada.
- Há pistas de recovery/resolve, mas a regra matemática de recuperação ainda precisa ser validada.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

## Amostra de comentários

- +------------------------------------------------------------------+
- | Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5         |
- | Diego + Grok                                                     |
- | Travamento inicial com pendings no preço base (LIMIT antes STOP) |
- +------------------------------------------------------------------+
- ---------------------- Inputs
- UI Config
- Botão
- ---------------------- State
- UI Labels
- +------------------------------------------------------------------+
- | Helpers                                                          |
- +------------------------------------------------------------------+
- sem & !!!
- +------------------------------------------------------------------+
- | UI - Resumo gráfico                                              |
- +------------------------------------------------------------------+
- +------------------------------------------------------------------+
- | Close All                                                        |
- +------------------------------------------------------------------+
- +------------------------------------------------------------------+
- | Core Logic                                                       |
- +------------------------------------------------------------------+
- Coloca LIMIT primeiro
- FIX: declare all variables here
- Limpa pendings sobrando
- +------------------------------------------------------------------+
- | Events                                                           |
- +------------------------------------------------------------------+
- +------------------------------------------------------------------+
