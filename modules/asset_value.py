
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx

def calculate_monthly_asset_value(transaction_file):
    # 取得每月持股數據（回傳 dict: Sean, Lo, Sean/Lo）
    holding_dict = parse_monthly_holdings(transaction_file)

    # 所有月份
    all_months = holding_dict["Sean"].index
    all_codes = set()
    for df in holding_dict.values():
        all_codes.update(df.columns)

    # 取得每月收盤價（台股 + 美股）與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_df = fetch_month_end_fx(all_months)  # 匯率資料：index=月份, value=USD→TWD

    # 初始化結果表
    result = pd.DataFrame(index=all_months, columns=["Sean", "Lo"])
    result = result.fillna(0)

    for month in all_months:
        fx = fx_df.get(month, 30)  # 預設匯率 fallback

        for source, weight in [("Sean", 1.0), ("Lo", 1.0), ("Sean/Lo", 0.5)]:
            if source not in holding_dict:
                continue
            df = holding_dict[source]
            if month not in df.index:
                continue
            row = df.loc[month]
            for code, qty in row.items():
                price = price_df.at[month, code] if code in price_df.columns else 0
                if isinstance(code, int) or (isinstance(code, str) and code.endswith(".TW")):
                    twd_value = qty * price * weight
                else:
                    twd_value = qty * price * fx * weight
                if source in ["Sean", "Sean/Lo"]:
                    result.at[month, "Sean"] += twd_value
                if source in ["Lo", "Sean/Lo"]:
                    result.at[month, "Lo"] += twd_value

    return result
