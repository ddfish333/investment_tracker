# 9_fx_debug.py

import streamlit as st
import pandas as pd
from modules.fx_fetcher import fetch_monthly_fx

# --- 頁面設定 ---
st.set_page_config(page_title="匯率除錯", layout="wide")

# --- 日期範圍選擇器 ---
st.title("🧪 匯率資料除錯（含 TWD = 1.0）")

start_month = st.selectbox("開始月份", pd.date_range("2019-01", "2025-12", freq="MS").strftime("%Y-%m"), index=48)
end_month = st.selectbox("結束月份", pd.date_range("2019-01", "2025-12", freq="MS").strftime("%Y-%m"), index=65)

if start_month > end_month:
    st.warning("⚠️ 結束月份不能早於開始月份")
else:
    months = pd.period_range(start=start_month, end=end_month, freq="M")
    fx_df = fetch_monthly_fx(months)

    st.markdown("### 💱 每月匯率表格")
    st.dataframe(fx_df.style.format({"USD": "{:.4f}", "TWD": "{:.1f}"}))

    st.markdown("---")
    st.caption(f"📅 資料時間範圍：{months[0]} 到 {months[-1]} | 資料筆數：{len(fx_df)}")
