# modules/asset_value.py
```python
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx

def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股：返回三個 DataFrame (Lo, Sean, 共享) 及 months, codes 清單
    monthly_Lo, monthly_Sean, monthly_Joint, all_codes, all_months = parse_monthly_holdings(transaction_path)

    # 取得價格與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_ser = fetch_month_end_fx(all_months)

    # 計算各自資產 (USD 轉 TWD)
    val_Lo = monthly_Lo.mul(price_df).mul(fx_ser, axis=0)
    val_Sean = monthly_Sean.mul(price_df).mul(fx_ser, axis=0)
    val_Joint = monthly_Joint.mul(price_df).mul(fx_ser, axis=0)

    # 總覽 DataFrame
    summary = pd.DataFrame({
        'Lo': val_Lo.sum(axis=1),
        'Sean': val_Sean.sum(axis=1),
        'Total': (val_Lo + val_Sean + val_Joint).sum(axis=1)
    })

    # 詳細 MultiIndex DataFrame (Code, Owner)
    detail = pd.concat([
        val_Lo.add_suffix('_Lo'),
        val_Sean.add_suffix('_Sean'),
        val_Joint.add_suffix('_Joint')
    ], axis=1)
    # 重整索引層級
    detail.columns = pd.MultiIndex.from_tuples([
        (col.split('_')[0], col.split('_')[1]) for col in detail.columns
    ], names=['Code','Owner'])

    return summary, detail
```
