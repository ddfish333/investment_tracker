# modules/asset_value.py
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx

def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股字典：返回三個 DataFrame: Lo, Sean, SeanLo，及所有股票代碼與月份索引
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months = parse_monthly_holdings(transaction_path)

    # 取得每月價格與匯率（模擬或 API）
    price_df = fetch_month_end_prices(all_codes, all_months)  # index: all_months, columns: codes
    fx_series = fetch_month_end_fx(all_months)               # index: all_months

    # 三層索引明細表：月份 x (代號, 持有人)
    detail = {}
    for owner, shares in zip(['Lo', 'Sean', 'Sean/Lo'], [monthly_Lo, monthly_Sean, monthly_SeanLo]):
        # 個股市值 = 持股量 * 價格 * 匯率 (台股匯率=1)
        # 判斷台股或美股
        is_us = [str(code).endswith('US') for code in all_codes]
        rate = fx_series.where(is_us, other=1.0)
        df_val = shares * price_df * rate.values[:, None]
        detail[owner] = df_val

    # 合併成多層 DataFrame: columns: (code, owner)
    detail_df = pd.concat(detail, axis=1)
    detail_df.columns.names = ['Code', 'Owner']

    # 彙總總資產：按持有人合計所有股票
    summary_df = detail_df.sum(axis=1, level='Owner')
    summary_df['Total'] = summary_df.sum(axis=1)

    return summary_df, detail_df
