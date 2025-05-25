import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, _, _ = parse_monthly_holdings(transaction_path)

    # 取得每月收盤價及匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx = fetch_month_end_fx(all_months)

    # 建立 detail DataFrame: 多層欄位 (code, owner)
    detail_frames = []
    for code in all_codes:
        # 判斷是否為美股
        is_us = str(code).endswith("US")
        rate = fx if is_us else 1.0

        # 計算各自價值
        v_lo = monthly_Lo[code] * price_df[code] * rate
        v_sean = monthly_Sean[code] * price_df[code] * rate
        v_joint = monthly_SeanLo[code] * price_df[code] * rate

        df = pd.DataFrame({
            (code, 'Lo'): v_lo,
            (code, 'Sean'): v_sean,
            (code, 'Sean/Lo'): v_joint,
        }, index=all_months)
        detail_frames.append(df)

    # 合併所有個股明細
    detail_df = pd.concat(detail_frames, axis=1).sort_index(axis=1)

    # 計算總表: 各月總資產
    summary_df = pd.DataFrame(
        {
            'Lo': detail_df.xs('Lo', axis=1, level=1).sum(axis=1),
            'Sean': detail_df.xs('Sean', axis=1, level=1).sum(axis=1),
            'Sean/Lo': detail_df.xs('Sean/Lo', axis=1, level=1).sum(axis=1),
        }
    )
    summary_df['Total'] = summary_df.sum(axis=1)

    return summary_df, detail_df
