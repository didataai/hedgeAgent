# MQL5 -> Python Block Translation Report — P0 / P0_V4

## Status

- Gerado UTC: `2026-05-27T21:25:41.270735+00:00`
- Source MQL5: `estrategias\P0\Hedge_P0_V4.mq5`
- LLM usada: `False`
- Translation source: `deterministic_block_scaffold_after_llm_error`
- Compilou: `True`
- Smoke test OK: `True`
- Funções selecionadas: `['OnInit', 'OnDeinit', 'OnTick', 'OnChartEvent', 'OpenPosition', 'ClosePosition', 'CloseAllOurPositionsAndReset', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'PositionExists', 'AtualizarResumoNoGrafico', 'PositionGetDouble']`

## Runtime LLM

```json
{
  "used": false,
  "provider": "ollama",
  "active_profile": "local_ollama_qwen25_7b",
  "model": "qwen2.5:7b-instruct",
  "base_url": "http://localhost:11434",
  "timeout_seconds": 300,
  "translation_source": "deterministic_block_scaffold_after_llm_error",
  "error": "Expecting property name enclosed in double quotes: line 2 column 5 (char 6)"
}
```

## Summary

- Scaffold determinístico gerado em modo block-first.
- LLM não usada ou retorno da LLM não foi aceito pelo schema.

## Source unresolved

- Resolver lógica real a partir dos blocos MQL5 selecionados.
- Confirmar sequência de abertura/fechamento, triggers e recovery.

## Validation

```json
{
  "compiled": true,
  "has_strategy_model": true,
  "required_methods": {
    "__init__": true,
    "on_start": true,
    "on_bar": true,
    "get_positions": true,
    "get_events": true,
    "get_metrics_snapshot": true
  },
  "smoke_test_ok": true,
  "errors": [],
  "positions_count": 3,
  "events_count": 3,
  "metrics_snapshot": {
    "family_id": "P0",
    "version_id": "P0_V4",
    "state": "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL",
    "positions_count": 3,
    "gross_lot": 0.09000000000000001,
    "net_lot": 0.010000000000000002,
    "realized_pnl": 4.0,
    "events_count": 3,
    "model_status": "deterministic_block_scaffold_with_source_unresolved"
  }
}
```
