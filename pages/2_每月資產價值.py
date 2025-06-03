#pages/2_每月資產價值.py
# -*- coding: utf-8 -*-
import os
import platform
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from datetime import datetime
from modules.asset_value import calculate_monthly_asset_value
from modules.time_utils import to_period_index
from config import TRANSACTION_FILE, CASH_ACCOUNT_FILE, FX_SNAPSHOT_PATH

# --- Streamlit Page Setup ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 設定中文字體（根據作業系統自動調整）
if platform.system() == "Darwin":
    font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
elif platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/msjh.ttc"
else:
    font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"

if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# --- 小工具函式：安全取最後一筆資料 ---
def safe_last(df, col_name):
    try:
        return df[col_name].iloc[-1]
    except (KeyError, IndexError):
        st.warning(f"⚠️ 找不到或無資料：{col_name}")
        return 0

# --- 資料計算：股票 + 現金 ---
summary_df, summary_stock_df, summary_cash_df, raw_df, stock_price_df, stock_value_df, fx_df, all_months = calculate_monthly_asset_value(
    filepath_transaction=TRANSACTION_FILE,
    filepath_cash=CASH_ACCOUNT_FILE
)

# --- 將 index 轉為字串格式以利顯示 ---
summary_df.index = summary_df.index.astype(str)

# --- 自動抓出資者名稱：只抓 base 欄位名（無底線） ---
owners = [col for col in summary_df.columns if col not in ("Total") and "_" not in col]

# --- 顯示資產摘要 ---
st.title(f"\U0001F4B8 我想和你一起慢慢變富")
latest = summary_df.iloc[-1]
for owner in owners:
    tw_stock = safe_last(summary_df, f"{owner}_TW_STOCK")
    us_stock = safe_last(summary_df, f"{owner}_US_STOCK")
    tw_cash = safe_last(summary_cash_df, f"{owner}_TWD_CASH")
    us_cash = safe_last(summary_cash_df, f"{owner}_USD_CASH")
    total = tw_stock + us_stock + tw_cash + us_cash
    st.markdown(f"**{owner}**：TWD {total:,.0f}（台股 TWD {tw_stock:,.0f}／美股 TWD {us_stock:,.0f}／台幣現金 TWD {tw_cash:,.0f}／美金現金 TWD {us_cash:,.0f}）")

st.markdown(f"**Sean&Lo**：TWD {summary_df['Total'].iloc[-1]:,.0f}")

# --- 總資產跑動（用 summary_df） ---
st.subheader("Sean&Lo總資產")
default_selection = ['Sean', 'Lo', 'Total']
selected_lines = st.multiselect("請選擇要顯示的資產線", options=default_selection, default=default_selection)
if selected_lines:
    st.line_chart(summary_df[selected_lines])
else:
    st.info("請至少選擇一條資產線來顯示。")

# --- 各類資產跑動詳細（含股票與現金） ---
st.subheader("各類資產跑動詳細(含股票與現金)")
total_asset_df = pd.concat([stock_value_df, summary_cash_df], axis=1).fillna(0)

for owner in owners:
    columns = [col for col in total_asset_df.columns if col.startswith(owner + "_")]
    df = total_asset_df[columns].copy()
    if df.empty:
        st.warning(f"找不到 {owner} 的資料")
        continue
    latest = df.iloc[-1]
    sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
    zero_codes = latest[latest == 0].index.tolist()
    df = df[sorted_codes + zero_codes]
    df.columns = [col.replace(owner + "_", "") for col in df.columns]
    df.index = df.index.astype(str)
    st.markdown(f"#### {owner} 每月資產變化（目前資產 NT${summary_df.iloc[-1].get(owner, 0):,.0f} 元）")
    st.bar_chart(df)


# --- 資料表顯示 summary ---
st.subheader("📊 整合後每月資產資料表 summary_df")
st.dataframe(summary_df[::-1].style.format("{:,.0f}"))

# --- 資料表顯示 fx ---
st.subheader("📊 整合後每月資產資料表 fx_df")
st.dataframe(fx_df[['USD']][::-1].style.format("{:.2f}"))
st.subheader("📈 美金匯率變化")
try:
    fx_snapshot = pd.read_parquet(FX_SNAPSHOT_PATH)
    if isinstance(fx_snapshot.index, pd.PeriodIndex):
        fx_snapshot.index = fx_snapshot.index.to_timestamp()
    usd_rate = fx_snapshot["USD"].sort_index(ascending=False)
    st.line_chart(usd_rate.rename("USD匯率"))
except Exception as e:
    st.error(f"❌ 無法讀取匯率資料：{e}")
