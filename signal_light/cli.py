"""Command-line entry point: fetch data, compute signals, backtest, and optionally plot."""

import argparse
import os
import sys

from .backtest import BacktestConfig, run_backtest
from .data import fetch_history, load_csv
from .indicators import BollingerConfig, bollinger_bands
from .plot import plot_equity_curve, plot_signals
from .signals import SignalConfig, generate_signals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bollinger Band stock signal light backtester")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--start", default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD")
    parser.add_argument("--period", default=None, help="yfinance period, e.g. 2y (overrides --start/--end)")
    parser.add_argument("--csv", default=None, help="Load local CSV instead of fetching from Yahoo Finance")
    parser.add_argument("--window", type=int, default=20, help="Bollinger Band moving-average window")
    parser.add_argument("--num-std", type=float, default=2.0, help="Bollinger Band standard-deviation multiplier")
    parser.add_argument("--top-threshold", type=float, default=0.8, help="%%B at/above this triggers near-top")
    parser.add_argument("--bottom-threshold", type=float, default=0.2, help="%%B at/below this triggers near-bottom")
    parser.add_argument("--no-short", action="store_true", help="Disable short entries on near-top signals")
    parser.add_argument("--capital", type=float, default=100_000.0, help="Initial backtest capital")
    parser.add_argument("--plot", default=None, help="Directory to save chart PNGs into")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.csv:
        history = load_csv(args.csv)
    else:
        history = fetch_history(args.ticker, start=args.start, end=args.end, period=args.period)

    bands = bollinger_bands(history["Close"], BollingerConfig(window=args.window, num_std=args.num_std))
    signals = generate_signals(
        bands, SignalConfig(top_threshold=args.top_threshold, bottom_threshold=args.bottom_threshold)
    )
    result = run_backtest(
        bands, signals, BacktestConfig(allow_short=not args.no_short, initial_capital=args.capital)
    )

    summary = result.summary()
    print(f"\n=== {args.ticker} Bollinger Band Signal Light Backtest ===")
    print(f"Trades:            {summary['num_trades']}")
    print(f"Win rate:          {summary['win_rate']:.1%}")
    print(f"Avg trade return:  {summary['avg_trade_return']:.2%}")
    print(f"Total return:      {summary['total_return']:.2%}")
    print(f"Sharpe ratio:      {summary['sharpe_ratio']:.2f}")
    print(f"Max drawdown:      {summary['max_drawdown']:.2%}")

    if args.plot:
        os.makedirs(args.plot, exist_ok=True)
        plot_signals(bands, signals, args.ticker, save_path=os.path.join(args.plot, f"{args.ticker}_signals.png"))
        plot_equity_curve(
            result.equity_curve, args.ticker, save_path=os.path.join(args.plot, f"{args.ticker}_equity.png")
        )
        print(f"\nCharts saved to {args.plot}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
