import pandas as pd
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_monthly_prices_batch, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    # 讀取並解析每月持股
    monthly_Lo, monthly_Sean, monthly_Joint, codes, months, raw_df = parse_monthly_holdings(transaction_path)

    # 將股票代碼轉為 Yahoo Finance 格式
    def fix_yf_code(row):
        code = str(row["股票代號"]).strip()
        market = str(row["台股/美股"]).strip()
        return code + ".TW" if market == "台股" else code

    # 建立股票代碼對照表（原始 ➝ Yahoo）
    yf_code_df = raw_df[["股票代號", "台股/美股"]].drop_duplicates()
    yf_code_df["Yahoo代碼"] = yf_code_df.apply(fix_yf_code, axis=1)
    code_map = dict(zip(yf_code_df["股票代號"], yf_code_df["Yahoo代碼"]))
    codes = [code_map.get(c, c) for c in codes]

    # ➤ 將每月持股欄位改為 Yahoo 代碼（這是最重要的一步！）
    monthly_Lo.rename(columns=code_map, inplace=True)
    monthly_Sean.rename(columns=code_map, inplace=True)
    monthly_Joint.rename(columns=code_map, inplace=True)

    # Debug 印出查詢代碼
    print("📈 Yahoo 查詢股票代碼：", codes)

    # 抓股價與匯率
    price_df = fetch_monthly_prices_batch(codes, months)
    fx_ser = fetch_month_end_fx(months)

    # 計算每人資產（以台幣計算）
    val_Lo = monthly_Lo.mul(price_df).mul(fx_ser, axis=0)
    val_Sean = monthly_Sean.mul(price_df).mul(fx_ser, axis=0)
    val_Joint = monthly_Joint.mul(price_df).mul(fx_ser, axis=0)

    # 總覽表
    summary = pd.DataFrame({
        'Sean': val_Sean.sum(axis=1),
        'Lo': val_Lo.sum(axis=1),
        'Joint': val_Joint.sum(axis=1),
        'Total': (val_Lo + val_Sean + val_Joint).sum(axis=1)
    })

    # MultiIndex 詳細表（每月每人每股）
    detail = pd.concat([
        val_Lo.add_suffix('_Lo'),
        val_Sean.add_suffix('_Sean'),
        val_Joint.add_suffix('_Joint')
    ], axis=1)

    detail.columns = pd.MultiIndex.from_tuples([
        (col.split('_')[0], col.split('_')[1]) for col in detail.columns
    ], names=['Code', 'Owner'])

    return summary, detail
