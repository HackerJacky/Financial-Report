import pandas as pd

from signal_light.signals import Signal, SignalConfig, generate_signals


def test_generate_signals_thresholds():
    percent_b = pd.Series([0.9, 0.5, 0.1, float("nan")])
    bands = pd.DataFrame({"percent_b": percent_b})

    signals = generate_signals(bands, SignalConfig(top_threshold=0.8, bottom_threshold=0.2))

    assert signals.iloc[0] == Signal.NEAR_TOP.value
    assert signals.iloc[1] == Signal.NONE.value
    assert signals.iloc[2] == Signal.NEAR_BOTTOM.value
    assert signals.iloc[3] == Signal.NONE.value
