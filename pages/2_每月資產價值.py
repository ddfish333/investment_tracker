# -*- coding: utf-8 -*-
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from modules.asset_value import calculate_monthly_asset_value
import pandas as pd

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

# 容錯處理：若 summary_df 為空則設為 0
try:
    lo_curr = summary_df['Lo'].iloc[-1]
except:
    lo_curr = 0
try:
    sean_curr = summary_df['Sean'].iloc[-1]
except:
    sean_curr = 0

# --- 顯示結果 ---
st.title(f"💸 每月資產價值（以台幣計值）")
st.markdown(f"**目前資產狀況**｜ Lo：NT${lo_curr:,.0f} 元｜ Sean：NT${sean_curr:,.0f} 元")

# 總資產趨勢圖
if not summary_df.empty:
    st.subheader("總資產跑動：Lo vs Sean")
    st.line_chart(summary_df[['Lo', 'Sean']])
else:
    st.warning("目前無總資產資料")

# 各股票資產明細圖
st.subheader("各股票資產跑動詳細")
for owner in ['Lo', 'Sean']:
    if (owner not in detail_df.columns.get_level_values(0)):
        st.write(f"### {owner}｜目前台幣資產：無資料")
        continue

    df = detail_df.loc[:, owner].copy()
    df['Total'] = df.sum(axis=1)

    current_total = df['Total'].iloc[-1] if not df.empty else 0
    st.write(f"### {owner}｜目前台幣資產：NT${current_total:,.0f}")

    # 排序股票：剩餘資產多的放前面
    latest = df.iloc[-1].drop('Total') if not df.empty else pd.Series()
    sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
    zero_codes = latest[latest == 0].index.tolist()
    df = df[sorted_codes + zero_codes + ['Total']]

    fig, ax = plt.subplots(figsize=(12, 4))
    for code in df.columns:
        if code == 'Total':
            ax.plot(df.index, df[code], label=code, linewidth=2.5, color='white')
        elif code in sorted_codes:
            ax.plot(df.index, df[code], label=code)
        else:
            ax.plot(df.index, df[code], label=code, linestyle='dotted', color='gray')
    ax.set_title(f"{owner} 各股票月資產變化")
    ax.legend(ncol=5, fontsize=8)
    st.pyplot(fig)
