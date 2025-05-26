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

# --- 顯示總資產走勢 ---
st.title(f"💸 每月資產價值（以台幣計值）")
st.markdown(f"**目前資產狀況**｜ Sean：NT${sean_curr:,.0f} 元｜ Lo：NT${lo_curr:,.0f} 元")

st.subheader("總資產走勢：Sean vs Lo")
st.line_chart(summary_df[['Sean', 'Lo']])

# --- 各股票資產改為長條圖疊加 ---
st.subheader("各股票資產：長條圖疊加顯示")

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex 格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.loc[:, detail_df.columns.get_level_values('Owner') == owner].copy()
        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        current_twd = df.sum(axis=1).iloc[-1]
        st.write(f"### {owner} ｜ 目前台幣資產：NT${current_twd:,.0f}")

        # 計算每月所有股票的堆疊長條圖
        fig, ax = plt.subplots(figsize=(12, 4))
        bottom = pd.Series([0]*len(df), index=df.index)
        sorted_codes = df.iloc[-1].sort_values(ascending=False).index.tolist()

        for code in sorted_codes:
            ax.bar(df.index, df[code], bottom=bottom, label=code)
            bottom += df[code]

        ax.set_title(f"{owner} 各股票資產（長條堆疊圖）")
        ax.set_ylabel("NTD")
        ax.legend(ncol=5, fontsize=8)
        st.pyplot(fig)
