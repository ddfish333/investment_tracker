import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx

def calculate_monthly_asset_value(transaction_path):
    # 解析每月持股：返回三個 DataFrame (Lo, Sean, Joint) 與 codes、months
    monthly_Lo, monthly_Sean, monthly_Joint, codes, months, raw_df = parse_monthly_holdings(transaction_path)

    # 從交易資料推斷每支股票幣別
    code_currency = raw_df.groupby("股票代號")["幣別"].last().to_dict()

    # 取得價格與匯率
    price_df = fetch_month_end_prices(codes, months)
    fx_ser = fetch_month_end_fx(months)

    def convert_to_twd(holding_df):
        val_df = pd.DataFrame(index=months, columns=codes)
        for code in codes:
            currency = code_currency.get(code, "TWD")
            prices = price_df[code]
            if currency == "USD":
                val_df[code] = holding_df[code] * prices * fx_ser
            else:
                val_df[code] = holding_df[code] * prices
        return val_df.astype(float)

    # 分別轉換為台幣資產
    val_Lo = convert_to_twd(monthly_Lo)
    val_Sean = convert_to_twd(monthly_Sean)
    val_Joint = convert_to_twd(monthly_Joint)

    # 總資產表
    summary = pd.DataFrame({
        'Lo': val_Lo.sum(axis=1),
        'Sean': val_Sean.sum(axis=1),
        'Total': (val_Lo + val_Sean + val_Joint).sum(axis=1)
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
