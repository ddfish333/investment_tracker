# modules/price_fetcher.py
```python
import pandas as pd
from datetime import datetime

def fetch_month_end_prices(codes, months):
    """
    模擬或真實抓取每月收盤價，index 為月份，columns 為股票代碼
    """
    # placeholder: 全部價格皆固定 100
    df = pd.DataFrame({code: [100.0]*len(months) for code in codes}, index=months)
    return df.astype(float)


def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬或真實抓取每月匯率，index 為月份
    """
    # placeholder: 全部匯率固定 30
    return pd.Series([30.0]*len(months), index=months).astype(float)
```
