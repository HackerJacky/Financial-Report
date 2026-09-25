import numpy as np
import pandas as pd

from signal_light.indicators import BollingerConfig, bollinger_bands


def test_bollinger_bands_shape_and_bounds():
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    prices = pd.Series(100 + np.sin(np.linspace(0, 6 * np.pi, 60)) * 5, index=dates)

    bands = bollinger_bands(prices, BollingerConfig(window=20, num_std=2))

    assert list(bands.columns) == ["close", "middle", "upper", "lower", "percent_b", "bandwidth"]
    valid = bands.dropna()
    assert len(valid) == 60 - 20 + 1
    assert (valid["upper"] >= valid["middle"]).all()
    assert (valid["middle"] >= valid["lower"]).all()


def test_percent_b_matches_definition():
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    prices = pd.Series(np.linspace(90, 110, 30), index=dates)

    bands = bollinger_bands(prices, BollingerConfig(window=10, num_std=2))
    valid = bands.dropna()

    expected = (valid["close"] - valid["lower"]) / (valid["upper"] - valid["lower"])
    pd.testing.assert_series_equal(valid["percent_b"], expected, check_names=False)
