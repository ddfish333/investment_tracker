import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st
import os

# --- 中文字體設定（macOS） ---
font_path = "/System/Library/Fonts/PingFang.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False
plt.style.use('dark_background')  # 深色背景風格

# --- 讀檔 ---
df = pd.read_excel("data/transactions.xlsx")
df = df[df["備註"] == "Lo"]
df["交易日期"] = pd.to_datetime(df["交易日期"])
df["月份"] = df["交易日期"].dt.to_period("M")

# 整理代號與月份
all_codes = sorted(df["股票代號"].dropna().unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化表格
monthly_holding = pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
current_holding = {code: 0 for code in all_codes}

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        code = row["股票代號"]
        qty = int(row["買賣股數"])
        current_holding[code] += qty
    for code in all_codes:
        monthly_holding.at[month, code] = current_holding[code]

# datetime index 用於格式化 x 軸
monthly_holding.index = monthly_holding.index.to_timestamp()

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo每月持股變化")

# 分批每4張顯示
chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            values = monthly_holding[code].astype(float)
            # 找出首次歸零的位置
            drop_index = None
            for idx in range(1, len(values)):
                if values.iloc[idx] == 0 and values.iloc[idx - 1] > 0:
                    drop_index = idx
                    break
            # 設定 bar 顏色：歸零後與前皆為灰
            if drop_index is not None:
                colors = ['gray' if idx <= drop_index else 'skyblue' for idx in range(len(values))]
            else:
                colors = ['skyblue'] * len(values)

            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(monthly_holding.index, values, color=colors, width=20)
            ax.set_title(f"Lo 每月 {code} 持股變化")
            ax.set_xlabel("年")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, 15000)
            ax.set_facecolor("#0b1c2c")
            fig.patch.set_facecolor('#0b1c2c')
            ax.tick_params(axis='x', labelrotation=45, colors='lightgray')
            ax.tick_params(axis='y', colors='lightgray')
            ax.spines['bottom'].set_color('lightgray')
            ax.spines['left'].set_color('lightgray')
            ax.title.set_color('white')
            ax.yaxis.label.set_color('lightgray')
            ax.xaxis.label.set_color('lightgray')

            plt.tight_layout()
            st.pyplot(fig)
