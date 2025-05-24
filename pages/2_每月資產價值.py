import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.asset_value import calculate_monthly_asset_value

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 載入資料與計算每月資產價值
monthly_holding_dict = parse_monthly_holdings("data/transactions.xlsx")
combined_df = calculate_monthly_asset_value("data/transactions.xlsx")

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("💰 每月資產價值（以台幣計價）")

# 繪製折線圖
st.line_chart(combined_df)
