"""Visualization for the Bollinger Band signal light."""

import pandas as pd

from .signals import Signal


def plot_signals(bands: pd.DataFrame, signals: pd.Series, ticker: str, save_path: str | None = None):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(bands.index, bands["close"], label="Close", color="black", linewidth=1)
    ax.plot(bands.index, bands["upper"], label="Upper Band", color="red", linewidth=0.8, linestyle="--")
    ax.plot(bands.index, bands["middle"], label="Middle (SMA)", color="gray", linewidth=0.8)
    ax.plot(bands.index, bands["lower"], label="Lower Band", color="green", linewidth=0.8, linestyle="--")
    ax.fill_between(bands.index, bands["lower"], bands["upper"], color="gray", alpha=0.08)

    near_top = signals == Signal.NEAR_TOP.value
    near_bottom = signals == Signal.NEAR_BOTTOM.value
    ax.scatter(
        bands.index[near_top], bands["close"][near_top], color="red", marker="v", s=40, label="Near Top", zorder=5
    )
    ax.scatter(
        bands.index[near_bottom],
        bands["close"][near_bottom],
        color="green",
        marker="^",
        s=40,
        label="Near Bottom",
        zorder=5,
    )

    ax.set_title(f"{ticker} - Bollinger Band Signal Light")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend(loc="best")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_equity_curve(equity_curve: pd.Series, ticker: str, save_path: str | None = None):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(equity_curve.index, equity_curve.values, color="blue")
    ax.set_title(f"{ticker} - Strategy Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig
