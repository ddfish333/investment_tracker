# -*- coding: utf-8 -*-
import os
import platform
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from datetime import datetime
from modules.asset_value import calculate_monthly_asset_value
from modules.cash_parser import parse_cash_balances, parse_cash_detail
from modules.time_utils import to_period_index  # ✅ 導入時間處理工具
from config import TRANSACTION_FILE, FX_SNAPSHOT_PATH

# --- Streamlit Page Setup ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 設定中文字體（根據作業系統自動調整）
if platform.system() == "Darwin":  # macOS
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

# --- 計算資產 ---
summary_df, raw_df, stock_price_df, stock_value_df, fx_df, all_months = calculate_monthly_asset_value(TRANSACTION_FILE)

# --- 銀行帳戶資產 ---
cash_summary = parse_cash_balances()
cash_latest = cash_summary.iloc[-1]

summary_df_display = summary_df.join(cash_summary, how="left").fillna(0)
owners = [col for col in summary_df.columns if not col.endswith("_TW_STOCK") and not col.endswith("_US_STOCK") and not col.endswith("_TWD_CASH") and not col.endswith("_USD_CASH") and not col.endswith("_TOTAL") and col != "Total"]
for owner in owners:
    summary_df_display[f"{owner}_TOTAL"] = (
        summary_df_display.get(f"{owner}_TW_STOCK", 0)
        + summary_df_display.get(f"{owner}_US_STOCK", 0)
        + summary_df_display.get(f"{owner}_TWD_CASH", 0)
        + summary_df_display.get(f"{owner}_USD_CASH", 0)
    )

# --- 建立 total_asset_df：每人每資產類型（個股/現金）為欄位的 DataFrame ---
total_asset_df = pd.concat([stock_value_df, cash_summary], axis=1).fillna(0)

# --- 顯示資產摘要 ---
st.title(f"\U0001F4B8 每月資產價值")
latest = summary_df_display.iloc[-1]
for owner in owners:
    tw_stock = latest.get(f"{owner}_TW_STOCK", 0)
    us_stock = latest.get(f"{owner}_US_STOCK", 0)
    tw_cash = latest.get(f"{owner}_TWD_CASH", 0)
    us_cash = latest.get(f"{owner}_USD_CASH", 0)
    total = tw_stock + us_stock + tw_cash + us_cash
    st.markdown(f"**{owner}**：TWD {total:,.0f}（台股 TWD {tw_stock:,.0f}／美股 TWD {us_stock:,.0f}／台幣現金 TWD {tw_cash:,.0f}／美金現金 TWD {us_cash:,.0f}）")

st.markdown(f"**Sean&Lo**：TWD {summary_df['Total'].iloc[-1] + cash_latest.sum():,.0f}")

# --- 總資產跑動 ---
st.subheader("Sean&Lo總資產")
summary_df_display.index = summary_df_display.index.astype(str)
default_selection = ['Sean', 'Lo', 'Total']
selected_lines = st.multiselect("請選擇要顯示的資產線", options=default_selection, default=default_selection)
if selected_lines:
    st.line_chart(summary_df_display[selected_lines])
else:
    st.info("請至少選擇一條資產線來顯示。")

# --- 各類資產跑動詳細（含股票與現金） ---
st.subheader("各類資產跑動詳細（含股票與現金）")
for owner in ["Sean", "Lo"]:
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

# --- 額外資訊表格 ---
st.subheader("📊 整合後每月資產資料表")
summary_df_display = summary_df_display[::-1]
st.dataframe(summary_df_display.style.format("{:,.0f}"))

# --- 美金匯率變化 ---
st.subheader("📈 美金匯率變化")
try:
    fx_snapshot = pd.read_parquet(FX_SNAPSHOT_PATH)
    if isinstance(fx_snapshot.index, pd.PeriodIndex):
        fx_snapshot.index = fx_snapshot.index.to_timestamp()
    usd_rate = fx_snapshot["USD"].sort_index(ascending=False)
    st.line_chart(usd_rate.rename("USD匯率"))
except Exception as e:
    st.error(f"❌ 無法讀取匯率資料：{e}")
