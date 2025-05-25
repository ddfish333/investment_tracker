import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    # 解析持股資料
    monthly_holdings, *_ = parse_monthly_holdings(transaction_path)
    all_codes = sorted(monthly_holdings.keys())
    all_months = next(iter(monthly_holdings.values())).index

    # 取得月末價格與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 初始化資產表（Summary）
    summary = pd.DataFrame(index=all_months, columns=["Lo", "Sean"]).fillna(0)
    # 初始化各股票明細表（Detail），三層索引: 月份, 股票代號, 所有人
    detail = pd.DataFrame(
        index=all_months,
        columns=pd.MultiIndex.from_product([all_codes, ["Lo", "Sean", "Joint"]]),
    ).fillna(0)

    # 計算每月每支股票各自資產
    for month in all_months:
        for owner, df in monthly_holdings.items():
            for code in all_codes:
                shares = df.at[month, code]
                price = price_df.at[month, code]
                # 美股乘以匯率
                if str(code).endswith("US"):
                    price *= fx_series.at[month]
                value = shares * price

                # 累加到 Summary
                summary.at[month, owner] += value
                # 記錄到 Detail
                col = owner if owner in ["Lo", "Sean"] else "Joint"
                detail.at[month, (code, col)] = value

    return summary, detail
