import pandas as pd
import yfinance as yf
from datetime import datetime


def fetch_monthly_prices_batch(codes, months):
    """
    批次抓取多檔股票的每月收盤價
    codes: list of stock codes（如 ['2330.TW', 'AAPL']）
    months: DatetimeIndex of month-ends
    return: DataFrame(index=months, columns=codes)
    """
    start = months.min().strftime("%Y-%m-%d")
    end = (months.max() + 1).strftime("%Y-%m-%d")  # yfinance 不含 end，所以往後一個月

    data = yf.download(codes, start=start, end=end, interval="1mo", group_by="ticker", auto_adjust=True, progress=False)
    df = pd.DataFrame(index=months)

    for code in codes:
        try:
            if len(codes) == 1:
                close = data['Close']
            else:
                close = data[code]['Close']
            close.index = close.index.to_period("M")
            df[code] = close.reindex(months).astype(float)
        except Exception as e:
            print(f"❌ 無法取得 {code} 的價格：{e}")
            df[code] = float('nan')

    return df


def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬或實作匯率抓取，這裡先固定 30.0。
    未來可接 API 實作。
    """
    return pd.Series([30.0] * len(months), index=months)
