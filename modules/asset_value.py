import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股：Lo、Sean、共同持股，以及所有代碼、所有月份、原始交易資料
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, raw_df, _ = parse_monthly_holdings(transaction_path)

    # 獲取月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 判定是否為美股
    def is_us_stock(code):
        try:
            return raw_df.loc[raw_df['股票代號'] == code, '台股/美股'].iloc[0] == '美股'
        except Exception:
            return str(code).upper().endswith('US')

    # 轉換價格為台幣：美股 * 匯率，台股保留當前價
    price_twd = price_df.copy()
    for code in price_twd.columns:
        if is_us_stock(code):
            price_twd[code] = price_twd[code] * fx_series

    # 建立結果表：Lo 與 Sean
    result = pd.DataFrame(index=all_months, columns=['Lo', 'Sean']).fillna(0)

    # 逐月計算資產價值
    for month in all_months:
        prices = price_twd.loc[month]
        lo_hold = monthly_Lo.loc[month]
        sean_hold = monthly_Sean.loc[month]
        joint_hold = monthly_SeanLo.loc[month]

        lo_val = (lo_hold * prices).sum()
        sean_val = (sean_hold * prices).sum()
        joint_val = (joint_hold * prices).sum()

        result.at[month, 'Lo'] = lo_val + joint_val
        result.at[month, 'Sean'] = sean_val + joint_val

    return result
