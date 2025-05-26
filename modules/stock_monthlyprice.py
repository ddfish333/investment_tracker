import yfinance as yf
import pandas as pd
from datetime import datetime

def get_monthly_prices(symbol: str, start: str = "2019-01-01", end: str = None) -> pd.DataFrame:
    """
    從 Yahoo Finance 抓取某股票的每月收盤價。
    - symbol: 股票代碼，例如 '2330.TW'、'AAPL'
    - start: 起始日期（字串，格式為 'YYYY-MM-DD'）
    - end: 結束日期（預設為今天）
    回傳 DataFrame，包含月份與收盤價。
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    data = yf.download(symbol, start=start, end=end, interval="1mo", auto_adjust=True, progress=False)

    if data.empty:
        raise ValueError(f"找不到股票代碼 {symbol} 的月資料")

    df = data[['Close']].copy()
    df.index = df.index.to_period("M")
    df.rename(columns={"Close": symbol}, inplace=True)
    return df
