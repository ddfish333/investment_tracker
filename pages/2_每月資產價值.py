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

# 指定顏色：讓 6770 換成不同色
custom_colors = {
    '6770': '#e63946',  # 深紅色（與2330不同）
    '2330': '#1f77b4',  # 預設藍色
}

# Check if detail_df has MultiIndex columns
if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        st.markdown(f"#### {owner} 資產組合")
        df = detail_df.xs(owner, axis=1, level='Owner')
        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df_display = df.copy()
        df_display.index = df_display.index.strftime("%Y-%m")

        # 自訂顏色列表（順序對應欄位）
        color_list = [custom_colors.get(code, None) for code in df.columns]

        fig, ax = plt.subplots(figsize=(12, 4))
        bottom = pd.Series([0] * len(df), index=df.index)
        for i, code in enumerate(df.columns):
            ax.bar(df.index, df[code], label=code, bottom=bottom, color=color_list[i])
            bottom += df[code]

        ax.set_title(f"{owner} 每月資產變化（長條圖）")
        ax.legend(fontsize=8, ncol=6)
        st.pyplot(fig)
