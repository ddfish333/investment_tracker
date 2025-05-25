# modules/asset_value.py
```python
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months = parse_monthly_holdings(transaction_path)
    # 拿到股價、匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx = fetch_month_end_fx(all_months)

    # 計算各持有者、各股票月末資產 = 持股數 * 股價 * 匯率(若為美股)
    detail = {}
    for owner, df in [('Lo', monthly_Lo), ('Sean', monthly_Sean)]:
        df_val = df.multiply(price_df).copy()
        # 美股轉匯
        us_mask = [c.endswith('US') for c in df.columns]
        df_val.loc[:, us_mask] = df_val.loc[:, us_mask].multiply(fx, axis=0)
        detail[owner] = df_val
    # 共同持股各拆一半
    df_joint = monthly_SeanLo.multiply(price_df)
    df_joint.loc[:, [c.endswith('US') for c in df_joint.columns]] = \
        df_joint.loc[:, [c.endswith('US') for c in df_joint.columns]].multiply(fx, axis=0)
    df_joint = df_joint.divide(2)
    detail['Sean/Lo'] = df_joint

    # 彙總每月各者總資產
    summary = pd.DataFrame(index=all_months)
    for owner in ['Lo', 'Sean', 'Sean/Lo']:
        summary[owner] = detail[owner].sum(axis=1)
    # 總和列出 Lo + Sean + Sean/Lo
    summary['Total'] = summary['Lo'] + summary['Sean'] + summary['Sean/Lo']

    # 合併 detail 多層 index: level0 Owner, level1 Code
    detail_df = pd.concat(detail, axis=1)
    # 回傳 summary_df, detail_df
    return summary, detail_df
```
