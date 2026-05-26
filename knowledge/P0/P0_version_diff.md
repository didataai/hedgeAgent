# Diff Evolutivo — Família P0

## Objetivo

Este relatório compara as versões MQL5 analisadas pelo mesmo script `analyze_mql5_version.py`. Ele evita criar outro script só para comparação e mantém a base de conhecimento da família em uma etapa única.

A comparação é objetiva: inputs, defaults, funções, eventos e pistas de lógica. Ela ainda não substitui backtest.

## Ordem das versões

- `P0_BASE`
- `P0_V1`
- `P0_V2`
- `P0_V3`
- `P0_V4`

## Matriz de pistas principais

| pista | P0_BASE | P0_V1 | P0_V2 | P0_V3 | P0_V4 |
|---|---|---|---|---|---|
| has_magic_number | True | True | True | True | True |
| has_spread_filter | True | False | True | True | True |
| has_initial_hedge_cue | True | False | True | True | True |
| has_directional_cue | True | True | True | True | True |
| has_lot_increase_cue | True | False | True | True | True |
| has_no_lot_increase_cue | False | False | False | False | False |
| has_pending_order_cue | False | True | False | False | False |
| has_recovery_cue | False | True | False | False | False |
| has_timer_event | False | True | False | False | False |
| has_tick_event | True | True | True | True | True |

## Comparação versão a versão

### P0_BASE

Primeira versão da família nesta análise.

Descrição detectada: `"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida"`

**Inputs adicionados:**
- `BotaoAltura`
- `BotaoCloseReset`
- `BotaoLargura`
- `BotaoPosX`
- `BotaoPosY`
- `CorBotao`
- `CorTextoBotao`
- `DirectionalLot`
- `ForceInitialHedge`
- `HedgeLargeLot`
- `HedgeSmallLot`
- `IgnoreSpreadOnReset`
- `LotIncrease`
- `MagicBase`
- `MaxSpread`
- `ResetStateOnStart`
- `StopThresholdUSD`
- `TriggerMode`
- `TriggerValue`

**Inputs removidos:**
- Nenhum.

**Funções adicionadas:**
- `CloseAllOurPositionsAndReset`
- `ClosePosition`
- `CountOurPositions`
- `GetPointsProfit`
- `GetProfit`
- `IsTriggered`
- `OnChartEvent`
- `OnDeinit`
- `OnInit`
- `OnTick`
- `OpenPosition`
- `PositionExists`

**Funções removidas:**
- Nenhum.

**Defaults alterados:**
- Nenhum.

**Riscos candidatos desta versão:**
- (medium) Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

**Pontos que ainda precisam revisão:**
- Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

### P0_V1

Comparada com: `P0_BASE`

Descrição detectada: `"Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."`

**Inputs adicionados:**
- `AutoStart`
- `BotaoCloseAll`
- `BotaoH`
- `BotaoW`
- `CommentText`
- `CooldownMs`
- `CorBuy`
- `CorNet`
- `CorProfit`
- `CorSell`
- `CorTxtBotao`
- `DeviationPts`
- `Esp_UI`
- `FonteUI`
- `HedgeExtraLot`
- `HedgeOffsetPts`
- `MagicNumber`
- `MinLot`
- `PosX_UI`
- `PosY_UI`
- `RangePts`
- `ReturnTolPts`
- `StartLot`
- `StepLot`
- `TimerMs`

**Inputs removidos:**
- `BotaoAltura`
- `BotaoCloseReset`
- `BotaoLargura`
- `CorTextoBotao`
- `DirectionalLot`
- `ForceInitialHedge`
- `HedgeLargeLot`
- `HedgeSmallLot`
- `IgnoreSpreadOnReset`
- `LotIncrease`
- `MagicBase`
- `MaxSpread`
- `ResetStateOnStart`
- `StopThresholdUSD`
- `TriggerMode`
- `TriggerValue`

**Funções adicionadas:**
- `CloseAllByMagic`
- `Cmt`
- `CreateUI`
- `CycleTag`
- `FindTicketByExactComment`
- `IsMyOrderByTicket`
- `IsMyPosByTicket`
- `IsTradeAllowedNow`
- `MyPositionsCount`
- `NormalizeLot`
- `OnTimer`
- `OpenDirAndLockFromBase`
- `OpenStartHedge`
- `Prefix`
- `PrintState`
- `ResolveOnHedgeProfit`
- `TriggerFromInitial`
- `TryTriggerFromSingleBase`
- `UpdateUI`

**Funções removidas:**
- `CloseAllOurPositionsAndReset`
- `ClosePosition`
- `CountOurPositions`
- `GetPointsProfit`
- `GetProfit`
- `IsTriggered`
- `OpenPosition`
- `PositionExists`

**Defaults alterados:**
- `BotaoPosX`: `30` -> `20`
- `BotaoPosY`: `30` -> `20`

**Riscos candidatos desta versão:**
- (low) Não foi detectada pista clara de filtro de spread nesta análise textual.

**Pontos que ainda precisam revisão:**
- Há pistas de ordens pendentes, mas a sequência exata de criação/renovação ainda precisa ser interpretada.
- Há pistas de recovery/resolve, mas a regra matemática de recuperação ainda precisa ser validada.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

### P0_V2

Comparada com: `P0_V1`

Descrição detectada: `"Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"`

**Inputs adicionados:**
- `BotaoAltura`
- `BotaoCloseReset`
- `BotaoLargura`
- `CorTextoBotao`
- `DirectionalLot`
- `ExtraLotWhenFar`
- `FarRangePts`
- `ForceInitialHedge`
- `HedgeLargeLot`
- `HedgeSmallLot`
- `IgnoreSpreadOnReset`
- `LotIncrease`
- `MagicBase`
- `MaxSpread`
- `ResetStateOnStart`
- `StopThresholdUSD`
- `TriggerMode`
- `TriggerValue`

**Inputs removidos:**
- `AutoStart`
- `BotaoCloseAll`
- `BotaoH`
- `BotaoW`
- `CommentText`
- `CooldownMs`
- `CorBuy`
- `CorNet`
- `CorProfit`
- `CorSell`
- `CorTxtBotao`
- `DeviationPts`
- `Esp_UI`
- `FonteUI`
- `HedgeExtraLot`
- `HedgeOffsetPts`
- `MagicNumber`
- `MinLot`
- `PosX_UI`
- `PosY_UI`
- `RangePts`
- `ReturnTolPts`
- `StartLot`
- `StepLot`
- `TimerMs`

**Funções adicionadas:**
- `CloseAllOurPositionsAndReset`
- `ClosePosition`
- `CountOurPositions`
- `GetPointsProfit`
- `GetProfit`
- `IsTriggered`
- `OpenPosition`
- `PositionExists`

**Funções removidas:**
- `CloseAllByMagic`
- `Cmt`
- `CreateUI`
- `CycleTag`
- `FindTicketByExactComment`
- `IsMyOrderByTicket`
- `IsMyPosByTicket`
- `IsTradeAllowedNow`
- `MyPositionsCount`
- `NormalizeLot`
- `OnTimer`
- `OpenDirAndLockFromBase`
- `OpenStartHedge`
- `Prefix`
- `PrintState`
- `ResolveOnHedgeProfit`
- `TriggerFromInitial`
- `TryTriggerFromSingleBase`
- `UpdateUI`

**Defaults alterados:**
- `BotaoPosX`: `20` -> `30`
- `BotaoPosY`: `20` -> `30`

**Riscos candidatos desta versão:**
- (medium) Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

**Pontos que ainda precisam revisão:**
- Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

### P0_V3

Comparada com: `P0_V2`

Descrição detectada: `"Hedge Progressivo - Correção tracking/sequência após aumento de lot"`

**Inputs adicionados:**
- `CorBuy`
- `CorLucro`
- `CorNet`
- `CorSell`
- `EA_InstanceSuffix`
- `Espacamento`
- `ExtraLotIncreaseOnRange`
- `PosX`
- `PosY`
- `RangeThresholdPts`
- `TamanhoFonte`

**Inputs removidos:**
- `ExtraLotWhenFar`
- `FarRangePts`

**Funções adicionadas:**
- `AtualizarResumoNoGrafico`

**Funções removidas:**
- Nenhum.

**Defaults alterados:**
- `BotaoAltura`: `40` -> `30`
- `BotaoLargura`: `160` -> `140`
- `BotaoPosX`: `30` -> `20`
- `BotaoPosY`: `30` -> `20`

**Riscos candidatos desta versão:**
- (medium) Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

**Pontos que ainda precisam revisão:**
- Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

### P0_V4

Comparada com: `P0_V3`

Descrição detectada: `"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"`

**Inputs adicionados:**
- Nenhum.

**Inputs removidos:**
- `DirectionalLot`

**Funções adicionadas:**
- Nenhum.

**Funções removidas:**
- Nenhum.

**Defaults alterados:**
- Nenhum.

**Riscos candidatos desta versão:**
- (medium) Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

**Pontos que ainda precisam revisão:**
- Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.
- Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.

## Próxima etapa sugerida

Usar este diff para escolher uma versão-base e criar `strategy_spec.json` por versão, ainda marcando regras ambíguas como `needs_human_review` antes de qualquer backtest.
