import numpy as np
import pandas as pd

from signal_light.backtest import BacktestConfig, run_backtest
from signal_light.indicators import BollingerConfig, bollinger_bands
from signal_light.signals import SignalConfig, generate_signals


def _oscillating_prices(n: int = 250) -> pd.Series:
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    wave = np.sin(np.linspace(0, 10 * np.pi, n)) * 8
    return pd.Series(100 + wave, index=dates)


def test_backtest_alternates_long_and_short_on_oscillation():
    prices = _oscillating_prices()
    bands = bollinger_bands(prices, BollingerConfig(window=20, num_std=1.5))
    signals = generate_signals(bands, SignalConfig(top_threshold=0.85, bottom_threshold=0.15))

    result = run_backtest(bands, signals, BacktestConfig(allow_short=True, initial_capital=100_000))

    assert len(result.trades) > 2
    sides = [t.side for t in result.trades]
    assert "long" in sides and "short" in sides
    for a, b in zip(sides, sides[1:]):
        assert a != b  # position always flips, never stacks

    summary = result.summary()
    assert summary["num_trades"] > 0
    assert len(result.equity_curve) == len(prices)
    assert result.equity_curve.iloc[0] > 0


def test_backtest_no_short_never_opens_short_trades():
    prices = _oscillating_prices()
    bands = bollinger_bands(prices, BollingerConfig(window=20, num_std=1.5))
    signals = generate_signals(bands, SignalConfig(top_threshold=0.85, bottom_threshold=0.15))

    result = run_backtest(bands, signals, BacktestConfig(allow_short=False, initial_capital=100_000))

    assert len(result.trades) > 0
    assert all(t.side == "long" for t in result.trades)


def test_flat_series_produces_no_trades():
    dates = pd.date_range("2022-01-01", periods=60, freq="D")
    prices = pd.Series(100.0, index=dates)
    bands = bollinger_bands(prices, BollingerConfig(window=20, num_std=2))
    signals = generate_signals(bands, SignalConfig())

    result = run_backtest(bands, signals)

    assert result.trades == []
    assert (result.equity_curve == 100_000.0).all()
