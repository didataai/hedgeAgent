# Hedge Evolution Lab — Arquitetura v0.1

## Visão geral

O Hedge Evolution Lab é composto por oito blocos principais:

```text
Hedge Evolution Lab
├── 1. Simulator Engine
├── 2. Strategy Genome Engine
├── 3. Scenario Generator
├── 4. Execution Engine
├── 5. Risk & Fitness Engine
├── 6. Evolution Engine
├── 7. Strategy Memory
└── 8. Multi-Agent Layer
```

## Ordem correta do projeto

```text
1. Simulador
2. Métricas
3. Estratégias base
4. Cenários
5. Fitness
6. Evolução
7. Agentes
8. Exportação para MQL5
```

## Simulator Engine

Responsável por simular:

- preço;
- ordens a mercado;
- ordens pendentes;
- spread;
- slippage;
- posições abertas;
- balance;
- equity;
- drawdown;
- margem;
- lucro realizado;
- lucro flutuante.

O simulador deve ser independente de MetaTrader no início.

## Strategy Genome Engine

Representa uma estratégia como um genoma combinável:

```json
{
  "entry_module": "p1_net",
  "hedge_module": "worm_large_small",
  "recovery_module": "oldest_loss_best_hedges",
  "baton_module": "residual_becomes_center",
  "lot_module": "anti_martingale",
  "protection_module": "max_gross_trend_pause"
}
```

## Risk & Fitness Engine

O score nunca deve usar apenas lucro.

Deve penalizar:

- drawdown alto;
- gross lots alto;
- muitas posições;
- tempo excessivo travado;
- margem alta;
- fragilidade a tendência;
- fragilidade a gap;
- complexidade excessiva.
