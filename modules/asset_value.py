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
    # 解析持股，回傳 monthly_Lo, monthly_Sean, monthly_SeanLo, 所有代碼及月份
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months = parse_monthly_holdings(transaction_path)

    # 取得股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    detail = {}
    # 分別計算 Lo 與 Sean 權益
    for owner, df in [('Lo', monthly_Lo), ('Sean', monthly_Sean)]:
        val = df.multiply(price_df)
        # 美股轉換匯率 (假設代碼以 'US' 結尾)
        us = [col.endswith('US') for col in df.columns]
        if any(us):
            val.loc[:, us] = val.loc[:, us].multiply(fx_series, axis=0)
        detail[owner] = val

    # 合資部分 (Sean/Lo) 平分
    joint = monthly_SeanLo.multiply(price_df)
    us = [col.endswith('US') for col in monthly_SeanLo.columns]
    if any(us):
        joint.loc[:, us] = joint.loc[:, us].multiply(fx_series, axis=0)
    detail['Sean/Lo'] = joint.divide(2)

    # 組出 summary
    summary_df = pd.DataFrame({owner: detail[owner].sum(axis=1) for owner in detail})
    summary_df['Total'] = summary_df.sum(axis=1)

    # 組出 detail 多層 columns
    detail_df = pd.concat(detail, axis=1)
    detail_df.columns.names = ['Owner', 'Code']

    return summary_df, detail_df
```