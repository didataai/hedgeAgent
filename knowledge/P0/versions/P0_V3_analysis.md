# Análise MQL5 — P0_V3

## Objetivo deste relatório

Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.

## Fonte

- Família: `P0`
- Versão: `P0_V3`
- Arquivo: `Hedge_P0_V3.mq5`
- Linhas: `542`
- Gerado em UTC: `2026-05-27T19:52:03.859999+00:00`

## Properties

- Linha 5: `copyright` = `"xAI"`
- Linha 6: `link` = `""`
- Linha 7: `version` = `"1.16"`
- Linha 8: `strict` = ``
- Linha 9: `description` = `"Hedge Progressivo - Correção tracking/sequência após aumento de lot"`

## Includes

- Linha 11: `<Trade\Trade.mqh>`

## Inputs detectados

| linha | tipo | nome | default | comentário |
|---:|---|---|---|---|
| 16 | `double` | `HedgeSmallLot` | `0.03` | Lote inicial small hedge |
| 17 | `double` | `HedgeLargeLot` | `0.04` | Lote inicial large hedge |
| 18 | `double` | `LotIncrease` | `0.01` | Incremento normal por nível |
| 19 | `double` | `ExtraLotIncreaseOnRange` | `0.01` | Extra se range > threshold |
| 20 | `int` | `RangeThresholdPts` | `400` | Range em pts para extra increase |
| 21 | `double` | `DirectionalLot` | `0.02` | Lote direcional FIXO (se preferir dinâmico, altere no código) |
| 22 | `double` | `StopThresholdUSD` | `-8.0` | Limite USD para stop (net small + directional) |
| 23 | `string` | `TriggerMode` | `"usd"` | "pts" ou "usd" |
| 24 | `double` | `TriggerValue` | `10.0` | Valor do trigger (pts ou net USD) |
| 25 | `int` | `MagicBase` | `12345` | Magic base (mude para cada instância!) |
| 26 | `string` | `EA_InstanceSuffix` | `"p0-1"` | Sufixo único no INÍCIO dos comentários |
| 27 | `double` | `MaxSpread` | `50.0` | Spread max em points |
| 28 | `bool` | `IgnoreSpreadOnReset` | `true` | Ignora spread após reset ou botão |
| 29 | `bool` | `ForceInitialHedge` | `false` | Força abertura mesmo com posições |
| 30 | `bool` | `ResetStateOnStart` | `false` | RESET ao iniciar |
| 33 | `color` | `CorBuy` | `clrGreen` |  |
| 34 | `color` | `CorSell` | `clrRed` |  |
| 35 | `color` | `CorNet` | `clrBlueViolet` |  |
| 36 | `color` | `CorLucro` | `clrBlue` |  |
| 37 | `int` | `TamanhoFonte` | `12` |  |
| 38 | `int` | `PosX` | `90` |  |
| 39 | `int` | `PosY` | `20` |  |
| 40 | `int` | `Espacamento` | `18` |  |
| 43 | `string` | `BotaoCloseReset` | `"Close_All_Reset"` |  |
| 44 | `int` | `BotaoPosX` | `20` |  |
| 45 | `int` | `BotaoPosY` | `20` |  |
| 46 | `int` | `BotaoLargura` | `140` |  |
| 47 | `int` | `BotaoAltura` | `30` |  |
| 48 | `color` | `CorBotao` | `clrRed` |  |
| 49 | `color` | `CorTextoBotao` | `clrWhite` |  |

## Funções detectadas

| linha | função | retorno | evento MQL5 |
|---:|---|---|---|
| 84 | `PositionExists` | `bool` | não |
| 86 | `GetProfit` | `double` | não |
| 91 | `GetPointsProfit` | `double` | não |
| 99 | `IsTriggered` | `bool` | não |
| 118 | `OpenPosition` | `ulong` | não |
| 174 | `ClosePosition` | `bool` | não |
| 185 | `CountOurPositions` | `int` | não |
| 196 | `AtualizarResumoNoGrafico` | `void` | não |
| 226 | `CloseAllOurPositionsAndReset` | `void` | não |
| 265 | `OnInit` | `int` | sim |
| 361 | `OnChartEvent` | `void` | sim |
| 372 | `OnTick` | `void` | sim |
| 534 | `OnDeinit` | `void` | sim |

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
- `lot_keyword_hits`: `{'lot': 15, 'Lot': 34, 'lote': 1, 'HedgeSmallLot': 6, 'HedgeLargeLot': 9, 'DirectionalLot': 3, 'LotIncrease': 4}`
- `hedge_keyword_hits`: `{'hedge': 5, 'Hedge': 28, 'small': 19, 'Small': 53, 'large': 21, 'Large': 54, 'directional': 10, 'Directional': 19, 'direcional': 1, 'isolating': 7, 'Isolating': 1, 'base': 4, 'Base': 17}`
- `risk_keyword_hits`: `{'StopThreshold': 3, 'MaxSpread': 4, 'DD': 1, 'stop': 1, 'Stop': 5, 'margin': 6}`

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
- |                    HedgeEA_Progressivo_v116.mq5                  |
- |                          xAI - Hedge Progressivo v1.16           |
- +------------------------------------------------------------------+
- --- Inputs ---
- Lote inicial small hedge
- Lote inicial large hedge
- Incremento normal por nível
- Extra se range > threshold
- Range em pts para extra increase
- Lote direcional FIXO (se preferir dinâmico, altere no código)
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
- --- Variáveis de lotes (sempre dos inputs) ---
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
- Inicialização
