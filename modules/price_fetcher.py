import pandas as pd
from modules.stock_monthlyprice import fetch_monthly_prices_batch

def fetch_month_end_prices(codes, months):
    """
    根據股票代碼與月份，抓取每月最後一天的收盤價
    - codes: list of 股票代碼
    - months: DatetimeIndex（應該是 timestamp 格式）
    """
    start = months.min().strftime("%Y-%m-%d")
    end = months.max().strftime("%Y-%m-%d")

    df = fetch_monthly_prices_batch(codes, start=start, end=end)
    df = df.reindex(months)  # 確保 index 與月資料對齊
    return df

def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬匯率：全為 30.0
    未來可擴充為 API 抓取匯率
    """
    return pd.Series([30.0] * len(months), index=months)
