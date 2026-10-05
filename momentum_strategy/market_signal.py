"""第 1 層：大盤方向訊號。

時間慣例：日期 t 的訊號使用 t 日收盤後(含美股 t 日收盤)已公布的資料，
只能用在 t+1 開盤之後的交易。回測時要用 t+1 之後的報酬，否則會有前視偏誤。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import (
    adx,
    bollinger_bandwidth,
    combine_votes,
    rolling_percentile,
    sma,
    threshold_vote,
    trailing_return,
)
from .trend_template import trend_template_mask

BULL = "Bull"
CORRECTION = "Correction"
BEAR = "Bear"
REBOUND = "Rebound"

COMPONENTS = ["breadth", "leaders", "volume", "chips", "cross"]


@dataclass(frozen=True)
class SignalConfig:
    # Goulding 市場週期：慢訊號 12 個月、快訊號 1 個月
    slow_window: int = 252
    fast_window: int = 21
    # 區間整理判斷
    ma_long: int = 200
    ma_slope_lookback: int = 20
    ma_slope_max: float = 0.01
    range_window: int = 60
    range_width_max: float = 0.10
    bb_window: int = 20
    bb_k: float = 2.0
    bb_pct_window: int = 252
    bb_pct_max: float = 0.30
    adx_window: int = 14
    adx_max: float = 20.0
    range_min_conditions: int = 3
    # 方向分數
    change_window: int = 20
    breadth_change_min: float = 0.10
    leaders_change_min: float = 0.02
    rs_min: float = 0.70
    volume_ratio_bull: float = 1.2
    volume_ratio_bear: float = 0.8
    margin_change_min: float = 0.02
    fx_change_min: float = 0.01
    min_components: int = 2
    long_threshold: float = 3.0
    short_threshold: float = -4.0
    # 突破確認
    breakout_buffer: float = 0.01
    breakout_volume_mult: float = 1.5
    volume_ma_window: int = 50
    false_breakout_days: int = 3
    # 多方曝險上限(佔總資金比例)
    long_cap_bull: float = 1.0
    long_cap_neutral: float = 0.5
    long_cap_bear: float = 0.0
    # 空方曝險上限：做空風險較高，只在確認後使用一半
    short_cap_confirmed: float = 0.5


@dataclass
class MarketData:
    """index 是必要資料，其餘缺漏時對應的分項會被排除。

    index: 加權指數日資料，欄位 open, high, low, close, volume
    constituents_close: 日期 x 股票代號的收盤價(算市場廣度和領導股)
    foreign_futures_net_oi: 外資台指期未平倉淨口數
    institutional_net_buy: 三大法人現貨買賣超金額
    margin_balance: 融資餘額
    financial_index: 金融類股指數
    sox: 費城半導體指數
    usdtwd: 美元兌新台幣匯率
    """

    index: pd.DataFrame
    constituents_close: pd.DataFrame | None = None
    foreign_futures_net_oi: pd.Series | None = None
    institutional_net_buy: pd.Series | None = None
    margin_balance: pd.Series | None = None
    financial_index: pd.Series | None = None
    sox: pd.Series | None = None
    usdtwd: pd.Series | None = None


def _align(series: pd.Series | None, index: pd.DatetimeIndex) -> pd.Series | None:
    """對齊到台股交易日；別的市場休市時沿用前一筆已知數值。"""
    if series is None:
        return None
    series = series.sort_index()
    return series.reindex(series.index.union(index)).ffill().reindex(index)


def market_state(close: pd.Series, cfg: SignalConfig) -> pd.DataFrame:
    """Goulding et al. (2023) 的四種市場週期。"""
    ret_slow = trailing_return(close, cfg.slow_window)
    ret_fast = trailing_return(close, cfg.fast_window)
    state = pd.Series(
        np.select(
            [
                (ret_slow >= 0) & (ret_fast >= 0),
                (ret_slow >= 0) & (ret_fast < 0),
                (ret_slow < 0) & (ret_fast < 0),
                (ret_slow < 0) & (ret_fast >= 0),
            ],
            [BULL, CORRECTION, BEAR, REBOUND],
            default="",
        ),
        index=close.index,
    )
    state = state.where(ret_slow.notna() & ret_fast.notna())
    return pd.DataFrame({"ret_slow": ret_slow, "ret_fast": ret_fast, "market_state": state})


def detect_range(index: pd.DataFrame, state: pd.Series, cfg: SignalConfig) -> pd.DataFrame:
    """判斷是否處於區間整理：5 個條件中符合 range_min_conditions 個以上。"""
    close, high, low = index["close"], index["high"], index["low"]
    ma_long = sma(close, cfg.ma_long)
    ma_slope = ma_long / ma_long.shift(cfg.ma_slope_lookback) - 1
    window_high = high.rolling(cfg.range_window, min_periods=cfg.range_window).max()
    window_low = low.rolling(cfg.range_window, min_periods=cfg.range_window).min()
    range_width = window_high / window_low - 1
    bbw_pct = rolling_percentile(
        bollinger_bandwidth(close, cfg.bb_window, cfg.bb_k), cfg.bb_pct_window
    )
    adx_value = adx(high, low, close, cfg.adx_window)

    conditions = pd.DataFrame(
        {
            "flat_ma": ma_slope.abs() < cfg.ma_slope_max,
            "narrow_range": range_width < cfg.range_width_max,
            "low_bandwidth": bbw_pct < cfg.bb_pct_max,
            "low_adx": adx_value < cfg.adx_max,
            "mixed_state": state.isin([CORRECTION, REBOUND]),
        }
    )
    range_conditions = conditions.sum(axis=1)
    return pd.DataFrame(
        {
            "ma200_slope": ma_slope,
            "range_width": range_width,
            "bbw_pct": bbw_pct,
            "adx": adx_value,
            "range_conditions": range_conditions,
            "is_range": range_conditions >= cfg.range_min_conditions,
            # 區間上下緣不含當日，突破才有意義
            "range_high": window_high.shift(1),
            "range_low": window_low.shift(1),
        }
    )


def breadth_component(close: pd.DataFrame, cfg: SignalConfig) -> pd.DataFrame:
    """市場廣度：站上 50MA 的比例變化 + 52 週新高減新低。"""
    ma50 = sma(close, 50)
    valid50 = ma50.notna() & close.notna()
    pct_above_ma50 = ((close > ma50) & valid50).sum(axis=1) / valid50.sum(axis=1).replace(0, np.nan)

    high_52w = close.rolling(252, min_periods=252).max()
    low_52w = close.rolling(252, min_periods=252).min()
    valid52 = high_52w.notna() & close.notna()
    n52 = valid52.sum(axis=1).replace(0, np.nan)
    new_highs = ((close >= high_52w) & valid52).sum(axis=1)
    new_lows = ((close <= low_52w) & valid52).sum(axis=1)
    nh_nl = ((new_highs - new_lows) / n52).rolling(
        cfg.change_window, min_periods=cfg.change_window
    ).mean()

    vote = combine_votes(
        [
            threshold_vote(
                pct_above_ma50.diff(cfg.change_window),
                cfg.breadth_change_min,
                -cfg.breadth_change_min,
            ),
            threshold_vote(nh_nl, 0.0, 0.0),
        ]
    )
    return pd.DataFrame({"pct_above_ma50": pct_above_ma50, "nh_nl": nh_nl, "comp_breadth": vote})


def leaders_component(close: pd.DataFrame, cfg: SignalConfig) -> pd.DataFrame:
    """符合趨勢樣板的股票比例是否在增加。"""
    mask, valid = trend_template_mask(close, cfg.rs_min)
    leaders_ratio = mask.sum(axis=1) / valid.sum(axis=1).replace(0, np.nan)
    vote = threshold_vote(
        leaders_ratio.diff(cfg.change_window), cfg.leaders_change_min, -cfg.leaders_change_min
    )
    return pd.DataFrame({"leaders_ratio": leaders_ratio, "comp_leaders": vote})


def volume_component(index: pd.DataFrame, cfg: SignalConfig) -> pd.DataFrame:
    """價漲量增、價跌量縮：上漲日總量 / 下跌日總量。"""
    change = index["close"].diff()
    volume = index["volume"].where(change.notna())
    up_volume = volume.where(change > 0, 0.0).rolling(cfg.change_window, min_periods=cfg.change_window).sum()
    down_volume = volume.where(change < 0, 0.0).rolling(cfg.change_window, min_periods=cfg.change_window).sum()
    ratio = up_volume / down_volume.replace(0, np.nan)
    vote = threshold_vote(ratio, cfg.volume_ratio_bull - 1e-12, cfg.volume_ratio_bear + 1e-12)
    return pd.DataFrame({"up_down_volume_ratio": ratio, "comp_volume": vote})


def chips_component(
    futures_oi: pd.Series | None,
    net_buy: pd.Series | None,
    margin: pd.Series | None,
    cfg: SignalConfig,
) -> pd.Series | None:
    """法人籌碼：外資期貨淨部位、三大法人買賣超、融資餘額(下降偏多)。"""
    w = cfg.change_window
    votes = []
    if futures_oi is not None:
        votes.append(threshold_vote(futures_oi.diff(w), 0.0, 0.0))
    if net_buy is not None:
        votes.append(threshold_vote(net_buy.rolling(w, min_periods=w).sum(), 0.0, 0.0))
    if margin is not None:
        votes.append(threshold_vote(-margin.pct_change(w), cfg.margin_change_min, -cfg.margin_change_min))
    return combine_votes(votes) if votes else None


def _stage_vote(series: pd.Series, cfg: SignalConfig) -> pd.Series:
    """站上 200MA 且 200MA 上升投 +1；跌破且下降(第四階段)投 -1。"""
    ma = sma(series, cfg.ma_long)
    rising = ma > ma.shift(cfg.fast_window)
    vote = pd.Series(
        np.where((series > ma) & rising, 1.0, np.where((series < ma) & ~rising, -1.0, 0.0)),
        index=series.index,
    )
    return vote.where(ma.shift(cfg.fast_window).notna())


def cross_component(
    financial: pd.Series | None,
    sox: pd.Series | None,
    usdtwd: pd.Series | None,
    cfg: SignalConfig,
) -> pd.Series | None:
    """跨市場：金融股、費半所處階段，以及新台幣升貶(升值偏多)。"""
    votes = []
    if financial is not None:
        votes.append(_stage_vote(financial, cfg))
    if sox is not None:
        votes.append(_stage_vote(sox, cfg))
    if usdtwd is not None:
        votes.append(
            threshold_vote(-usdtwd.pct_change(cfg.change_window), cfg.fx_change_min, -cfg.fx_change_min)
        )
    return combine_votes(votes) if votes else None


def run_breakout_state(
    close: pd.Series,
    range_high: pd.Series,
    range_low: pd.Series,
    up_break: pd.Series,
    down_break: pd.Series,
    bias: pd.Series,
    state: pd.Series,
    cfg: SignalConfig,
) -> pd.DataFrame:
    """逐日推進的突破狀態機，只用當日以前的資訊。

    - 方向分數偏多 + 帶量突破區間上緣 -> 做多確認，記下突破價位
    - 之後收盤跌回突破價位以下：false_breakout_days 天內算假突破，之後算跌回區間
    - 大盤轉為 Bear 時多方出場；空方對稱處理
    """
    events, modes = [], []
    mode, level, days = None, np.nan, 0
    for t in close.index:
        event = ""
        if mode == "long":
            days += 1
            if state.get(t) == BEAR:
                event, mode = "大盤轉空出場", None
            elif close[t] < level:
                event = "假突破出場" if days <= cfg.false_breakout_days else "跌回區間出場"
                mode = None
        elif mode == "short":
            days += 1
            if state.get(t) == BULL:
                event, mode = "大盤轉多回補", None
            elif close[t] > level:
                event = "假跌破回補" if days <= cfg.false_breakout_days else "漲回區間回補"
                mode = None
        else:
            if up_break[t]:
                if bias[t] == "long":
                    event, mode, level, days = "做多確認", "long", range_high[t], 0
                else:
                    event = "突破但方向分數不足"
            elif down_break[t]:
                if bias[t] == "short":
                    event, mode, level, days = "做空確認", "short", range_low[t], 0
                else:
                    event = "跌破但方向分數不足"
        events.append(event)
        modes.append(mode or "")
    return pd.DataFrame({"event": events, "mode": modes}, index=close.index)


def compute_market_signal(data: MarketData, cfg: SignalConfig | None = None) -> pd.DataFrame:
    cfg = cfg or SignalConfig()
    index = data.index.sort_index()
    dates = index.index
    close = index["close"]

    states = market_state(close, cfg)
    ranges = detect_range(index, states["market_state"], cfg)

    components = pd.DataFrame(index=dates, columns=[f"comp_{c}" for c in COMPONENTS], dtype=float)
    details = []
    if data.constituents_close is not None:
        panel = data.constituents_close.sort_index().reindex(dates)
        breadth = breadth_component(panel, cfg)
        leaders = leaders_component(panel, cfg)
        components["comp_breadth"] = breadth["comp_breadth"]
        components["comp_leaders"] = leaders["comp_leaders"]
        details += [breadth.drop(columns="comp_breadth"), leaders.drop(columns="comp_leaders")]
    volume = volume_component(index, cfg)
    components["comp_volume"] = volume["comp_volume"]
    details.append(volume.drop(columns="comp_volume"))

    chips = chips_component(
        _align(data.foreign_futures_net_oi, dates),
        _align(data.institutional_net_buy, dates),
        _align(data.margin_balance, dates),
        cfg,
    )
    if chips is not None:
        components["comp_chips"] = chips
    cross = cross_component(
        _align(data.financial_index, dates), _align(data.sox, dates), _align(data.usdtwd, dates), cfg
    )
    if cross is not None:
        components["comp_cross"] = cross

    n_components = components.notna().sum(axis=1)
    raw_score = components.sum(axis=1, min_count=1)
    # 缺資料時換算成 -5 ~ +5 的尺度，可用分項太少則不給方向
    direction_score = (raw_score * len(COMPONENTS) / n_components).where(
        n_components >= cfg.min_components
    )
    bias = pd.Series(
        np.where(
            direction_score >= cfg.long_threshold,
            "long",
            np.where(direction_score <= cfg.short_threshold, "short", "neutral"),
        ),
        index=dates,
    )

    vol_ma = index["volume"].rolling(cfg.volume_ma_window, min_periods=cfg.volume_ma_window).mean().shift(1)
    heavy_volume = index["volume"] > cfg.breakout_volume_mult * vol_ma
    up_break = (close > ranges["range_high"] * (1 + cfg.breakout_buffer)) & heavy_volume
    down_break = (close < ranges["range_low"] * (1 - cfg.breakout_buffer)) & heavy_volume

    machine = run_breakout_state(
        close, ranges["range_high"], ranges["range_low"], up_break, down_break, bias,
        states["market_state"], cfg,
    )

    state = states["market_state"]
    is_range = ranges["is_range"]
    mode = machine["mode"]
    action = np.select(
        [
            machine["event"] != "",
            mode == "long",
            mode == "short",
            (state == BULL) & ~is_range,
            (state == BEAR) & ~is_range,
            bias == "long",
            bias == "short",
        ],
        [machine["event"], "持有多方", "持有空方", "多頭趨勢", "空頭趨勢", "準備做多", "準備做空"],
        default="觀望",
    )
    long_cap = np.select(
        [mode == "long", is_range, state == BULL, state == BEAR, state.isin([CORRECTION, REBOUND])],
        [cfg.long_cap_bull, cfg.long_cap_neutral, cfg.long_cap_bull, cfg.long_cap_bear, cfg.long_cap_neutral],
        default=0.0,
    )
    short_cap = np.where(mode == "short", cfg.short_cap_confirmed, 0.0)

    return pd.concat(
        [
            close.rename("close"),
            states,
            ranges,
            *details,
            components,
            pd.DataFrame(
                {
                    "n_components": n_components,
                    "direction_score": direction_score,
                    "bias": bias,
                    "up_break": up_break,
                    "down_break": down_break,
                    "event": machine["event"],
                    "mode": mode,
                    "action": action,
                    "long_cap": long_cap,
                    "short_cap": short_cap,
                },
                index=dates,
            ),
        ],
        axis=1,
    )
