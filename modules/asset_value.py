import pandas as pd
from modules.holding_parser import parse_monthly_holdings  # returns (Lo_df, Sean_df, Joint_df, codes, months)
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def calculate_monthly_asset_value(transaction_path):
    """
    計算每月各家 (Lo, Sean, Joint) 資產
    回傳兩個 DataFrame:
      - summary_df: index=month, columns=['Lo','Sean','Total']
      - detail_df: MultiIndex columns=(Code, Owner) with每股資產 (TWD)
    """
    # 1) 解析每月持股
    monthly_Lo, monthly_Sean, monthly_Joint, codes, months = parse_monthly_holdings(transaction_path)

    # 2) 取得每月股價與匯率
    price_df = fetch_month_end_prices(codes, months)
    fx_ser = fetch_month_end_fx(months)

    # 3) 計算每家資產 (USD張數 x USD價格 x TWD匯率)
    val_Lo = monthly_Lo.mul(price_df).mul(fx_ser, axis=0)
    val_Sean = monthly_Sean.mul(price_df).mul(fx_ser, axis=0)
    val_Joint = monthly_Joint.mul(price_df).mul(fx_ser, axis=0)

    # 4) summary: 加總每月資產
    summary_df = pd.DataFrame({
        'Lo': val_Lo.sum(axis=1),
        'Sean': val_Sean.sum(axis=1),
        'Total': (val_Lo + val_Sean + val_Joint).sum(axis=1)
    })

    # 5) detail: 展開為 MultiIndex
    df_lo = val_Lo.add_suffix('_Lo')
    df_sean = val_Sean.add_suffix('_Sean')
    df_joint = val_Joint.add_suffix('_Joint')
    detail_df = pd.concat([df_lo, df_sean, df_joint], axis=1)
    detail_df.columns = pd.MultiIndex.from_tuples(
        [(col.split('_')[0], col.split('_')[1]) for col in detail_df.columns],
        names=['Code', 'Owner']
    )

    return summary_df, detail_df