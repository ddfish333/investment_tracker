import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st
import os

# --- 設定中文字體（使用思源黑體） ---
font_path = "/System/Library/Fonts/PingFang.ttc"  # macOS 內建中文
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False

# --- 讀檔 ---
df = pd.read_excel("data/transactions.xlsx")
df = df[df["備註"].isin(["Lo", "Sean", "Sean/Lo"])]
df["股票代號"] = df["股票代號"].astype(str)
df["交易日期"] = pd.to_datetime(df["交易日期"])
df["月份"] = df["交易日期"].dt.to_period("M")

# 整理代號與月份
all_codes = sorted(df["股票代號"].dropna().unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")
owners = ["Lo", "Sean", "Sean/Lo"]

# 初始化表格
holdings = {
    owner: pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
    for owner in owners
}
current = {owner: {code: 0 for code in all_codes} for owner in owners}

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        code = row["股票代號"]
        qty = int(row["買賣股數"])
        owner = row["備註"]
        current[owner][code] += qty
    for owner in owners:
        for code in all_codes:
            holdings[owner].at[month, code] = current[owner][code]

# 檢查是否已歸零來決定是否灰色
total_holding = sum(holdings[owner] for owner in owners)
colors_by_code = {}
for code in all_codes:
    series = total_holding[code]
    zero_idx = series[series == 0]
    gray_start = zero_idx.index[0] if len(zero_idx) > 0 and series[:zero_idx.index[0]].max() > 0 else None
    colors = []
    for date in series.index:
        if gray_start is not None and date >= gray_start:
            colors.append("gray")
        else:
            colors.append("normal")
    colors_by_code[code] = colors

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 每月持股變化總覽（含 Lo / Sean / SeanLo）")

# 顏色設定
color_map = {"Lo": "#4FC3F7", "Sean": "#0288D1", "Sean/Lo": "#01579B"}

# 分批每4張顯示
chunk_size = 4
chunks = [all_codes[i:i + chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            x = holdings["Lo"].index.to_timestamp()

            bottoms = [0] * len(x)
            for owner in owners:
                values = holdings[owner][code].astype(float)
                bar_colors = [
                    color_map[owner] if colors_by_code[code][j] == "normal" else "lightgray"
                    for j in range(len(x))
                ]
                ax.bar(x, values, bottom=bottoms, color=bar_colors, label=owner)
                bottoms = [b + v for b, v in zip(bottoms, values)]

            ax.set_title(f"每月 {code} 持股數量")
            ax.set_xlabel("月份")
            ax.set_ylabel("股數")
            ax.set_ylim(0, 15000)
            ax.tick_params(axis='x', labelrotation=45)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
