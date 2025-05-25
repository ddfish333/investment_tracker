# modules/stock_monthlyprice.py
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx


def get_monthly_stock_prices(codes, months):
    """
    回傳指定股票於各月的收盤價 (若為美股，可搭配匯率轉換)
    """
    # 取得原幣別月末收盤價
    price_df = fetch_month_end_prices(codes, months)
    return price_df


def get_monthly_fx(months):
    """
    回傳指定月份的 USD→TWD 匯率
    """
    return fetch_month_end_fx(months)


# pages/4_每月股票價格.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.holding_parser import parse_monthly_holdings
from modules.stock_monthlyprice import get_monthly_stock_prices, get_monthly_fx

# --- Streamlit Page: 每月股票價格查詢 ---
st.set_page_config(layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

st.title("📈 每月股票價格查詢 (2330 & TSLA)")

# 從持股解析器取得完整月份索引
_, _, _, all_codes, all_months, _, _ = parse_monthly_holdings("data/transactions.xlsx")

# 選擇要查詢的股票代號
selected = ["2330", "TSLA"]
# 撈取各月收盤價 (原幣)
price_df = get_monthly_stock_prices(selected, all_months)
# 撈取各月匯率
fx = get_monthly_fx(all_months)

# 將美股價格換算成台幣
if "TSLA" in price_df.columns:
    price_df["TSLA (TWD)"] = price_df["TSLA"] * fx

# 繪製折線圖
st.line_chart(
    price_df.drop(columns=["TSLA"]) if "TSLA" in price_df.columns else price_df
)
