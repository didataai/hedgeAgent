hedge_discovery_lab/
│
├── inputs/
│   ├── markdown/
│   ├── mql5/
│   ├── spreadsheets/
│   └── text/
│
├── specs/
│   └── strategy_spec.json
│
├── translated/
│   └── strategy_python.py
│
├── simulator/
│   ├── engine.py
│   ├── market_scenarios.py
│   ├── broker_simulator.py
│   └── metrics.py
│
├── runs/
│   └── <strategy_id>/<run_id>/
│       ├── trades.csv
│       ├── equity_curve.csv
│       ├── events.jsonl
│       ├── metrics.json
│       └── summary.md
│
├── memory/
│   ├── strategy_registry.parquet
│   ├── experiment_results.parquet
│   └── failure_patterns.jsonl
│
└── agents/
    ├── strategy_interpreter.py
    ├── mql5_analyzer.py
    ├── python_generator.py
    ├── backtest_runner.py
    └── report_agent.py