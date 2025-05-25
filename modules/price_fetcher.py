mport pandas as pd
from datetime import datetime


def fetch_month_end_prices(codes, months):
    """
    模擬或真實抓取每月收盤價
    - codes: list of stock codes
    - months: DatetimeIndex of month-ends
    回傳 DataFrame(index=months, columns=codes) with float prices
    """
    # placeholder: 全部價格皆固定為 100.0
    df = pd.DataFrame(
        {code: [100.0] * len(months) for code in codes},
        index=months
    )
    return df.astype(float)


def fetch_month_end_fx(months, base="USD", quote="TWD"):  # noqa: ARG000
    """
    模擬或真實抓取每月匯率
    - months: DatetimeIndex of month-ends
    回傳 Series(index=months) with float FX rate
    """
    # placeholder: 全部匯率固定為 30.0
    fx = pd.Series([30.0] * len(months), index=months)
    return fx.astype(float)