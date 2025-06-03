# pages/9_debug_summary_df.py
import streamlit as st
import pandas as pd
from modules.asset_value import calculate_monthly_asset_value
from modules.cash_parser import parse_cash_balances
from config import TRANSACTION_FILE

st.set_page_config(page_title="DEBUG 資產表", layout="wide")

# --- 資料計算 ---
summary_df, raw_df, stock_price_df, stock_value_df, fx_df, all_months = calculate_monthly_asset_value(TRANSACTION_FILE)

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
st.subheader("📊 stock_value_df（每人每月每股票市值）")
st.dataframe(stock_value_df[::-1].style.format("{:,.0f}"))

# --- 顯示 cash_summary ---
st.subheader("💵 cash_summary（每人每月現金資產）")
st.dataframe(cash_summary[::-1].style.format("{:,.0f}"))

# --- 顯示 total_asset_df ---
st.subheader("🧾 total_asset_df（股票＋現金的整合資產表）")
st.dataframe(total_asset_df[::-1].style.format("{:,.0f}"))

# --- 顯示 stock_price_df ---
st.subheader("📗 stock_price_df（每月股票價格快照）")
st.dataframe(stock_price_df.sort_index(ascending=False).style.format("{:,.2f}"))

# --- 顯示 raw_df ---
st.subheader("📒 raw_df（parse_transaction後的DataFrame）")
st.dataframe(raw_df.reset_index(drop=True)[::-1])

# --- 顯示 fx_df ---
st.subheader("📘 fx_df（每月匯率）")
st.dataframe(fx_df.sort_index(ascending=False).style.format("{:,.2f}"))
