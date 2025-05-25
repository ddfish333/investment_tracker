# modules/price_fetcher.py
```python
import pandas as pd


def fetch_month_end_prices(codes, months):
    """
    擷取指定股票在每月最後交易日的收盤價。
    目前模擬：固定回傳 100.0
    未來可替換為實際 API 呼叫
    """
    # 建立固定價格 DataFrame，index 為 months, columns 為 codes
    price_df = pd.DataFrame({code: [100.0] * len(months) for code in codes}, index=months)
    return price_df.astype(float)


def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    擷取每月 USD->TWD 匯率。
    目前模擬：固定 30.0
    """
    fx = pd.Series([30.0] * len(months), index=months)
    return fx.astype(float)
```