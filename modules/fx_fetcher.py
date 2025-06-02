import streamlit as st
import pandas as pd
import logging
import os
import yfinance as yf
from modules.time_utils import to_period_index

# --- 設定快照檔案路徑與預設匯率 ---
FX_SNAPSHOT_PATH = "data/monthly_fx_history.parquet"
DEFAULT_RATE = 30.0

# --- 主功能：抓取每月 USD/TWD 匯率（中位數） ---
def fetch_monthly_fx(months):
    months = to_period_index(months)
    unique_months = sorted(set(months))

    # 讀取已存在的快照檔
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
    else:
        fx_df = pd.DataFrame(columns=["USD", "來源", "TWD"])
        fx_df.index = pd.period_range("2000-01", "2000-01", freq="M")[:0]
        fx_df.index.name = "月份"

    fx_df = fx_df.copy()
    new_data = {}

    for month in unique_months:
        if month in fx_df.index:
            continue

        try:
            start_date = month.to_timestamp(how="start")
            end_date = month.to_timestamp(how="end") + pd.Timedelta(days=1)  # ✅ 抓整月資料

            data = yf.download("TWD=X", start=start_date, end=end_date, progress=False)
            close = data["Close"].dropna()
            if not close.empty:
                median_rate = round(float(close.median()), 4)
                new_data[month] = {"USD": median_rate, "來源": "Yahoo Finance"}
                logging.info(f"✅ 匯率 @ {month} ➜ {median_rate}")
                continue
        except Exception as e:
            logging.warning(f"❌ 無法下載 {month} 匯率：{e}")

        logging.warning(f"⚠️ {month} 匯率設為預設值 {DEFAULT_RATE}")
        new_data[month] = {"USD": DEFAULT_RATE, "來源": "預設值"}

    # 加入新資料
    if new_data:
        new_df = pd.DataFrame.from_dict(new_data, orient="index")
        fx_df = pd.concat([fx_df, new_df])
        fx_df = fx_df.sort_index()

    # 🛠️ 強制欄位型別正確
    fx_df["TWD"] = 1.0
    fx_df["USD"] = pd.to_numeric(fx_df["USD"], errors="coerce")
    fx_df["來源"] = fx_df["來源"].astype(str)

    # 💾 儲存快照
    os.makedirs(os.path.dirname(FX_SNAPSHOT_PATH), exist_ok=True)
    fx_df.to_parquet(FX_SNAPSHOT_PATH)
    logging.info(f"💾 匯率快照已儲存至：{FX_SNAPSHOT_PATH}")

    return fx_df.loc[unique_months]

# ✅ 若要手動測試用
if __name__ == "__main__":
    test_months = pd.period_range("2023-01", "2024-12", freq="M")
    fx_df = fetch_monthly_fx(test_months)
    print(fx_df)
