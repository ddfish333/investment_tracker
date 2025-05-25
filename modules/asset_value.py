# modules/asset_value.py
import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def is_us_stock(code):
    return str(code).upper().endswith("US")


def calculate_monthly_asset_value(transaction_path):
    """
    計算每月各人 (Lo/Sean) 與總計的資產價值 (TWD)
    返回 summary_df (Lo, Sean, Total) 與 detail_df (MultiIndex: [Lo, Sean] × codes)
    """
    # 解析每月持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, _, _ = parse_monthly_holdings(transaction_path)
    # 抓取行情與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx = fetch_month_end_fx(all_months)

    # 對美股價格換算為台幣
    us = [c for c in all_codes if is_us_stock(c)]
    if us:
        price_df.loc[:, us] = price_df[us].mul(fx, axis=0)

    # 計算資產 (Lo + half of Joint, Sean + half of Joint)
    asset_Lo = monthly_Lo.mul(price_df).add(monthly_SeanLo.mul(price_df).div(2), fill_value=0)
    asset_Sean = monthly_Sean.mul(price_df).add(monthly_SeanLo.mul(price_df).div(2), fill_value=0)

    # Detail: 每支股票每月 Lo/Sean 資產
    detail_df = pd.concat(
        {"Lo": asset_Lo, "Sean": asset_Sean},
        axis=1
    )
    detail_df.columns.names = ["Owner", "Code"]

    # Summary: 各人與總資產
    summary_df = pd.DataFrame({
        "Lo": detail_df.xs("Lo", level="Owner", axis=1).sum(axis=1),
        "Sean": detail_df.xs("Sean", level="Owner", axis=1).sum(axis=1)
    })
    summary_df["Total"] = summary_df["Lo"] + summary_df["Sean"]

    return summary_df, detail_df

