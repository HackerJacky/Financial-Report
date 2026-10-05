"""Minervini 趨勢樣板。大盤層用它計算「領導股數量」，之後的選股層也會沿用。"""

from __future__ import annotations

import pandas as pd

from .indicators import sma, trailing_return


def trend_template_mask(
    close: pd.DataFrame, rs_min: float = 0.70
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """輸入日期 x 股票代號的收盤價，回傳 (是否符合樣板, 是否有足夠資料判斷)。

    8 條條件：
    1. 股價 > 150MA 且 > 200MA
    2. 150MA > 200MA
    3. 200MA 比一個月前高(上升中)
    4. 50MA > 150MA 且 > 200MA
    5. 股價 > 50MA
    6. 股價比 52 週低點高至少 30%
    7. 股價距 52 週高點不超過 25%
    8. 相對強度(過去 12 個月報酬的全市場百分位) >= rs_min
    """
    ma50 = sma(close, 50)
    ma150 = sma(close, 150)
    ma200 = sma(close, 200)
    ma200_prev = ma200.shift(21)
    low_52w = close.rolling(252, min_periods=252).min()
    high_52w = close.rolling(252, min_periods=252).max()
    rs = trailing_return(close, 252).rank(axis=1, pct=True)

    mask = (
        (close > ma150)
        & (close > ma200)
        & (ma150 > ma200)
        & (ma200 > ma200_prev)
        & (ma50 > ma150)
        & (ma50 > ma200)
        & (close > ma50)
        & (close >= 1.30 * low_52w)
        & (close >= 0.75 * high_52w)
        & (rs >= rs_min)
    )
    valid = ma200_prev.notna() & low_52w.notna() & rs.notna()
    return mask & valid, valid
