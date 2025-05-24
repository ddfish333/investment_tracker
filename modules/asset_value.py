import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    monthly_holdings = parse_monthly_holdings(transaction_path)
    all_months = next(iter(monthly_holdings.values())).index

    # 取得所有股票代號
    all_codes = sorted(set().union(*[df.columns for df in monthly_holdings.values()]))

    # 取得月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)  # 這裡用 series 來表示匯率資料

    # 初始化資產表
    result = pd.DataFrame(index=all_months, columns=["Sean", "Lo"]).fillna(0)

    for month in all_months:
        for owner, df in monthly_holdings.items():
            total = 0
            for code in df.columns:
                shares = df.at[month, code]
                price = price_df.at[month, code] if code in price_df.columns else 0
                currency = "USD" if code.endswith("US") else "TWD"
                fx = fx_series.at[month] if currency == "USD" else 1
                total += shares * price * fx

            if owner == "Sean":
                result.at[month, "Sean"] += total
            elif owner == "Lo":
                result.at[month, "Lo"] += total
            elif owner == "Sean/Lo":
                result.at[month, "Sean"] += total / 2
                result.at[month, "Lo"] += total / 2

    return result
