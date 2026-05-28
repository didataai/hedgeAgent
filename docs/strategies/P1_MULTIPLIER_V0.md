# P1_MULTIPLIER_V0 — Strategy Card

## 1. Identity

```yaml
strategy_id: P1_MULTIPLIER_V0
strategy_family: P1_MULTIPLIER
strategy_version: V0
status: experimental
project: Hedge Evolution Lab
primary_goal: multiplier-based alternating hedge simulation
dataset_contract: strategy_dataset_contract.v0
```

## 2. Purpose

P1_MULTIPLIER_V0 is an experimental hedge strategy based on the original P1 multiplier idea.

Unlike P1_NET_V0, which tries to keep a fixed absolute net exposure, P1_MULTIPLIER_V0 grows the opposite side by a configured multiplier.

Core idea:

```text
desired_opposite_total = current_reference_side_total × multiplier
```

This can be powerful in range/reversal movement, but it can also expand gross exposure quickly.

## 3. Operational Logic

### 3.1 Initial state

The strategy starts with one market position:

```text
initial_side = BUY or SELL
start_lot = initial lot
```

Example:

```text
initial_side = SELL
start_lot = 0.02
multiplier = 2.0

Initial position:
SELL 0.02
```

### 3.2 First opposite expansion

If price moves against the initial SELL by `range_points`, the strategy opens BUY so that:

```text
total_buy = total_sell × multiplier
```

Example:

```text
SELL total = 0.02
multiplier = 2.0
desired BUY total = 0.04
add BUY = 0.04
```

### 3.3 Alternating multiplier expansion

After opening BUY, the next trigger is a move back by `range_points`.

Then the strategy opens SELL so that:

```text
total_sell = total_buy × multiplier
```

Example:

```text
BUY total = 0.04
desired SELL total = 0.08
current SELL = 0.02
add SELL = 0.06
```

Then it alternates:

```text
BUY side expansion
SELL side expansion
BUY side expansion
SELL side expansion
```

## 4. Parameters

| Parameter | Meaning |
|---|---|
| `initial_side` | Initial market direction, BUY or SELL |
| `start_lot` | Initial order lot |
| `range_points` | Price movement required to trigger the next side |
| `multiplier` | Multiplies opposite/reference side total |
| `enable_protection` | Enables strategy-level protection |
| `max_gross_to_net_ratio` | Blocks new order if projected gross/net ratio is too high |
| `max_strategy_gross_lots` | Optional cap for projected gross lots |
| `max_strategy_positions` | Optional cap for projected open positions |

## 5. State Variables

| State | Meaning |
|---|---|
| `started` | Whether initial position was opened |
| `last_level` | Price level used as current trigger anchor |
| `next_side` | Next side to expand, BUY or SELL |
| `rebalance_count` | Number of multiplier expansions |
| `protection_block_count` | Number of protection blocks |
| `last_action` | Last strategy action |
| `last_protection_reason` | Reason for last protection block |

## 6. Protection Logic

Before opening a planned multiplier expansion, the strategy estimates projected exposure.

It can block orders when:

```text
projected_gross_to_net_ratio >= max_gross_to_net_ratio
projected_gross_lots > max_strategy_gross_lots
projected_position_count > max_strategy_positions
```

Protection is especially important for this strategy because multiplier-based expansion can grow gross exposure much faster than P1_NET_V0.

## 7. Known Strengths

P1_MULTIPLIER_V0 is useful for studying:

```text
aggressive range recovery
multiplier expansion behavior
gross exposure acceleration
protection efficiency
regime sensitivity
comparison against P1_NET_V0
```

Potential strengths:

```text
can recover strongly in oscillating/ranging paths
can create profitable imbalance after reversal
simple and measurable expansion logic
```

## 8. Known Weaknesses

Known risks:

```text
gross lots can expand quickly
position count can increase quickly
risk debt can become large during trends
protection may block too much if multiplier is aggressive
performance can depend heavily on range_points and multiplier
```

## 9. Dataset Contract

Strategy datasets must be stored using:

```text
datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/
```

For this strategy:

```text
datasets/strategies/P1_MULTIPLIER_V0/SYNTH/SIM/monte_carlo/...
datasets/strategies/P1_MULTIPLIER_V0/SYNTH/SIM/genetic_search/...
```

## 10. Dynamic Learning Memory

Dynamic empirical learning should be generated under:

```text
datasets/strategies/P1_MULTIPLIER_V0/_memory/strategy_learning_summary.json
datasets/strategies/P1_MULTIPLIER_V0/_memory/strategy_learning_summary.md
```

Use:

```powershell
python -m hedge_lab.analysis.build_strategy_learning_summary --strategy-id P1_MULTIPLIER_V0
```

## 11. Agent and RAG Usage

Agents should compare P1_MULTIPLIER_V0 against P1_NET_V0 by asking:

```text
Which strategy controls gross better?
Which strategy recovers better in range?
Which strategy fails first in trends?
Which has better regime balance?
Which has lower risk debt?
Which multiplier values are survivable?
```

## 12. Open Questions

Important future experiments:

```text
Find safest multiplier range.
Compare multiplier 1.25, 1.5, 2.0, 2.5 and 3.0.
Test stronger protection limits.
Add historical GOLD validation.
Add spread/slippage stress.
Add recovery/close logic after profitable imbalance.
```
