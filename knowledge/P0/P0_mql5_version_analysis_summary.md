# Resumo de Análise MQL5 — Família P0

## Objetivo

Este relatório consolida a leitura automática das versões MQL5 da família. Ele serve como base para documentação, comparação e futura tradução para Python/backtest.

## Versões analisadas

| versão | arquivo | inputs | funções | eventos | resolução por fontes |
|---|---|---:|---:|---|---|
| P0_BASE | `hedge_P0-NaoAmentaLot.mq5` | 19 | 12 | OnInit, OnChartEvent, OnTick, OnDeinit | sim |
| P0_V1 | `Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5` | 28 | 23 | OnInit, OnDeinit, OnTimer, OnChartEvent, OnTick | sim |
| P0_V2 | `Hedge_P0_V2-RangeAumentoLot-NaoFunciona2EAS.mq5` | 21 | 12 | OnInit, OnChartEvent, OnTick, OnDeinit | sim |
| P0_V3 | `Hedge_P0_V3.mq5` | 30 | 13 | OnInit, OnChartEvent, OnTick, OnDeinit | sim |
| P0_V4 | `Hedge_P0_V4.mq5` | 29 | 13 | OnInit, OnChartEvent, OnTick, OnDeinit | sim |

## Leituras importantes

- Esta etapa ainda não interpreta matematicamente a estratégia; ela organiza sinais do código.
- A próxima etapa deve comparar as regras entre versões e montar uma especificação `strategy_spec.json` por versão.
- Qualquer ponto marcado como resolução por fontes precisa ser validado antes do backtest.
