import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_monthly_prices_batch, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股：返回三個 DataFrame (Lo, Sean, Joint) 與 codes、months
    monthly_Lo, monthly_Sean, monthly_Joint, codes, months, raw_df = parse_monthly_holdings(transaction_path)


    # 抓取 API 月末股價與匯率
    price_df = fetch_monthly_prices_batch(codes, months)
    fx_ser = fetch_month_end_fx(months)

    # 計算各自資產（依原始幣別調整）
    val_Lo = monthly_Lo.mul(price_df).mul(fx_ser, axis=0)
    val_Sean = monthly_Sean.mul(price_df).mul(fx_ser, axis=0)
    val_Joint = monthly_Joint.mul(price_df).mul(fx_ser, axis=0)

    # 總覽 DataFrame
    summary = pd.DataFrame({
        'Lo': val_Lo.sum(axis=1),
        'Sean': val_Sean.sum(axis=1),
        'Total': (val_Lo + val_Sean + val_Joint).sum(axis=1),
        'Joint': val_Joint.sum(axis=1)  # 額外加回 Joint 欄，供後續調整
    })

    # 詳細 MultiIndex DataFrame (Code, Owner)
    detail = pd.concat([
        val_Lo.add_suffix('_Lo'),
        val_Sean.add_suffix('_Sean'),
        val_Joint.add_suffix('_Joint')
    ], axis=1)
    detail.columns = pd.MultiIndex.from_tuples([
        (col.split('_')[0], col.split('_')[1]) for col in detail.columns
    ], names=['Code', 'Owner'])

    return summary, detail
