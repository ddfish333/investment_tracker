import streamlit as st
import pandas as pd
import logging
import os
import yfinance as yf
from modules.time_utils import to_period_index
from datetime import datetime

# --- 設定快照檔案路徑與預設匯率 ---
FX_SNAPSHOT_PATH = "data/monthly_fx_history.parquet"
DEFAULT_RATE = 30.0

# --- 主功能：搶取每月 USD/TWD 匯率（中位數） ---
def fetch_monthly_fx(months):
    months = to_period_index(months)
    unique_months = sorted(set(months))

    # 讀取已存在快照
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
    else:
        fx_df = pd.DataFrame()

    fx_df = fx_df.copy()
    if "資料日期" not in fx_df.columns:
        fx_df["資料日期"] = pd.NaT
    if "USD" not in fx_df.columns:
        fx_df["USD"] = pd.NA
    if "來源" not in fx_df.columns:
        fx_df["來源"] = pd.NA

    today = pd.Timestamp.today().normalize()

    for month in unique_months:
        if month in fx_df.index and pd.notna(fx_df.at[month, "USD"]):
            continue

        try:
            start_date = month.to_timestamp(how="start")
            end_date = month.to_timestamp(how="end") + pd.Timedelta(days=1)

            data = yf.download("TWD=X", start=start_date, end=end_date, progress=False)
            close = data["Close"].dropna()
            if not close.empty:
                median_rate = round(float(close.median()), 4)
                fx_df.at[month, "USD"] = median_rate
                fx_df.at[month, "來源"] = "Yahoo Finance"
                fx_df.at[month, "資料日期"] = today
                logging.info(f"✅ 匯率 @ {month} ➔ {median_rate}")
                continue
        except Exception as e:
            logging.warning(f"❌ 無法下載 {month} 匯率：{e}")

        fx_df.at[month, "USD"] = DEFAULT_RATE
        fx_df.at[month, "來源"] = "預設值"
        fx_df.at[month, "資料日期"] = today
        logging.warning(f"⚠️ {month} 匯率設為預設值 {DEFAULT_RATE}")

    fx_df["TWD"] = 1.0
    fx_df["USD"] = pd.to_numeric(fx_df["USD"], errors="coerce")
    fx_df["資料日期"] = pd.to_datetime(fx_df["資料日期"], errors="coerce")
    fx_df = fx_df.convert_dtypes()
    fx_df = fx_df.sort_index()

    os.makedirs(os.path.dirname(FX_SNAPSHOT_PATH), exist_ok=True)
    fx_df.to_parquet(FX_SNAPSHOT_PATH)
    logging.info(f"📂 匯率快照已儲存至：{FX_SNAPSHOT_PATH}")

    return fx_df.loc[unique_months]

# --- 擴充功能：傳入某月份（文字格式），回傳匯率與資料日期 ---
def get_fx_rate_for(month_str, fallback=DEFAULT_RATE):
    df = fetch_monthly_fx([month_str])
    row = df.iloc[0]
    return row["USD"], row["資料日期"].strftime("%Y-%m-%d") if pd.notna(row["資料日期"]) else "未知"

# --- 擴充功能：直接取得快照中最新匯率（不重抓） ---
def get_latest_fx_rate():
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH).sort_index()
        latest = fx_df.iloc[-1]
        return latest["USD"], latest["資料日期"].strftime("%Y-%m-%d")
    return DEFAULT_RATE, "未知"

# --- 擴充功能：輸入特定日期（yyyy-mm-dd），自動取當月匯率 ---
def get_fx_rate_on_date(date_str, fallback=DEFAULT_RATE):
    period_str = pd.to_datetime(date_str).strftime("%Y-%m")
    return get_fx_rate_for(period_str, fallback)

def get_fx_rate():
    """簡化主程式用法：直接取得今天的匯率與日期"""
    return get_fx_rate_on_date(datetime.today().strftime("%Y-%m-%d"))

# 將 snapshot 中的匯率資料轉為 long format（方便依月份與幣別查詢）
# 回傳值為 Series，index 為 (月份, 幣別)，value 為匯率
# 用於金額轉換時能直接用 fx.loc[(month, currency)] 查出匯率
def load_fx_rates():
    fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
    fx_df.index = to_period_index(fx_df.index)
    fx_long = fx_df.stack().reset_index()
    fx_long.columns = ["Month", "Currency", "Rate"]
    return fx_long.set_index(["Month", "Currency"])["Rate"]