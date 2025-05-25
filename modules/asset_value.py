import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    """
    計算 Sean、Lo 與總資產價值，並拆分 joint 持股到各自名下。
    回傳：
      - summary_df: pd.DataFrame(index=月份, columns=['Lo','Sean','Total'])
      - detail_df: pd.DataFrame(columns=MultiIndex[(code, owner)])
    """
    # 解析每月持股
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, _, _ = \
        parse_monthly_holdings(transaction_path)

    # 取得價格與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 初始化 summary
    summary_df = pd.DataFrame(index=all_months, columns=['Lo', 'Sean']).fillna(0.0)

    # detail: {code: DataFrame({'Lo':, 'Sean':})}
    detail = {}
    for code in all_codes:
        price = price_df[code]
        # 台股不換算匯率，美股需乘上匯率
        fx = fx_series if str(code).endswith('US') else 1.0

        # 各自持股與 joint 持股平分
        share_lo = monthly_Lo[code] + monthly_SeanLo[code] / 2.0
        share_sean = monthly_Sean[code] + monthly_SeanLo[code] / 2.0

        # 計算價值
        val_lo = share_lo * price * fx
        val_sean = share_sean * price * fx

        # 累加到 summary
        summary_df['Lo'] += val_lo
        summary_df['Sean'] += val_sean

        # 個股明細
        detail[code] = pd.DataFrame({
            'Lo': val_lo,
            'Sean': val_sean,
        }, index=all_months)

    # 總資產
    summary_df['Total'] = summary_df['Lo'] + summary_df['Sean']

    # 合併個股 detail
    detail_df = pd.concat(detail, axis=1)

    return summary_df, detail_df
