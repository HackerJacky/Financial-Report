"""Historical price data access."""

from pathlib import Path

import pandas as pd


def fetch_history(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    period: str | None = None,
) -> pd.DataFrame:
    """Fetch daily OHLC history for a ticker via yfinance.

    Requires network access to Yahoo Finance. Raises RuntimeError instead of
    silently returning an empty frame if the download comes back empty
    (blocked network, bad ticker, no data for the range, etc.).
    """
    import yfinance as yf

    kwargs = {"progress": False, "auto_adjust": True}
    if period:
        kwargs["period"] = period
    else:
        kwargs["start"] = start
        kwargs["end"] = end

    df = yf.download(ticker, **kwargs)
    if df.empty:
        raise RuntimeError(
            f"No data returned for '{ticker}'. Check the ticker symbol, date range, "
            "and network access to Yahoo Finance."
        )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load OHLC history from a local CSV with a Date column and a Close column."""
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date")
