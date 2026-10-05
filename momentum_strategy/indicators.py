"""基礎技術指標。所有函式只使用當期與過去的資料，不會偷看未來。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series | pd.DataFrame, window: int) -> pd.Series | pd.DataFrame:
    return series.rolling(window, min_periods=window).mean()


def trailing_return(series: pd.Series | pd.DataFrame, window: int) -> pd.Series | pd.DataFrame:
    return series / series.shift(window) - 1


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    ranges = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    )
    return ranges.max(axis=1)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder 的 ADX，數值越低代表越沒有趨勢。"""
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index
    )
    alpha = 1.0 / window
    smoothed_tr = true_range(high, low, close).ewm(
        alpha=alpha, adjust=False, min_periods=window
    ).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False, min_periods=window).mean() / smoothed_tr
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False, min_periods=window).mean() / smoothed_tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    dx = dx.replace([np.inf, -np.inf], np.nan)
    return dx.ewm(alpha=alpha, adjust=False, min_periods=window).mean()


def bollinger_bandwidth(close: pd.Series, window: int = 20, k: float = 2.0) -> pd.Series:
    """布林通道寬度 = (上軌 - 下軌) / 中軌。"""
    mid = sma(close, window)
    std = close.rolling(window, min_periods=window).std()
    return 2 * k * std / mid


def rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    """當期數值在過去 window 期(含當期)中的百分位，介於 0 到 1。"""
    return series.rolling(window, min_periods=window).apply(
        lambda x: np.mean(x <= x[-1]), raw=True
    )


def threshold_vote(x: pd.Series, upper: float, lower: float) -> pd.Series:
    """x > upper 投 +1，x < lower 投 -1，其他投 0；資料缺漏時為 NaN。"""
    vote = pd.Series(np.where(x > upper, 1.0, np.where(x < lower, -1.0, 0.0)), index=x.index)
    return vote.where(x.notna())


def combine_votes(votes: list[pd.Series]) -> pd.Series:
    """把幾個子指標的投票加總後取正負號，全部缺漏時為 NaN。"""
    frame = pd.concat(votes, axis=1)
    return np.sign(frame.sum(axis=1, min_count=1))
