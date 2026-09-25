"""Signal classification from Bollinger Band %B."""

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class Signal(str, Enum):
    NEAR_TOP = "near_top"  # take-profit on longs / consider opening or adding shorts
    NEAR_BOTTOM = "near_bottom"  # cover shorts / consider going long
    NONE = "none"


@dataclass(frozen=True)
class SignalConfig:
    top_threshold: float = 0.8  # %B >= this counts as "near top"
    bottom_threshold: float = 0.2  # %B <= this counts as "near bottom"


def generate_signals(bands: pd.DataFrame, config: SignalConfig = SignalConfig()) -> pd.Series:
    """Classify each bar's %B into NEAR_TOP / NEAR_BOTTOM / NONE.

    `bands` must have a "percent_b" column, as produced by `bollinger_bands`.
    """
    percent_b = bands["percent_b"]
    signal = pd.Series(Signal.NONE.value, index=percent_b.index)
    signal[percent_b >= config.top_threshold] = Signal.NEAR_TOP.value
    signal[percent_b <= config.bottom_threshold] = Signal.NEAR_BOTTOM.value
    return signal
