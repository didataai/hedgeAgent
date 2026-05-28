# Strategy Genome — Hedge Evolution Lab

## Conceito

Uma estratégia será representada como um genoma.

O genoma define:

- como entra;
- como calcula net;
- como abre hedge;
- como faz recovery;
- como passa o bastão;
- como controla lote;
- como se protege;
- quando para.

## Estrutura conceitual

```json
{
  "id": "strategy_000001",
  "family": "hybrid",
  "entry": {},
  "hedge": {},
  "recovery": {},
  "baton": {},
  "lot_control": {},
  "protection": {},
  "exit": {}
}
```

## Módulos iniciais

### Entry Module

- `single_direction`
- `hedge_pair`
- `p1_net`
- `residual_cycle`

### Hedge Module

- `fixed_opposite`
- `large_small_alternating`
- `same_plus_opposite`
- `pending_ladder`
- `travamento_pair`

### Recovery Module

- `oldest_loss_best_hedges`
- `biggest_loss_best_profit`
- `basket_profit_covers_loss`
- `residual_plus_hedge_covers_directional`

### Baton Module

- `residual_becomes_center`
- `last_same_becomes_active`
- `reset_cycle`
- `reduce_cycle`
- `stop_after_recovery`

### Lot Control Module

- `fixed`
- `anti_martingale_decrement`
- `reset_after_recovery`
- `gross_limited`
- `volatility_adjusted`

### Protection Module

Parâmetros obrigatórios:

- `max_gross_lots`
- `max_positions`
- `max_levels`
- `max_drawdown_pct`
- `max_margin_usage_pct`
- `spread_limit_pts`
- `cooldown_ticks`
- `recovery_only_after_level`

## Métricas derivadas

Cada genoma deve produzir:

- net lots;
- gross lots;
- oldest loss;
- recovery power;
- risk debt;
- floating profit;
- realized profit;
- max drawdown;
- survival status;
- failure reason.
