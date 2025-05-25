# modules/stock_monthlyprice.py
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def get_monthly_stock_prices(codes, months):
    """
    回傳指定股票於各月的收盤價 (若為美股，可搭配匯率轉換)
    """
    # 取得原幣別月末收盤價
    price_df = fetch_month_end_prices(codes, months)
    # 確保 DataFrame 索引為月份，欄位為代號
    price_df = price_df.reindex(index=months, columns=codes)
    return price_df


def get_monthly_fx(months):
    """
    回傳指定月份的 USD→TWD 匯率
    """
    fx = fetch_month_end_fx(months)
    return fx.reindex(months)

# pages/4_每月股票價格.py
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from modules.holding_parser import parse_monthly_holdings
from modules.stock_monthlyprice import get_monthly_stock_prices, get_monthly_fx

# --- Streamlit Page: 每月股票價格查詢 ---
st.set_page_config(page_title="每月股票價格", layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

st.title("📈 每月股票價格查詢 (2330 & TSLA)")

# 取得所有月份索引
_, _, _, all_codes, all_months, _, _ = parse_monthly_holdings("data/transactions.xlsx")

# 固定查詢列表，可改為 selectbox
query_codes = ["2330", "TSLA"]

# 撈取收盤價與匯率
price_df = get_monthly_stock_prices(query_codes, all_months)
fx_series = get_monthly_fx(all_months)

# 將美股價格換算為台幣
if "TSLA" in price_df.columns:
    price_df["TSLA_TWD"] = price_df["TSLA"] * fx_series

# 顯示折線圖
st.subheader("原幣別收盤價")
st.line_chart(price_df[query_codes])

if "TSLA_TWD" in price_df.columns:
    st.subheader("TSLA 換算後之台幣價格")
    st.line_chart(price_df[["TSLA_TWD"]])
