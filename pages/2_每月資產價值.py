# -*- coding: utf-8 -*-
import os
import platform
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import yfinance as yf
from datetime import datetime
from modules.asset_value import calculate_monthly_asset_value
from modules.price_fetcher import fetch_month_end_fx

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
summary_df, detail_df, raw_df, monthly_Lo, monthly_Sean, monthly_Joint, price_df, detail_value_df = calculate_monthly_asset_value("data/transactions.xlsx")

# --- 顯示資產摘要 ---
sean_curr = summary_df.iloc[-1]['Sean']
lo_curr = summary_df.iloc[-1]['Lo']
total_curr = summary_df.iloc[-1]['Total']
sean_tw = summary_df.iloc[-1].get('Sean_TW', 0)
sean_us = summary_df.iloc[-1].get('Sean_US', 0)
lo_tw = summary_df.iloc[-1].get('Lo_TW', 0)
lo_us = summary_df.iloc[-1].get('Lo_US', 0)
total_tw = sean_tw + lo_tw
total_us = sean_us + lo_us

st.title(f"\U0001F4B8 每月資產價值")
st.markdown(f"**Sean**：TWD {sean_curr:,.0f}（台股 TWD {sean_tw:,.0f}／美股 TWD {sean_us:,.0f}）")
st.markdown(f"**Lo**：TWD {lo_curr:,.0f}（台股 TWD {lo_tw:,.0f}／美股 TWD {lo_us:,.0f}）")
st.markdown(f"**Sean&Lo**：TWD {total_curr:,.0f}（台股 TWD {total_tw:,.0f}／美股 TWD {total_us:,.0f}）")

# --- 總資產跑動 ---
st.subheader("Sean&Lo總資產")
summary_df_display = summary_df.copy()
summary_df_display.index = summary_df_display.index.to_timestamp()

# 加入篩選功能
default_selection = ['Sean', 'Lo', 'Total']
selected_lines = st.multiselect("請選擇要顯示的資產線", options=default_selection, default=default_selection)
if selected_lines:
    st.line_chart(summary_df_display[selected_lines])
else:
    st.info("請至少選擇一條資產線來顯示。")

# --- 各股票資產跑動詳細 ---
st.subheader("各股票資產跑動詳細")

if not isinstance(detail_value_df.columns, pd.MultiIndex):
    st.error("detail_value_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_value_df.xs(owner, axis=1, level='Owner').copy()

        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df_display = df.copy().round(0).fillna(0).astype(int)
        df_display.columns.name = "stock"
        df_display.index = df_display.index.strftime("%Y-%m")
        df_display.index.name = "date"

        owner_curr = summary_df.iloc[-1][owner]
        st.markdown(f"#### {owner} 每月資產變化（目前資產 NT${owner_curr:,.0f} 元）")
        st.bar_chart(df_display)

# --- 除錯：顯示原始表格 ---
st.subheader("\U0001F50D 除錯用資料表")
st.markdown("**原始交易紀錄**")
st.dataframe(raw_df)

st.markdown("**Yahoo 月底股價資料（含最新價格）**")
latest_label = datetime.today().strftime("最新價格（%Y/%m/%d）")
latest_prices_df = price_df.iloc[[-1]].copy()
latest_prices_df.index = [latest_label]
st.dataframe(latest_prices_df.round(2))
