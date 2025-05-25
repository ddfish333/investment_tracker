import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings


def calculate_monthly_asset_value(transaction_path):
    """
    计算每月资产价值（以台币计价），返回一个DataFrame，索引为月份，列为 ['Lo', 'Sean']
    """
    # 解析每月持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, raw_df, color_map = \
        parse_monthly_holdings(transaction_path)

    # 拉取月末价格和汇率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)  # 美股美元兑台币

    # 初始化资产表
    result = pd.DataFrame(index=all_months, columns=["Lo", "Sean"]).fillna(0)

    # 累加每月资产
    for month in all_months:
        for code in all_codes:
            # Lo 持股
            lo_shares = monthly_Lo.at[month, code]
            # Sean 个人持股
            sean_shares = monthly_Sean.at[month, code]
            # Sean/Lo 共同持股也算到 Sean
            share_lo_sean = monthly_SeanLo.at[month, code]

            total_shares = lo_shares + sean_shares + share_lo_sean
            if total_shares == 0:
                continue

            # 取得当月价格
            price = price_df.at[month, code]
            # 如果是美股，需要乘以汇率
            is_us = raw_df.loc[raw_df['股票代號'] == code, '台股/美股'].eq('美股').any()
            if is_us:
                price = price * fx_series.at[month]

            # 累计资产
            if lo_shares:
                result.at[month, 'Lo'] += lo_shares * price
            if sean_shares:
                result.at[month, 'Sean'] += sean_shares * price
            if share_lo_sean:
                result.at[month, 'Sean'] += share_lo_sean * price

    return result
