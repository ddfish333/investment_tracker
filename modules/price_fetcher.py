import pandas as pd

def fetch_month_end_prices(codes, months):
    """
    模擬歷史每月股票收盤價（固定為100，未連接API）
    """
    return pd.DataFrame({code: [100.0 for _ in months] for code in codes}, index=months)

def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬每月匯率（固定為30）
    """
    return pd.Series([30.0 for _ in months], index=months)

