import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st
import os

# --- 設定中文字體（macOS 或 Linux） ---
font_path = "/System/Library/Fonts/STHeiti Medium.ttc"  # macOS 預設中文
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False

# --- 讀檔 ---
df = pd.read_excel("data/transactions.xlsx")
df = df[df["備註"].isin(["Lo", "Sean", "Sean/Lo"])]
df["交易日期"] = pd.to_datetime(df["交易日期"])
df["月份"] = df["交易日期"].dt.to_period("M")

# 整理代號與月份
all_codes = sorted(df["股票代號"].dropna().astype(str).unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化持股表格
sources = ["Lo", "Sean", "Sean/Lo"]
monthly_holdings = {src: pd.DataFrame(index=all_months, columns=all_codes).fillna(0) for src in sources}
current_holdings = {src: {code: 0 for code in all_codes} for src in sources}

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        code = str(row["股票代號"])
        qty = int(row["買賣股數"])
        note = row["備註"]
        current_holdings[note][code] += qty
    for src in sources:
        for code in all_codes:
            monthly_holdings[src].at[month, code] = current_holdings[src][code]

# 計算疊加值找 y 軸最大值
combined = monthly_holdings["Lo"] + monthly_holdings["Sean"] + monthly_holdings["Sean/Lo"]
y_max = (combined.max().max() * 1.1).round(-2)

# --- 畫圖 ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化")

chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            code = str(code)
            x = monthly_holdings["Lo"].index.to_timestamp()
            
            bottom = [0] * len(x)
            for src, color in zip(sources, ["#90caf9", "#42a5f5", "#1565c0"]):
                values = monthly_holdings[src][code].astype(float).values
                ax.bar(x, values, bottom=bottom, color=color, label=src)
                bottom = [sum(x) for x in zip(bottom, values)]

            ax.set_title(f"{code} 每月持股變化（堆疊）")
            ax.set_xlabel("月")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, y_max)
            ax.legend()
            ax.tick_params(axis='x', labelrotation=30)
            plt.tight_layout()
            st.pyplot(fig)