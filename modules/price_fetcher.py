import pandas as pd

def fetch_month_end_prices(codes, months):
    """
    模擬歷史每月股票收盤價（固定為100，未連接API）
    回傳一個 DataFrame：index=months, columns=codes，全部都是 float
    """
    # 建立完整的月份 × 代碼表格，並填入固定收盤價 100.0
    price_df = pd.DataFrame(index=months, columns=codes)
    return price_df.fillna(100.0)

def fetch_month_end_fx(months, base="USD", quote="TWD"):
    """
    模擬每月匯率（固定為30）
    """
    return pd.Series([30.0 for _ in months], index=months)
