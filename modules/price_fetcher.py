```python
# modules/asset_value.py
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    """
    計算並回傳：
      - summary_df (index 為月份，欄位為 Lo, Sean): 各自持股台幣價值總和
      - detail_df (index 為月份，MultiIndex 欄位 (code, owner)): 每支股票、每個月、每人的台幣持股價值
    """
    # 解析每月持股，支援返回多個值（取前五）
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, *_ = parse_monthly_holdings(transaction_path)

    # 抓取月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)  # index: all_months, columns: all_codes
    fx_series = fetch_month_end_fx(all_months)               # index: all_months

    # 計算各持股者、各股票的台幣價值
    detail_parts = []
    for owner, df in zip(["Lo", "Sean", "Joint"], [monthly_Lo, monthly_Sean, monthly_SeanLo]):
        # 股價乘以持股數
        value = df * price_df
        # 美股乘以匯率
        us_mask = [str(code).endswith("US") for code in all_codes]
        if any(us_mask):
            value.loc[:, us_mask] = value.loc[:, us_mask].multiply(fx_series, axis=0)
        # 建立 MultiIndex 欄位
        cols = pd.MultiIndex.from_product([all_codes, [owner]])
        value.columns = cols
        detail_parts.append(value)

    # 合併所有 owner 的明細
    detail_df = pd.concat(detail_parts, axis=1).sort_index(axis=1)

    # 計算 summary：各自擁有的台幣資產
    half_joint = detail_df.xs('Joint', axis=1, level=1) / 2
    lo_assets = detail_df.xs('Lo', axis=1, level=1) + half_joint
    sean_assets = detail_df.xs('Sean', axis=1, level=1) + half_joint
    summary_df = pd.DataFrame({
        'Lo': lo_assets.sum(axis=1),
        'Sean': sean_assets.sum(axis=1)
    }, index=all_months)

    return summary_df, detail_df
```
