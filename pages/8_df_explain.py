# pages/9_debug_summary_df.py
import streamlit as st
import pandas as pd
from modules.asset_value import calculate_monthly_asset_value
from modules.cash_parser import parse_cash_balances
from config import TRANSACTION_FILE

st.set_page_config(page_title="DEBUG 資產表", layout="wide")

# --- 資料計算 ---
result = calculate_monthly_asset_value(TRANSACTION_FILE)
summary_df = result.summary_df
summary_stock_df = result.summary_stock_df
summary_cash_df = result.summary_cash_df
raw_df = result.raw_df
stock_price_df = result.stock_price_df
stock_value_df = result.stock_value_df
fx_df = result.fx_df
all_months = result.all_months

# --- raw_df有哪些欄位 ---

st.subheader("🔍 raw_df 欄位總覽")
st.dataframe(raw_df.head())

# --- 現金資料計算 ---
cash_summary = parse_cash_balances()

# --- 合併成 total_asset_df（每人每月每資產類型）---
total_asset_df = pd.concat([stock_value_df, cash_summary], axis=1).fillna(0)



# --- 顯示目前每人每股票剩餘股數 ---
st.subheader("📌 每人每股票目前持股數量（依 raw_df 計算）")
latest_shares = (
    raw_df.groupby(['出資者', '股票代號'])['股數']
    .sum()
    .reset_index()
    .query("股數 != 0")
    .sort_values(['出資者', '股票代號'])
)
st.dataframe(latest_shares)

# --- 顯示 summary_df ---
st.subheader("📈 summary_df（每人每月總資產）")
st.dataframe(summary_df[::-1].style.format("{:,.0f}"))

# --- 顯示 stock_value_df ---
st.subheader("📊 stock_value_df（目前仍有持股者的股票市值）")
latest_row = stock_value_df.iloc[-1]# 抓最後一列（最新月份） > 0 的欄位
active_columns = latest_row[latest_row > 0].index.tolist()

# 篩選出目前有持股的股票
filtered_stock_value_df = stock_value_df[active_columns]

st.dataframe(filtered_stock_value_df[::-1].style.format("{:,.0f}"))
# --- 顯示 cash_summary ---
st.subheader("💵 cash_summary（每人每月現金資產）")
st.dataframe(cash_summary[::-1].style.format("{:,.0f}"))


