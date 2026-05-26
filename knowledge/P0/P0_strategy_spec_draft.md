# Strategy Spec Draft — P0

## Status

- Artefato: `strategy_spec_draft`
- Schema: `0.1`
- Status: `draft_needs_source_resolution`
- Gerado em UTC: `2026-05-26T21:11:42.404748+00:00`

## Tese

Família P0 tenta transformar um hedge inicial em ciclos de eliminação, exposição direcional controlada e recovery/neutralização.

## Pistas numéricas

- Lotes: `['0.01', '0.02', '0.03', '0.04', '0.05', '0.06']`
- Preços/pontos: `['3000', '3500', '500']`
- Valores USD: `['-8USD', '10usd']`

## Entidades

### small_hedge
- Papel: ordem/lote menor usado como parte do travamento inicial ou base de neutralização
- Evidência: Prompt humano menciona lote 0.03; códigos progressivos usam HedgeSmallLot quando presente.
- Confiança: `medium`

### large_hedge
- Papel: ordem/lote maior usado para eliminar a ordem menor perdedora quando houver lucro suficiente
- Evidência: Prompt humano menciona lote 0.04; códigos progressivos usam HedgeLargeLot quando presente.
- Confiança: `medium`

### directional_order
- Papel: ordem direcional aberta após eliminação parcial para criar exposição líquida controlada
- Evidência: Prompt humano menciona lote 0.02; várias versões têm pista de directional.
- Confiança: `medium`

### recovery_or_stop_pair
- Papel: combinação de lucro da ordem remanescente com stop/prejuízo da direcional para tentar fechar perto de zero
- Evidência: Prompt humano cita retorno do preço e diferença próxima de -8USD.
- Confiança: `medium`

### next_cycle_hedge
- Papel: novo par de hedge com incremento de lote após uma eliminação/recovery
- Evidência: Prompt humano cita compra/venda 0.05 após incremento 0.01; versões progressivas têm pista de LotIncrease.
- Confiança: `medium`

## Estados operacionais

- `S0_EMPTY_OR_RESET`: Nenhuma estrutura ativa da família ou estado resetado. Entrada: EA iniciado, resetado ou sem posições controladas pela instância.
- `S1_INITIAL_MARKET_HEDGE`: Travamento inicial a mercado com pares small/large BUY+SELL. Entrada: AutoStart/ForceInitialHedge ou condição inicial validada.
- `S2_RANGE_TRIGGER_REACHED`: Preço andou range/trigger suficiente para uma ordem maior lucrativa eliminar uma menor perdedora. Entrada: Trigger por pontos ou USD conforme configuração.
- `S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL`: Fecha par vencedor/perdedor e abre ordem direcional de exposição líquida controlada. Entrada: Eliminação validada e ordem direcional permitida.
- `S4_RETURN_STOP_OR_RECOVERY`: Preço retorna contra a direcional e tenta neutralizar stop/prejuízo com ordem remanescente. Entrada: Diferença/lucro combinado atinge threshold de stop/recovery.
- `S5_NEXT_CYCLE_REBUILD`: Recria/continua a estrutura com novo hedge, possivelmente com incremento de lote. Entrada: Recovery/eliminação concluída e próximo ciclo permitido.

## Transições candidatas

### S0_EMPTY_OR_RESET -> S1_INITIAL_MARKET_HEDGE
- Evento: `start_or_reset`
- Regra draft: Abrir BUY e SELL para small_hedge e BUY e SELL para large_hedge, se permitido.
- Evidência: Prompt humano descreve início com 4 ordens: compra/venda 0.03 e compra/venda 0.04.
- Confiança: `medium`

### S1_INITIAL_MARKET_HEDGE -> S2_RANGE_TRIGGER_REACHED
- Evento: `range_or_profit_trigger`
- Regra draft: Aguardar range em pontos ou lucro configurado para permitir eliminação entre large e small.
- Evidência: Prompt humano cita range 500 pts e trigger por 20 pts ou 10 USD.
- Confiança: `medium`

### S2_RANGE_TRIGGER_REACHED -> S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL
- Evento: `winner_eliminates_loser`
- Regra draft: Usar ordem large lucrativa para eliminar ordem small perdedora e abrir direcional.
- Evidência: Prompt humano descreve buy 0.04 eliminando sell 0.03 e depois buy 0.02.
- Confiança: `medium`

### S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL -> S4_RETURN_STOP_OR_RECOVERY
- Evento: `price_returns_against_directional`
- Regra draft: Usar lucro da ordem remanescente para fechar a direcional com resultado próximo de zero ou threshold configurado.
- Evidência: Prompt humano cita lucro da 0.03 + stop da 0.02 próximo de 0 ou -8 USD.
- Confiança: `medium`

### S4_RETURN_STOP_OR_RECOVERY -> S5_NEXT_CYCLE_REBUILD
- Evento: `recovery_completed`
- Regra draft: Abrir/reconstruir novo hedge, possivelmente com incremento de lote, e continuar ciclo.
- Evidência: Prompt humano cita novo hedge 0.05 e continuidade da lógica.
- Confiança: `medium`

## Sublinha(s)

- `progressive_hedge_or_lot_increase`: `P0_BASE`, `P0_V2`, `P0_V3`, `P0_V4`
- `pending_recovery_or_initial_lock`: `P0_V1`
- `spread_magic_operational_control`: `P0_BASE`, `P0_V1`, `P0_V2`, `P0_V3`, `P0_V4`

## Versões

### P0_BASE — `hedge_P0-NaoAmentaLot.mq5`
- Descrição: "Hedge Progressivo - Correção lotes globais não carregados + sequência garantida"
- Sublinha(s): `['progressive_hedge_or_lot_increase', 'spread_magic_operational_control']`
- Mecanismos: `['initial_hedge_or_small_large_structure', 'directional_order_or_directional_exposure', 'lot_increase_or_progressive_lot', 'spread_filter', 'magic_or_instance_separation']`
- Status resolução: `unresolved_from_sources`
- Precisa resolver em fonte: `True`
- Parâmetros candidatos:
  - `HedgeSmallLot` = `0.03` (double)
  - `HedgeLargeLot` = `0.04` (double)
  - `DirectionalLot` = `0.02` (double)
  - `LotIncrease` = `0.01` (double)
  - `StopThresholdUSD` = `-8.0` (double)
  - `TriggerMode` = `"usd"` (string)
  - `TriggerValue` = `10.0` (double)
  - `MaxSpread` = `50.0` (double)
  - `MagicBase` = `12345` (int)

### P0_V1 — `Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5`
- Descrição: "Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."
- Sublinha(s): `['pending_recovery_or_initial_lock', 'spread_magic_operational_control']`
- Mecanismos: `['directional_order_or_directional_exposure', 'pending_orders', 'recovery_or_resolution_logic', 'magic_or_instance_separation']`
- Status resolução: `unresolved_from_sources`
- Precisa resolver em fonte: `True`
- Parâmetros candidatos:
  - `RangePts` = `300` (int)
  - `MagicNumber` = `20260206` (ulong)

### P0_V2 — `Hedge_P0_V2-RangeAumentoLot-NaoFunciona2EAS.mq5`
- Descrição: "Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"
- Sublinha(s): `['progressive_hedge_or_lot_increase', 'spread_magic_operational_control']`
- Mecanismos: `['initial_hedge_or_small_large_structure', 'directional_order_or_directional_exposure', 'lot_increase_or_progressive_lot', 'spread_filter', 'magic_or_instance_separation']`
- Status resolução: `unresolved_from_sources`
- Precisa resolver em fonte: `True`
- Parâmetros candidatos:
  - `HedgeSmallLot` = `0.03` (double)
  - `HedgeLargeLot` = `0.04` (double)
  - `DirectionalLot` = `0.02` (double)
  - `LotIncrease` = `0.01` (double)
  - `ExtraLotWhenFar` = `0.01` (double)
  - `FarRangePts` = `400` (int)
  - `StopThresholdUSD` = `-8.0` (double)
  - `TriggerMode` = `"usd"` (string)
  - `TriggerValue` = `10.0` (double)
  - `MaxSpread` = `50.0` (double)
  - `MagicBase` = `12345` (int)

### P0_V3 — `Hedge_P0_V3.mq5`
- Descrição: "Hedge Progressivo - Correção tracking/sequência após aumento de lot"
- Sublinha(s): `['progressive_hedge_or_lot_increase', 'spread_magic_operational_control']`
- Mecanismos: `['initial_hedge_or_small_large_structure', 'directional_order_or_directional_exposure', 'lot_increase_or_progressive_lot', 'spread_filter', 'magic_or_instance_separation']`
- Status resolução: `unresolved_from_sources`
- Precisa resolver em fonte: `True`
- Parâmetros candidatos:
  - `HedgeSmallLot` = `0.03` (double)
  - `HedgeLargeLot` = `0.04` (double)
  - `DirectionalLot` = `0.02` (double)
  - `LotIncrease` = `0.01` (double)
  - `ExtraLotIncreaseOnRange` = `0.01` (double)
  - `RangeThresholdPts` = `400` (int)
  - `StopThresholdUSD` = `-8.0` (double)
  - `TriggerMode` = `"usd"` (string)
  - `TriggerValue` = `10.0` (double)
  - `MaxSpread` = `50.0` (double)
  - `MagicBase` = `12345` (int)
  - `EA_InstanceSuffix` = `"p0-1"` (string)

### P0_V4 — `Hedge_P0_V4.mq5`
- Descrição: "Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"
- Sublinha(s): `['progressive_hedge_or_lot_increase', 'spread_magic_operational_control']`
- Mecanismos: `['initial_hedge_or_small_large_structure', 'directional_order_or_directional_exposure', 'lot_increase_or_progressive_lot', 'spread_filter', 'magic_or_instance_separation']`
- Status resolução: `unresolved_from_sources`
- Precisa resolver em fonte: `True`
- Parâmetros candidatos:
  - `HedgeSmallLot` = `0.03` (double)
  - `HedgeLargeLot` = `0.04` (double)
  - `LotIncrease` = `0.01` (double)
  - `ExtraLotIncreaseOnRange` = `0.01` (double)
  - `RangeThresholdPts` = `400` (int)
  - `StopThresholdUSD` = `-8.0` (double)
  - `TriggerMode` = `"usd"` (string)
  - `TriggerValue` = `10.0` (double)
  - `MaxSpread` = `50.0` (double)
  - `MagicBase` = `12345` (int)
  - `EA_InstanceSuffix` = `"p0-1"` (string)

## Limitações conhecidas

- P0_BASE: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V1: Não foi detectada pista clara de filtro de spread nesta análise textual.
- P0_V2: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V3: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.
- P0_V4: Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida.

## Pontos pendentes / resolução por fontes

- A intenção menciona dúvida entre executar a mercado ou usar limits; isso precisa virar regra formal.
- Ainda é necessário transformar a intenção em uma especificação de estados, transições e eventos testáveis.
- Backtest ainda não foi executado; a robustez em tendência, range e zig-zag é desconhecida.
- Definir como separar ordens de hedge inicial, hedge de ciclo, direcional e isolating por magic/comment.
- Definir fórmula exata para saber quando large elimina small em pontos, USD ou lucro líquido combinado.
- Definir limite de incremento de lote, DD máximo, margem mínima e parada de segurança.
- Definir se ordens de reconstrução serão a mercado, limit ou stop em cada transição.
- Validar se P0_V1 é sublinha separada ou deve ser fundida com o hedge progressivo em uma P0 futura.

## Requisitos de validação e backtesting

- Converter a lógica operacional MQL5 para um modelo Python rastreável antes do backtest.
- Teste sintético com trend up, trend down, range, zig-zag, spike up e spike down.
- Backtest histórico com separação clara entre treino, validação e teste.
- Walk-forward/back-forward por janelas para medir estabilidade temporal da lógica.
- Monte Carlo sobre sequência de trades/ciclos, slippage, spread, gaps e ordem dos eventos.
- Medição de DD, margem, exposição líquida, número máximo de posições, pior ciclo e tempo preso em hedge.
- Medição do range necessário para zerar, recuperar e fechar positivo por ciclo hedge.
- Comparação de duas ou mais janelas independentes, inclusive janela A contra janela B e inverso.
- Teste por subfamília: progressive_hedge_or_lot_increase versus pending_recovery_or_initial_lock.
- Otimização paramétrica com limites de risco para lotes, ranges, stops, triggers e incrementos.
- Ranking de candidatos por lucro, DD, margem, lote máximo, robustez temporal e sobrevivência Monte Carlo.
- Gerar datasets de eventos/ciclos para alimentar a próxima inteligência evolutiva.
- Garantir compatibilidade multiativo, multitimeframe, Windows e Linux no simulador futuro.

## Protocolo de resolução por fontes

- Required: `True`
- Significado: Campos pendentes devem ser resolvidos primeiro por leitura das fontes reais, especialmente MQL5, prompts e artefatos de análise. Só permanecem unresolved_from_sources quando nenhuma fonte prova a regra.
- Ordem de resolução:
  - MQL5 source file
  - version analysis JSON
  - Prompt/notas da estratégia
  - strategy brain/evolution map
  - unresolved_from_sources

## Próxima fase planejada

- Fase: `mql5_to_python_backtesting_lab`
- Status: `planned_after_mapping`
- Timeframes suportados planejados: `['M5', 'M15', 'H1', 'H4', 'D1']`
- Escopo:
  - converter lógica operacional MQL5 para Python
  - criar simulador/backtester mínimo
  - rodar cenários sintéticos controlados
  - rodar backtest histórico
  - executar walk-forward/back-forward
  - executar Monte Carlo
  - executar otimização paramétrica controlada
  - gerar ranking de melhores configurações por perfil de risco
  - gerar métricas, eventos, curvas e datasets para evolução
- Métricas específicas para hedge:
  - `max_floating_dd_usd`
  - `max_floating_dd_points`
  - `dd_by_cycle`
  - `margin_used_max`
  - `net_exposure_lots`
  - `gross_exposure_lots`
  - `max_lot_reached`
  - `cycle_count`
  - `time_locked_bars`
  - `range_to_breakeven_points`
  - `range_to_positive_close_points`
  - `range_to_recovery_points`
  - `worst_adverse_excursion_points`
  - `best_favorable_excursion_points`
  - `recovery_success_rate`
  - `forced_stop_count`
- Plano de otimização paramétrica:
  - Enabled phase 2: `True`
  - Objetivo: Gerar conhecimento sobre sensibilidade da estratégia e encontrar configurações candidatas mais robustas, sem confundir otimização com prova de robustez.
  - Parâmetros candidatos:
    - `HedgeSmallLot`
    - `HedgeLargeLot`
    - `DirectionalLot`
    - `LotIncrease`
    - `ExtraLotIncreaseOnRange`
    - `RangePts`
    - `RangeThresholdPts`
    - `TriggerMode`
    - `TriggerValue`
    - `StopThresholdUSD`
    - `MaxSpread`
    - `max_cycles`
    - `max_total_lot`
    - `pending_vs_market_policy`
  - Métodos iniciais:
    - `grid_search_small`
    - `random_search_bounded`
    - `walk_forward_selection`
    - `monte_carlo_robustness_filter`
  - Perfis de ranking:
    - `best_overall`
    - `safest_low_dd`
    - `fastest_recovery`
    - `lowest_margin_usage`
    - `best_monte_carlo_survival`
    - `aggressive_high_return`
  - Guardrails:
    - não aceitar candidato apenas por lucro final
    - penalizar DD flutuante alto
    - penalizar aumento excessivo de lote
    - penalizar margem alta
    - penalizar tempo travado em hedge
    - penalizar diferença grande entre janela de otimização e validação
- Nota evolução: Deep learning, otimização evolutiva e mutação de regras pertencem à fase posterior de evolução, usando os dados gerados pelo backtesting, otimização paramétrica, walk-forward/back-forward e Monte Carlo.

## Runtime LLM usado no brain

```json
{
  "used": false,
  "provider": "ollama",
  "active_profile": "local_ollama_qwen25_7b",
  "model": "qwen2.5:7b-instruct",
  "base_url": "http://localhost:11434",
  "temperature": 0.2,
  "top_p": 0.9,
  "timeout_seconds": 120,
  "max_context_chars": 60000,
  "source": "deterministic_fallback_after_llm_error",
  "error": "timed out"
}
```
