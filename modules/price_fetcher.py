# modules/price_fetcher.py
import pandas as pd


def fetch_month_end_prices(codes, months):
    """
    模擬或抓取歷史每月股票收盤價（預設為100.0，可替換為 API 調用）
    返回 DataFrame：index 為 months，columns 為 codes
    """
    idx = pd.to_datetime(months)
    price_df = pd.DataFrame(
        {code: [100.0 for _ in idx] for code in codes},
        index=idx
    )
    price_df.columns = codes
    return price_df


def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬或抓取歷史每月匯率（預設為30.0，可替換為 API）
    返回 Series：index 為 months
    """
    idx = pd.to_datetime(months)
    fx = pd.Series([30.0 for _ in idx], index=idx)
    return fx
