# modules/price_fetcher.py
```python
import pandas as pd


def fetch_month_end_prices(codes, months):
    """
    擷取指定股票在每月最後一個交易日的收盤價。
    目前採用模擬：所有股票回傳固定 100
    日後可替換為實際 API 呼叫
    """
    df = pd.DataFrame({code: [100.0 for _ in months] for code in codes}, index=months)
    # 重新 index，確保月份完整
    return df.reindex(months).astype(float)


def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    擷取指定月份的匯率 (USD->TWD)
    目前採用模擬：固定值 30
    """
    series = pd.Series([30.0 for _ in months], index=months)
    return series.astype(float)
```
