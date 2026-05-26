# Análise MQL5 — P0_BASE

## Objetivo deste relatório

Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.

## Fonte

- Família: `P0`
- Versão: `P0_BASE`
- Arquivo: `hedge_P0-NaoAmentaLot.mq5`
- Linhas: `420`
- Gerado em UTC: `2026-05-26T18:57:51.617091+00:00`

## Properties

- Linha 5: `copyright` = `"xAI"`
- Linha 6: `link` = `""`
- Linha 7: `version` = `"1.10"`
- Linha 8: `strict` = ``
- Linha 9: `description` = `"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida"`

## Includes

- Linha 11: `<Trade\Trade.mqh>`

## Inputs detectados

| linha | tipo | nome | default | comentário |
|---:|---|---|---|---|
| 16 | `double` | `HedgeSmallLot` | `0.03` | Lote inicial small hedge |
| 17 | `double` | `HedgeLargeLot` | `0.04` | Lote inicial large hedge |
| 18 | `double` | `DirectionalLot` | `0.02` | Lote direcional fixo |
| 19 | `double` | `LotIncrease` | `0.01` | Incremento por nível |
| 20 | `double` | `StopThresholdUSD` | `-8.0` | Limite USD para stop (net small + directional) |
| 21 | `string` | `TriggerMode` | `"usd"` | "pts" ou "usd" |
| 22 | `double` | `TriggerValue` | `10.0` | Valor do trigger (pts ou net USD) |
| 23 | `int` | `MagicBase` | `12345` | Magic base |
| 24 | `double` | `MaxSpread` | `50.0` | Spread max em points (0 = sem filtro) |
| 25 | `bool` | `IgnoreSpreadOnReset` | `true` | Ignora spread após reset ou botão |
| 26 | `bool` | `ForceInitialHedge` | `false` | Força abertura mesmo com posições |
| 27 | `bool` | `ResetStateOnStart` | `false` | RESET ao iniciar (use 1x) |
| 30 | `string` | `BotaoCloseReset` | `"Close_All_Reset"` |  |
| 31 | `int` | `BotaoPosX` | `30` |  |
| 32 | `int` | `BotaoPosY` | `30` |  |
| 33 | `int` | `BotaoLargura` | `160` |  |
| 34 | `int` | `BotaoAltura` | `40` |  |
| 35 | `color` | `CorBotao` | `clrRed` |  |
| 36 | `color` | `CorTextoBotao` | `clrWhite` |  |

## Funções detectadas

| linha | função | retorno | evento MQL5 |
|---:|---|---|---|
| 60 | `PositionExists` | `bool` | não |
| 62 | `GetProfit` | `double` | não |
| 67 | `GetPointsProfit` | `double` | não |
| 75 | `IsTriggered` | `bool` | não |
| 89 | `OpenPosition` | `ulong` | não |
| 144 | `ClosePosition` | `bool` | não |
| 155 | `CountOurPositions` | `int` | não |
| 166 | `CloseAllOurPositionsAndReset` | `void` | não |
| 208 | `OnInit` | `int` | sim |
| 271 | `OnChartEvent` | `void` | sim |
| 282 | `OnTick` | `void` | sim |
| 417 | `OnDeinit` | `void` | sim |

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
- `trade_keyword_hits`: `{'CTrade': 1, 'trade.Buy': 1, 'trade.Sell': 1, 'PositionSelect': 1, 'PositionSelectByTicket': 1, 'PositionsTotal': 3, 'PositionClose': 1}`
- `lot_keyword_hits`: `{'lot': 13, 'Lot': 64, 'lote': 2, 'HedgeSmallLot': 5, 'HedgeLargeLot': 5, 'DirectionalLot': 3, 'LotIncrease': 2}`
- `hedge_keyword_hits`: `{'hedge': 8, 'Hedge': 17, 'small': 16, 'Small': 67, 'large': 16, 'Large': 69, 'directional': 6, 'Directional': 18, 'direcional': 1, 'isolating': 7, 'Isolating': 2, 'base': 1, 'Base': 11}`
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
- |                    HedgeEA_Progressivo_v110.mq5                  |
- |                          xAI - Hedge Progressivo v1.10           |
- +------------------------------------------------------------------+
- --- Inputs ---
- Lote inicial small hedge
- Lote inicial large hedge
- Lote direcional fixo
- Incremento por nível
- Limite USD para stop (net small + directional)
- "pts" ou "usd"
- Valor do trigger (pts ou net USD)
- Magic base
- Spread max em points (0 = sem filtro)
- Ignora spread após reset ou botão
- Força abertura mesmo com posições
- RESET ao iniciar (use 1x)
- --- Botão ---
- --- Magics ---
- --- Globais persistentes ---
- --- Funções auxiliares ---
- +------------------------------------------------------------------+
- | Expert initialization                                            |
- +------------------------------------------------------------------+
- Força recarga se globals estiverem zeradas
- Botão
- +------------------------------------------------------------------+
- | Chart Event                                                      |
- +------------------------------------------------------------------+
- +------------------------------------------------------------------+
- | Expert tick function                                             |
- +------------------------------------------------------------------+
- Força lotes mínimos se globais zeradas
- Abrir hedges iniciais
- Trigger eliminação
- Stop + sequência
- OnDeinit
