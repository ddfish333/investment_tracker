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
# 將 Joint 的一半加到各自持有者
if ('Joint' in summary_df.columns):
    sean_curr = (summary_df['Sean'] + summary_df['Joint'] * 0.5).iloc[-1]
    lo_curr = (summary_df['Lo'] + summary_df['Joint'] * 0.5).iloc[-1]
    summary_df['Sean'] += summary_df['Joint'] * 0.5
    summary_df['Lo'] += summary_df['Joint'] * 0.5
else:
    sean_curr = summary_df['Sean'].iloc[-1]
    lo_curr = summary_df['Lo'].iloc[-1]

# --- 顯示結果 ---
st.title(f"💸 每月資產價值（以台幣計值）")
st.markdown(f"**目前資產狀況**｜ Sean：NT${sean_curr:,.0f} 元｜ Lo：NT${lo_curr:,.0f} 元")

st.subheader("總資產跑動：Sean vs Lo")
st.line_chart(summary_df[['Sean', 'Lo']])

st.subheader("各股票資產跑動詳細")

# Check if detail_df has MultiIndex columns
if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.xs(owner, axis=1, level='Owner').copy()
        if 'Joint' in detail_df.columns.get_level_values('Owner'):
            df_joint = detail_df.xs('Joint', axis=1, level='Owner').copy() * 0.5
            df += df_joint

        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df_display = df.copy()
        df_display.columns.name = "stock"  # 設定欄位名稱為 stock
        df_display.index = df_display.index.strftime("%Y-%m")
        df_display.index.name = "date"  # 將 index 名稱改為 date

        st.markdown(f"#### {owner} 每月資產變化")
        st.bar_chart(df_display)
