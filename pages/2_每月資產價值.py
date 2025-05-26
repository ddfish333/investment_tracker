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
st.title(f"💸 每月資產價值（以台幣計值）")
st.markdown(f"**目前資產狀況**｜ Sean：NT${sean_curr:,.0f} 元｜ Lo：NT${lo_curr:,.0f} 元")

st.subheader("總資產跑動：Sean vs Lo")
st.line_chart(summary_df[['Sean', 'Lo']])

st.subheader("Sean 每月資產變化")
if isinstance(detail_df.columns, pd.MultiIndex) and 'Sean' in detail_df.columns.get_level_values("Owner"):
    df_sean = detail_df.loc[:, detail_df.columns.get_level_values("Owner") == "Sean"]
    df_sean['Total'] = df_sean.sum(axis=1)
    st.line_chart(df_sean)

st.subheader("Lo 每月資產變化")
if isinstance(detail_df.columns, pd.MultiIndex) and 'Lo' in detail_df.columns.get_level_values("Owner"):
    df_lo = detail_df.loc[:, detail_df.columns.get_level_values("Owner") == "Lo"]
    df_lo['Total'] = df_lo.sum(axis=1)
    st.line_chart(df_lo)
