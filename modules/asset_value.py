import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    # 解析持股資料 (回傳 Lo, Sean, Joint 各自持股 DataFrame 以及所有代碼和月份)
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, *_ = parse_monthly_holdings(transaction_path)
    # 建立 owner->持股表 的字典
    monthly_holdings = {
        'Lo': monthly_Lo,
        'Sean': monthly_Sean,
        'Joint': monthly_SeanLo,
    }

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

                # 累加到 Summary (Joint 對應分到兩人各半)
                if owner == 'Joint':
                    summary.at[month, 'Lo'] += value / 2
                    summary.at[month, 'Sean'] += value / 2
                else:
                    summary.at[month, owner] += value

                # 記錄到 Detail
                detail.at[month, (code, owner)] = value

    return summary, detail
