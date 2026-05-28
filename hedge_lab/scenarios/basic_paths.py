"""
File: hedge_lab/scenarios/basic_paths.py

Purpose:
    Provide small synthetic market paths for the first Hedge Evolution Lab simulations.

Inputs:
    - Optional scenario name selected by the runner or tests.

Outputs:
    - Scenario objects containing asset, timeframe, prices and metadata.

Integrations:
    - Used by hedge_lab.simulator.run_simulation.
    - Later can be reused by metrics, evolution and agent layers.

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - These are synthetic paths, not historical market data.
    - Do not hardcode strategy behavior here; scenarios only describe market movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PricePathScenario:
    """Synthetic price path used by the simulator."""

    name: str
    asset: str
    timeframe: str
    prices: List[float]
    description: str


def get_basic_scenarios(asset: str = "SYNTH", timeframe: str = "SIM") -> Dict[str, PricePathScenario]:
    """
    Return a small catalog of deterministic scenarios.

    The default asset/timeframe are intentionally synthetic so this module
    does not imply GOLD-only or any specific timeframe dependency.
    """

    return {
        "range_up_down": PricePathScenario(
            name="range_up_down",
            asset=asset,
            timeframe=timeframe,
            prices=[3000.0, 3300.0, 3000.0, 3300.0, 3000.0],
            description="Clean alternating range path for validating P1-Net mechanics.",
        ),
        "trend_up": PricePathScenario(
            name="trend_up",
            asset=asset,
            timeframe=timeframe,
            prices=[3000.0, 3300.0, 3600.0, 3900.0, 4200.0],
            description="Simple one-way uptrend path for exposing accumulation risk.",
        ),
        "trend_down": PricePathScenario(
            name="trend_down",
            asset=asset,
            timeframe=timeframe,
            prices=[3000.0, 2700.0, 2400.0, 2100.0, 1800.0],
            description="Simple one-way downtrend path for exposing accumulation risk.",
        ),
        "spike_return": PricePathScenario(
            name="spike_return",
            asset=asset,
            timeframe=timeframe,
            prices=[3000.0, 3600.0, 3300.0, 3000.0, 3150.0],
            description="Spike with partial/full return for recovery-behavior exploration.",
        ),
    }
