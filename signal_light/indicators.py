"""Bollinger Bands indicator."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BollingerConfig:
    window: int = 20
    num_std: float = 2.0


def bollinger_bands(close: pd.Series, config: BollingerConfig = BollingerConfig()) -> pd.DataFrame:
    """Compute Bollinger Bands and %B for a close-price series.

    %B expresses where the price sits relative to the bands: 1.0 means the
    price is exactly at the upper band, 0.0 exactly at the lower band; values
    above 1 or below 0 mean the price has pushed through a band.

    Returns a DataFrame indexed like `close` with columns:
    close, middle, upper, lower, percent_b, bandwidth.
    """
    middle = close.rolling(window=config.window, min_periods=config.window).mean()
    std = close.rolling(window=config.window, min_periods=config.window).std(ddof=0)
    upper = middle + config.num_std * std
    lower = middle - config.num_std * std
    percent_b = (close - lower) / (upper - lower)
    bandwidth = (upper - lower) / middle

    return pd.DataFrame(
        {
            "close": close,
            "middle": middle,
            "upper": upper,
            "lower": lower,
            "percent_b": percent_b,
            "bandwidth": bandwidth,
        }
    )
