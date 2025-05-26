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

st.subheader("各股票資產跑動詳細")

# 冷色系配色方案（最多支援 10 檔）
cool_colors = [
    "#1f77b4",  # 深藍
    "#2a9fd6",  # 淺藍
    "#17becf",  # 藍綠
    "#4c72b0",  # 紫藍
    "#76b7b2",  # 淺綠藍
    "#5DA5DA",  # 藍灰
    "#AEC7E8",  # 淡藍
    "#6baed6",  # 藍灰中間色
    "#9ecae1",  # 淺灰藍
    "#c6dbef",  # 最淡藍
]

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.loc[:, detail_df.columns.get_level_values('Owner') == owner].copy()
        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df.index = df.index.strftime("%Y-%m")

        fig, ax = plt.subplots(figsize=(10, 4))
        bottom = pd.Series([0] * len(df), index=df.index)

        for i, code in enumerate(df.columns):
            color = cool_colors[i % len(cool_colors)]
            ax.bar(df.index, df[code], label=code, bottom=bottom, color=color)
            bottom += df[code]

        ax.set_title(f"{owner} 每月股票資產分佈（堆疊長條圖）")
        ax.set_ylabel("台幣資產")
        ax.set_xticks(range(len(df.index)))
        ax.set_xticklabels(df.index, rotation=45, ha='right')
        ax.legend(fontsize=8, ncol=5)
        st.pyplot(fig)
