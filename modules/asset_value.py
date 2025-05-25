import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings


def calculate_monthly_asset_value(transaction_path):
    """
    計算每月資產價值並分拆 joint (Sean/Lo) 一半至 Sean 與 Lo，
    並附加總資產欄位。

    回傳:
    - summary_df: 每月總資產 DataFrame (index=月份, columns=[Lo, Sean, Total])
    - detail_df: 每月各股票各人資產 DataFrame (index=月份, columns=MultiIndex[代碼, 所有人])
    """
    # 取得每月持股數 (Lo, Sean, joint)
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, *_ = parse_monthly_holdings(transaction_path)

    # 取得月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 構建 detail DataFrame, 使用 MultiIndex (code, owner)
    owners = ['Lo', 'Sean']
    detail_cols = pd.MultiIndex.from_product([all_codes, owners], names=['code', 'owner'])
    detail_df = pd.DataFrame(0.0, index=all_months, columns=detail_cols)

    # 計算各人資產
    for code in all_codes:
        # 持股拆分: joint 平分到兩人
        shares_lo = monthly_Lo[code] + monthly_SeanLo[code] / 2
        shares_sean = monthly_Sean[code] + monthly_SeanLo[code] / 2

        # 計算資產 (台股不換算匯率，美股需乘匯率)
        is_us = str(code).endswith("US")
        price = price_df[code]
        if is_us:
            assets_lo = shares_lo * price * fx_series
            assets_sean = shares_sean * price * fx_series
        else:
            assets_lo = shares_lo * price
            assets_sean = shares_sean * price

        detail_df[(code, 'Lo')] = assets_lo
        detail_df[(code, 'Sean')] = assets_sean

    # 計算 summary: 各人與總資產
    summary_df = detail_df.sum(axis=1, level='owner')
    summary_df['Total'] = summary_df.sum(axis=1)

    return summary_df, detail_df
