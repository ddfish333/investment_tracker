# modules/stock_monthlyprice.py
```python
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings


def get_stock_monthly_prices(codes, transaction_path):
    """
    取得指定股票代號的每月月末收盤價（已轉成台幣）
    codes: list of str, 股票代號列表，台股代號原樣輸入，美股後綴需加 US
    transaction_path: str, 交易檔案路徑，用來解析出所有月份範圍
    """
    # 解析所有追蹤月份
    _, _, _, all_codes, all_months, *_ = parse_monthly_holdings(transaction_path)
    
    # 抓取原始月末收盤價與匯率
    price_df = fetch_month_end_prices(codes, all_months)
    fx = fetch_month_end_fx(all_months)

    # 將美股價格轉為台幣
    for code in codes:
        if code.endswith("US"):
            price_df[code] = price_df[code] * fx
    
    return price_df
```