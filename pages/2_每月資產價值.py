# pages/2_每月資產價值.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("💰 每月資產價值（以台幣計價）")

# 解析並計算資產價值
data_file = "data/transactions.xlsx"
monthly_dict = parse_monthly_holdings(data_file)
# calculate_monthly_asset_value 內已處理同時過濾0值與匯率
df_asset = calculate_monthly_asset_value(data_file)

# 繪製折線圖
# 保留日期索引
st.line_chart(df_asset)
