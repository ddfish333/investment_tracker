#transaction_parser.py
import pandas as pd
from modules.time_utils import to_period_index
from modules.fx_fetcher import fetch_monthly_fx


def parse_transaction(filepath_main, filepath_ownership):
    """
    將交易主表與出資比例表合併，回傳每位出資者的拆分交易紀錄。
    主表與比例表需存在 "交易編號" 欄位。
    """
    # 讀取資料
    main_df = pd.read_excel(filepath_main, sheet_name="交易主表")
    ownership_df = pd.read_excel(filepath_ownership, sheet_name="出資比例")

    # 合併兩張表（多對一），每筆交易依出資比例拆為多人紀錄
    merged = main_df.merge(ownership_df, on="交易編號", how="left")

    # 拆出每位出資者的股數與成本
    merged["股數"] = merged["買賣股數"] * merged["出資比例"]
    merged["成本"] = merged["股數"] * merged["價格"] + merged["手續費"] + merged["稅金"]

    # 加入月份欄位供後續聚合
    merged["交易日期"] = pd.to_datetime(merged["交易日期"])
    merged["月份"] = to_period_index(merged["交易日期"])

    # 匯率轉換為 TWD：取得匯率快照，補值處理（補前補後）
    months = merged["月份"].unique()
    fx_df = fetch_monthly_fx(months=months)
    fx_df = fx_df.ffill().bfill()

    # 合併匯率資料
    merged = merged.merge(fx_df, left_on="月份", right_index=True, how="left")

    # 換算為「等值台幣成本」
    merged["成本_等值台幣"] = merged.apply(
        lambda row: row["成本"] if row["幣別"] == "TWD" else row["成本"] * row.get(row["幣別"], 1),
        axis=1
    )

    # 重組欄位順序
    cols = [
        "交易編號", "交易日期", "月份", "股票代號", "出資者", "股數", "成本", "成本_等值台幣",
        "幣別", "價格", "手續費", "稅金", "動作", "資產名稱", "台股/美股", "備註"
    ]
    return merged[cols]
