# modules/asset_value.py
```python
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    """
    計算每月各持有人(Lo, Sean, Sean/Lo)及總資產價值。
    回傳 summary_df (Lo, Sean, Sean/Lo, Total) 及 detail_df (多層 column)
    """
    # 解析持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months = parse_monthly_holdings(transaction_path)

    # 取每月股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 計算各者資產
    detail = {}
    for owner, df in [('Lo', monthly_Lo), ('Sean', monthly_Sean)]:
        df_val = df.multiply(price_df)
        # 美股乘匯率
        us_mask = [code.endswith('US') for code in df.columns]
        if any(us_mask):
            df_val.loc[:, us_mask] = df_val.loc[:, us_mask].multiply(fx_series, axis=0)
        detail[owner] = df_val

    # 合資按半分配
    joint_val = monthly_SeanLo.multiply(price_df)
    us_mask = [code.endswith('US') for code in joint_val.columns]
    if any(us_mask):
        joint_val.loc[:, us_mask] = joint_val.loc[:, us_mask].multiply(fx_series, axis=0)
    detail['Sean/Lo'] = joint_val.divide(2)

    # summary 資料框
    summary_df = pd.DataFrame(index=all_months)
    for owner in ['Lo', 'Sean', 'Sean/Lo']:
        summary_df[owner] = detail[owner].sum(axis=1)
    # 總資產
    summary_df['Total'] = summary_df[['Lo', 'Sean', 'Sean/Lo']].sum(axis=1)

    # detail 多層 column
    detail_df = pd.concat(detail, axis=1)
    detail_df.columns.names = ['Owner', 'Code']

    return summary_df, detail_df
```  
