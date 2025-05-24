
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# Streamlit Layout
st.set_page_config(layout="wide")
st.title("💰 每月資產價值分析（以台幣計算）")

# 計算每月資產價值（回傳 DataFrame: index=月份, columns=[Sean, Lo]）
asset_df = calculate_monthly_asset_value("data/transactions.xlsx")

# 顯示總資產變化趨勢
st.subheader("📈 每月台幣資產變化（含 Sean + Lo）")
fig, ax = plt.subplots(figsize=(10, 5))
asset_df["Total"] = asset_df["Sean"] + asset_df["Lo"]
asset_df["Total"].plot(ax=ax, color="teal", linewidth=2)
ax.set_ylabel("總資產（TWD）")
ax.set_xlabel("月份")
ax.set_title("合併總資產")
ax.grid(True)
st.pyplot(fig)

# 分別顯示 Sean / Lo 的變化
st.subheader("👤 資產分開觀察")
st.line_chart(asset_df[["Sean", "Lo"]])

# 顯示數據表格
st.subheader("📋 每月資產明細")
st.dataframe(asset_df.style.format("{:,.0f}"))
