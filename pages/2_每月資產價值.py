# -*- coding: utf-8 -*-
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
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

st.subheader("總資產跑動：Sean vs Lo")
st.line_chart(summary_df[['Sean', 'Lo']])

st.subheader("各股票資產跑動詳細")

# 冷色系配色（支援 50 種）
cool_colors = plt.cm.Blues_r(np.linspace(0.3, 0.9, 50))

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex 格式，無法分別顯示 Sean / Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.xs(owner, level='Owner', axis=1).copy()
        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        # 排序股票：剩餘資產多的放前面
        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df.index = df.index.strftime("%Y-%m")

        fig, ax = plt.subplots(figsize=(12, 5))
        bottom = np.zeros(len(df))
        x = np.arange(len(df.index))

        for i, code in enumerate(df.columns):
            color = cool_colors[i % len(cool_colors)]
            ax.bar(x, df[code].values, bottom=bottom, label=str(code), color=color)
            bottom += df[code].values

        ax.set_title(f"{owner} 每月股票資產分佈（堆疊長條圖）")
        ax.set_ylabel("台幣資產")
        ax.set_xticks(x)
        ax.set_xticklabels(df.index, rotation=45, ha='right')
        ax.legend(fontsize=8, ncol=5)
        st.pyplot(fig)
