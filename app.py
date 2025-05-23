import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st
import os

# --- 設定中文字體（macOS 思源黑體） ---
font_path = "/System/Library/Fonts/Supplemental/Heiti TC.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False

# --- 載入資料 ---
df = pd.read_excel("data/transactions.xlsx")
df = df[df["備註"].isin(["Lo", "Sean", "Sean/Lo"])].copy()
df["交易日期"] = pd.to_datetime(df["交易日期"])
df["月份"] = df["交易日期"].dt.to_period("M")

# 股票代號統一成字串型態（避免數字型和字串型混在一起）
df["股票代號"] = df["股票代號"].astype(str)

# 所有代號與月份
all_codes = sorted(df["股票代號"].dropna().unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化結構：每個代號一個 DataFrame
holdings_by_label = {"Lo": {}, "Sean": {}, "Sean/Lo": {}}
for label in holdings_by_label:
    holdings_by_label[label]["df"] = pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
    holdings_by_label[label]["current"] = {code: 0 for code in all_codes}

# FIFO 累積
for month in all_months:
    month_df = df[df["月份"] == month]
    for _, row in month_df.iterrows():
        label = row["備註"]
        code = row["股票代號"]
        qty = int(row["買賣股數"])
        holdings_by_label[label]["current"][code] += qty
    for label in holdings_by_label:
        for code in all_codes:
            holdings_by_label[label]["df"].at[month, code] = holdings_by_label[label]["current"][code]

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化")

# 全部轉 timestamp，方便畫圖
for label in holdings_by_label:
    holdings_by_label[label]["df"].index = holdings_by_label[label]["df"].index.to_timestamp()

# 計算每個月份總和的最大值來設 Y 軸上限
total_stacks = sum(holdings_by_label[label]["df"] for label in holdings_by_label)
max_holding = total_stacks.max().max()
ymax = int(max_holding * 1.1)

# 每4張為一組
chunk_size = 4
chunks = [all_codes[i:i + chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            x = holdings_by_label["Lo"]["df"].index
            lo_values = holdings_by_label["Lo"]["df"][code].astype(float)
            sean_values = holdings_by_label["Sean"]["df"][code].astype(float)
            seanlo_values = holdings_by_label["Sean/Lo"]["df"][code].astype(float)

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(x, lo_values, color="#91cfff", label="Lo", width=25)
            ax.bar(x, sean_values, bottom=lo_values, color="#3e8de3", label="Sean", width=25)
            ax.bar(x, seanlo_values, bottom=lo_values + sean_values, color="#155fa0", label="Sean/Lo", width=25)

            ax.set_title(f"{code} 每月持股數量變化")
            ax.set_xlabel("月")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, ymax)
            ax.tick_params(axis='x', labelrotation=45)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
