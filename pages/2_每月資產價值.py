# -*- coding: utf-8 -*-
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from modules.asset_value import calculate_monthly_asset_value

# --- Streamlit Page Setup ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# --- 計算資產 ---
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")
sean_curr = summary_df['Sean'].iloc[-1]
lo_curr = summary_df['Lo'].iloc[-1]

# --- 顯示結果 ---
st.title(f"\U0001F4B8 每月資產價值（以台幣計值）")
st.markdown(f"**目前資產狀況**｜ Sean：NT${sean_curr:,.0f} 元｜ Lo：NT${lo_curr:,.0f} 元")

# --- 總資產趨勢 ---
st.subheader("總資產跑動：Sean vs Lo")
st.line_chart(summary_df[['Sean', 'Lo']])

# --- 個別持有人資產明細長條圖 ---
for owner in ['Sean', 'Lo']:
    df = detail_df.xs(owner, axis=1, level='Owner').fillna(0).copy()
    df['Total'] = df.sum(axis=1)
    st.write(f"### {owner} ｜ 目前台幣資產：NT${df['Total'].iloc[-1]:,.0f}")

    fig, ax = plt.subplots(figsize=(12, 4))
    bottom = pd.Series([0] * len(df), index=df.index)

    for code in df.drop(columns='Total').columns:
        values = df[code].fillna(0)
        ax.bar(df.index, values, label=code, bottom=bottom)
        bottom += values

    ax.set_title(f"{owner} 各股票月資產變化（長條堆疊圖）")
    ax.legend(ncol=5, fontsize=8, loc='upper left')
    st.pyplot(fig)
