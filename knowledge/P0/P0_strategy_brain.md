# Strategy Brain — P0

## Ideia original detectada

- Família P0: intenção humana extraída de arquivos de notas/contexto.
- Esta leitura é determinística e deve ser validada por resolução por fontes.
- A estratégia parece nascer de um hedge/travamento inicial a mercado.
- Há pistas de dois blocos/lotes principais, especialmente 0.03 e 0.04.
- Há intenção de usar a ordem maior lucrativa para eliminar ordem menor perdedora.
- Após eliminação, há intenção de abrir uma ordem direcional.
- O retorno do preço contra a direcional é tratado como problema central de stop/recovery.
- Há pista de incremento de lote, que precisa ser avaliado por DD, margem e risco.

## Evidências do código

- P0_BASE: property description = "Hedge Progressivo - Correção lotes globais não carregados + sequência garantida"
- P0_BASE: detectados 19 inputs, 12 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].
- P0_V1: property description = "Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."
- P0_V1: detectados 28 inputs, 23 funções e eventos ['OnInit', 'OnDeinit', 'OnTimer', 'OnChartEvent', 'OnTick'].
- P0_V2: property description = "Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"
- P0_V2: detectados 21 inputs, 12 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].
- P0_V3: property description = "Hedge Progressivo - Correção tracking/sequência após aumento de lot"
- P0_V3: detectados 30 inputs, 13 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].
- P0_V4: property description = "Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"
- P0_V4: detectados 29 inputs, 13 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].

## Linha de raciocínio evolutiva

- P0_BASE: versão inicial analisada. Descrição detectada: "Hedge Progressivo - Correção lotes globais não carregados + sequência garantida".
- P0_BASE -> P0_V1; descrição detectada: "Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."; inputs adicionados: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; inputs removidos: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', 'IgnoreSpreadOnReset', 'LotIncrease', '...(+6)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; funções removidas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; mudanças de pistas: ['has_spread_filter: True -> False', 'has_initial_hedge_cue: True -> False', 'has_lot_increase_cue: True -> False', 'has_pending_order_cue: False -> True', 'has_recovery_cue: False -> True', 'has_reset_state_cue: True -> False', 'has_timer_event: False -> True'].
- P0_V1 -> P0_V2; descrição detectada: "Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"; inputs adicionados: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ExtraLotWhenFar', 'FarRangePts', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', '...(+8)']; inputs removidos: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; funções removidas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; mudanças de pistas: ['has_spread_filter: False -> True', 'has_initial_hedge_cue: False -> True', 'has_lot_increase_cue: False -> True', 'has_pending_order_cue: True -> False', 'has_recovery_cue: True -> False', 'has_reset_state_cue: False -> True', 'has_timer_event: True -> False'].
- P0_V2 -> P0_V3; descrição detectada: "Hedge Progressivo - Correção tracking/sequência após aumento de lot"; inputs adicionados: ['CorBuy', 'CorLucro', 'CorNet', 'CorSell', 'EA_InstanceSuffix', 'Espacamento', 'ExtraLotIncreaseOnRange', 'PosX', 'PosY', 'RangeThresholdPts', '...(+1)']; inputs removidos: ['ExtraLotWhenFar', 'FarRangePts']; defaults alterados: ['BotaoAltura', 'BotaoLargura', 'BotaoPosX', 'BotaoPosY']; funções adicionadas: ['AtualizarResumoNoGrafico'].
- P0_V3 -> P0_V4; descrição detectada: "Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"; inputs removidos: ['DirectionalLot'].

## Sublinha(s) detectadas

- `progressive_hedge_or_lot_increase`: `P0_BASE`, `P0_V2`, `P0_V3`, `P0_V4`
- `pending_recovery_or_initial_lock`: `P0_V1`
- `spread_magic_operational_control`: `P0_BASE`, `P0_V1`, `P0_V2`, `P0_V3`, `P0_V4`

## Limitações conhecidas/candidatas

- P0_BASE: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V1: Não foi detectada pista clara de filtro de spread nesta análise textual.
- P0_V2: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V3: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V4: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

## Próximos passos

- Validar a leitura humana da estratégia antes de criar `strategy_spec.json`.
- Formalizar estados, transições, regras de lote, hedge, stop e recovery.
- Só depois executar backtests sintéticos e reais.