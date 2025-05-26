import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def get_monthly_prices(symbol: str, start: str = "2019-01-01", end: str = None, plot=False) -> pd.DataFrame:
    """
    從 Yahoo Finance 抓取某股票的每月收盤價。
    - symbol: 股票代碼，例如 '2330.TW'、'AAPL'
    - start: 起始日期（字串，格式為 'YYYY-MM-DD'）
    - end: 結束日期（預設為今天）
    - plot: 是否畫出折線圖
    回傳 DataFrame，包含月份與收盤價。
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    df = yf.download(
        tickers=symbol,
        start=start,
        end=end,
        interval="1mo",
        group_by="ticker",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"找不到股票代碼 {symbol} 的月資料")

    # 如果是多股票格式
    if isinstance(df.columns, pd.MultiIndex):
        df = df[symbol]["Close"]
    else:
        df = df["Close"]

    df = df.dropna()
    df.index = df.index.to_period("M").to_timestamp()
    df.name = symbol

    if plot:
        df.plot(title=f"{symbol} 每月收盤價", figsize=(10, 4))
        plt.xlabel("月份")
        plt.ylabel("收盤價 (TWD/USD)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return df.to_frame()
