"""Bollinger Band stock signal light: near-top / near-bottom detection and backtesting."""

from .backtest import BacktestConfig, BacktestResult, Trade, run_backtest
from .indicators import BollingerConfig, bollinger_bands
from .signals import Signal, SignalConfig, generate_signals

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "Trade",
    "run_backtest",
    "BollingerConfig",
    "bollinger_bands",
    "Signal",
    "SignalConfig",
    "generate_signals",
]
