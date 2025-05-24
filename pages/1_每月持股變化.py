# pages/1_每月持股變化.py
import streamlit as st
import matplotlib.pyplot as plt
from modules.holding_parser import parse_monthly_holdings

# 讀取持股資料
monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, raw_df, color_map = parse_monthly_holdings("data/transactions.xlsx")

st.set_page_config(layout="wide")
st.title("🌟 每月持股變化總覽（量加直方圖）")

# 總描直方圖
for code in all_codes:
    fig, ax = plt.subplots(figsize=(6, 3))
    series_Lo = monthly_Lo[code]
    series_Sean = monthly_Sean[code]
    series_SeanLo = monthly_SeanLo[code]

    ax.bar(series_Lo.index, series_Lo, color=color_map(series_Lo, '#B0B0B0'), label="Lo", width=20)
    ax.bar(series_Sean.index, series_Sean, color=color_map(series_Sean, '#888888'), label="Sean", width=20, bottom=series_Lo)
    ax.bar(series_SeanLo.index, series_SeanLo, color=color_map(series_SeanLo, '#4F4F4F'), label="Sean/Lo", width=20, bottom=series_Lo + series_Sean)

    ax.set_title(f"{code} 持股變化")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)
