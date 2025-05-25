# modules/asset_value.py
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股，返回 Lo, Sean, Sean/Lo 各自的持股表，以及代碼列表與月份列表
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, raw_df, color_map = \
        parse_monthly_holdings(transaction_path)

    # 組合持股字典
    monthly_holdings = {
        "Lo": monthly_Lo,
        "Sean": monthly_Sean,
        "Sean/Lo": monthly_SeanLo,
    }

    # 過濾出有實際持股的代碼
    valid_codes = set()
    for df in monthly_holdings.values():
        valid_codes.update(df.loc[:, (df != 0).any(axis=0)].columns)
    all_codes = sorted(map(str, valid_codes))

    # 取得月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)  # Index 為月份

    # 初始化結果表
    result = pd.DataFrame(index=all_months, columns=["Sean", "Lo"]).fillna(0)

    # 計算各人資產
    for month in all_months:
        for owner, df in monthly_holdings.items():
            for code in all_codes:
                shares = df.at[month, code] if code in df.columns else 0
                price = price_df.at[month, code] if code in price_df.columns else 0
                # 美股需要換匯
                fx = fx_series.at[month] if str(code).endswith("US") and month in fx_series.index else 1
                total_value = shares * price * fx

                if owner == "Sean":
                    result.at[month, "Sean"] += total_value
                elif owner == "Lo":
                    result.at[month, "Lo"] += total_value
                else:  # Sean/Lo
                    result.at[month, "Sean"] += total_value / 2
                    result.at[month, "Lo"] += total_value / 2

    return result
