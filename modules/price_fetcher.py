import pandas as pd

def fetch_month_end_prices(codes, months):
    """
    讀取本地歷史月末股價資料，並取出指定代號與月份
    從 data/year_end_prices.xlsx 中讀取，每欄為一個股票代號，索引為月份
    """
    # 載入 Excel
    price_df = pd.read_excel(
        "data/year_end_prices.xlsx",
        index_col=0,
        parse_dates=True
    )
    # 篩選指定月份與代號
    price_df = price_df.reindex(months).astype(float)
    return price_df[codes]


def fetch_month_end_fx(months, base="USD", quote="TWD"):  # noqa: F841
    """
    讀取本地歷史匯率資料（USD/TWD），並取出指定月份
    從 data/fx_rates.csv 或 Excel 中讀取，索引為月份，值為匯率
    """
    # 載入 Excel 或 CSV
    fx_df = pd.read_excel(
        "data/fx_rates.xlsx",
        index_col=0,
        parse_dates=True
    )
    fx_series = fx_df["USD/TWD"].reindex(months).astype(float)
    return fx_series
