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

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex 格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.xs(owner, level='Owner', axis=1).copy()
        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        df['Total'] = df.sum(axis=1)
        current_twd = df['Total'].iloc[-1]
        st.write(f"### {owner} ｜ 目前台幣資產：NT${current_twd:,.0f}")

        # 排序股票：剩餘資產多的放前面
        latest = df.iloc[-1].drop('Total')
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        plot_codes = sorted_codes + zero_codes

        df_plot = df[plot_codes].copy()

        fig, ax = plt.subplots(figsize=(12, 4))
        bottom = pd.Series([0]*len(df_plot), index=df_plot.index)
        for code in plot_codes:
            values = df_plot[code].fillna(0)
            ax.bar(df_plot.index, values, bottom=bottom, label=str(code))
            bottom += values

        ax.set_title(f"{owner} 各股票月資產變化（長條堆疊圖）")
        ax.set_ylabel("資產（元）")
        ax.legend(ncol=5, fontsize=8)
        st.pyplot(fig)
