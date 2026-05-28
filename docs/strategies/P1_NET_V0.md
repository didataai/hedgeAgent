# P1_NET_V0 — Strategy Card

## 1. Identity

```yaml
strategy_id: P1_NET_V0
strategy_family: P1_NET
strategy_version: V0
status: experimental
project: Hedge Evolution Lab
primary_goal: controlled net-reversal hedge simulation
dataset_contract: strategy_dataset_contract.v0
```

## 2. Purpose

P1_NET_V0 is an experimental hedge strategy designed to study controlled net exposure reversals.

The strategy keeps the portfolio around a fixed absolute net exposure:

```text
net_lots = buy_lots - sell_lots
target_abs_net = net_abs_lots
```

The strategy alternates between:

```text
+net_abs_lots
-net_abs_lots
```

This means it does not attempt to remain perfectly neutral. It intentionally keeps a small directional net exposure while using opposite-side additions to flip the net when price moves by a configured range.

## 3. Operational Logic

### 3.1 Initial state

The strategy starts by opening one market position in the configured initial direction:

```text
initial_side = BUY or SELL
start_lot = net_abs_lots
```

In the current strategy contract, `start_lot` should match `net_abs_lots`.

Example:

```text
initial_side = SELL
net_abs_lots = 0.01

Initial position:
SELL 0.01
Current net = -0.01
```

### 3.2 Rebalance trigger

The strategy stores a `last_level` price.

If current net is positive and price falls by `range_points`, the strategy opens SELL volume to flip net from positive to negative.

If current net is negative and price rises by `range_points`, the strategy opens BUY volume to flip net from negative to positive.

Conceptually:

```text
If net >= +target and price <= last_level - range:
    open SELL enough to reach -target

If net <= -target and price >= last_level + range:
    open BUY enough to reach +target
```

### 3.3 Net flip calculation

To flip from positive net to negative net:

```text
required_sell = current_net + target_abs_net
```

To flip from negative net to positive net:

```text
required_buy = target_abs_net - current_net
```

Example:

```text
Current net = +0.01
Target net = -0.01
Required SELL = 0.02
```

After opening SELL 0.02:

```text
new net = +0.01 - 0.02 = -0.01
```

## 4. Parameters

| Parameter | Meaning |
|---|---|
| `initial_side` | Initial market direction, BUY or SELL |
| `net_abs_lots` | Desired absolute net exposure |
| `range_points` | Price movement required to trigger a net flip |
| `enable_protection` | Enables strategy-level protection before opening new orders |
| `max_gross_to_net_ratio` | Blocks new order if projected gross/net ratio is too high |
| `max_strategy_gross_lots` | Optional cap for projected gross lots |
| `max_strategy_positions` | Optional cap for projected open positions |

## 5. State Variables

| State | Meaning |
|---|---|
| `started` | Whether initial position was opened |
| `last_level` | Price level used as current rebalance anchor |
| `rebalance_count` | Number of completed net flips |
| `protection_block_count` | Number of times protection blocked a planned order |
| `last_action` | Last strategy action |
| `last_protection_reason` | Reason for the last protection block |

## 6. Protection Logic

The protection layer evaluates the projected portfolio after a planned order.

It can block orders when:

```text
projected_gross_to_net_ratio >= max_gross_to_net_ratio
projected_gross_lots > max_strategy_gross_lots
projected_position_count > max_strategy_positions
```

This was added because the raw P1-Net logic can grow gross exposure during alternating movement.

## 7. Known Strengths

P1_NET_V0 is useful for studying:

```text
controlled net exposure
gross exposure growth
impact of protection rules
range-vs-trend behavior
synthetic Monte Carlo validation
genetic parameter discovery
regime-aware scoring
```

Observed strengths in early synthetic tests:

```text
protection reduces gross exposure
protection reduces position count
protection reduces drawdown in whipsaw/random cases
strategy remains simple and measurable
```

## 8. Known Weaknesses

P1_NET_V0 is not a complete production strategy.

Known risks:

```text
gross exposure can grow without protection
risk debt remains in directional movement
strategy can become too inactive if protection is too restrictive
large range_points may reduce trading activity too much
small range_points may increase gross and position count
performance can vary by regime
```

## 9. Regime Interpretation

The strategy must be evaluated separately across regimes:

```text
random_walk
range_noise
trend_up
trend_down
spike_return
spike_no_return
whipsaw
volatility_expansion
```

A good aggregate score is not enough. The strategy must avoid being strong in only one regime and weak in another.

## 10. Dataset Contract

Strategy datasets must be stored using:

```text
datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/
```

For this strategy:

```text
datasets/strategies/P1_NET_V0/SYNTH/SIM/monte_carlo/...
datasets/strategies/P1_NET_V0/SYNTH/SIM/genetic_search/...
```

## 11. Dynamic Learning Memory

The stable conceptual document is this file.

Dynamic empirical learning should be generated under:

```text
datasets/strategies/P1_NET_V0/_memory/strategy_learning_summary.json
datasets/strategies/P1_NET_V0/_memory/strategy_learning_summary.md
```

Those files should be generated from completed Monte Carlo, walk-forward, back-forward and genetic search runs.

## 12. Agent and RAG Usage

Agents and RAG systems should use this Strategy Card to understand:

```text
what the strategy is
how the strategy operates
what parameters matter
what risks are known
where to find the empirical datasets
how to compare this strategy against other strategies
```

The dynamic learning memory should be used to understand:

```text
what tests were already run
what the best known genome is
which regimes are strongest
which regimes are weakest
which risks appeared empirically
what experiments should be run next
```

## 13. Open Questions

Important future experiments:

```text
Compare P1_NET_V0 against P1_MULTIPLIER_V0.
Test historical GOLD data by timeframe.
Add spread/slippage stress.
Add margin usage simulation.
Add close/recovery logic instead of only opening rebalances.
Test adaptive range_points by volatility.
Test regime-specific parameter sets.
```
