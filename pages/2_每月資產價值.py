# pages/2_每月資產價值.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value

# --- Streamlit Page: 每月資產價值（以台幣計價） ---
st.set_page_config(layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 計算每月資產（summary & detail）
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# --- 顯示總資產走勢 ---
st.title("💰 每月資產價值（以台幣計價）")
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df)

# --- 顯示各股票明細 ---
st.subheader("個股資產明細")
for code in detail_df.columns.levels[0]:
    st.markdown(f"### {code} 資產走勢")
    df_code = detail_df[code]
    st.line_chart(df_code)
