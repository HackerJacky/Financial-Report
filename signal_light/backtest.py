"""Backtest engine for the Bollinger Band near-top/near-bottom signal light."""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .signals import Signal


@dataclass(frozen=True)
class BacktestConfig:
    allow_short: bool = True  # open/flip to a short on near-top signals
    initial_capital: float = 100_000.0


@dataclass
class Trade:
    side: str  # "long" or "short"
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None

    @property
    def pnl_pct(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        change = (self.exit_price - self.entry_price) / self.entry_price
        return change if self.side == "long" else -change


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series

    @property
    def closed_trades(self) -> list[Trade]:
        return [t for t in self.trades if t.exit_price is not None]

    def summary(self) -> dict:
        closed = self.closed_trades
        n = len(closed)
        wins = [t for t in closed if t.pnl_pct > 0]

        total_return = (
            self.equity_curve.iloc[-1] / self.equity_curve.iloc[0] - 1 if len(self.equity_curve) else 0.0
        )
        daily_returns = self.equity_curve.pct_change().dropna()
        sharpe_ratio = (
            (daily_returns.mean() / daily_returns.std()) * (252**0.5)
            if len(daily_returns) > 1 and daily_returns.std() > 0
            else 0.0
        )
        running_max = self.equity_curve.cummax()
        drawdown = self.equity_curve / running_max - 1
        max_drawdown = drawdown.min() if len(drawdown) else 0.0

        return {
            "num_trades": n,
            "win_rate": (len(wins) / n) if n else 0.0,
            "avg_trade_return": (sum(t.pnl_pct for t in closed) / n) if n else 0.0,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
        }


def run_backtest(
    bands: pd.DataFrame,
    signals: pd.Series,
    config: BacktestConfig = BacktestConfig(),
) -> BacktestResult:
    """Simulate the near-top/near-bottom mean-reversion strategy bar by bar.

    State machine, evaluated at each bar's close:
      - flat  + NEAR_BOTTOM -> enter long
      - flat  + NEAR_TOP    -> enter short (if allow_short)
      - long  + NEAR_TOP    -> take profit; flip to short (if allow_short)
      - short + NEAR_BOTTOM -> cover; flip to long

    A position decided at bar t is held from t's close onward and its return
    is realized over t -> t+1 (no lookahead: the decision uses only
    information available at t's close).
    """
    close = bands["close"]
    trades: list[Trade] = []
    open_trade: Optional[Trade] = None
    position = 0  # 0 flat, 1 long, -1 short
    target_positions: list[int] = []

    for date, price, signal in zip(close.index, close, signals):
        if position == 0:
            if signal == Signal.NEAR_BOTTOM.value:
                open_trade = Trade(side="long", entry_date=date, entry_price=price)
                trades.append(open_trade)
                position = 1
            elif signal == Signal.NEAR_TOP.value and config.allow_short:
                open_trade = Trade(side="short", entry_date=date, entry_price=price)
                trades.append(open_trade)
                position = -1
        elif position == 1 and signal == Signal.NEAR_TOP.value:
            open_trade.exit_date, open_trade.exit_price = date, price
            if config.allow_short:
                open_trade = Trade(side="short", entry_date=date, entry_price=price)
                trades.append(open_trade)
                position = -1
            else:
                open_trade = None
                position = 0
        elif position == -1 and signal == Signal.NEAR_BOTTOM.value:
            open_trade.exit_date, open_trade.exit_price = date, price
            open_trade = Trade(side="long", entry_date=date, entry_price=price)
            trades.append(open_trade)
            position = 1

        target_positions.append(position)

    position_series = pd.Series(target_positions, index=close.index)
    daily_returns = close.pct_change()
    strategy_returns = (position_series.shift(1).fillna(0) * daily_returns).fillna(0)
    equity_curve = config.initial_capital * (1 + strategy_returns).cumprod()
    equity_curve.name = "equity"

    return BacktestResult(trades=trades, equity_curve=equity_curve)
