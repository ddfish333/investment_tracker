import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st
import os

# --- 設定中文字體（使用思源黑體） ---
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
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
df["股票代號"] = df["股票代號"].astype(str)

# 所有代號與月份
all_codes = sorted(df["股票代號"].dropna().unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化資料結構：每個來源一份表
holdings_by_label = {"Lo": {}, "Sean": {}, "Sean/Lo": {}}
for label in holdings_by_label:
    holdings_by_label[label]["df"] = pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
    holdings_by_label[label]["current"] = {code: 0 for code in all_codes}

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        label = row["備註"]
        code = row["股票代號"]
        qty = int(row["買賣股數"])
        holdings_by_label[label]["current"][code] += qty
    for label in holdings_by_label:
        for code in all_codes:
            holdings_by_label[label]["df"].at[month, code] = holdings_by_label[label]["current"][code]

# 將 index 轉 timestamp
for label in holdings_by_label:
    holdings_by_label[label]["df"].index = holdings_by_label[label]["df"].index.to_timestamp()

# 依照三個來源加總後，找出最高總持股做為 Y 軸最大值
total_stack = sum(holdings_by_label[label]["df"] for label in holdings_by_label)
max_y = total_stack.max().max() * 1.1

# 根據最新月份持股數總和做排序（從高到低）
latest = total_stack.iloc[-1].sort_values(ascending=False)
sorted_codes = latest.index.tolist()

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化")

# 每4張一列
chunk_size = 4
chunks = [sorted_codes[i:i+chunk_size] for i in range(0, len(sorted_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(len(chunk))
    for i, code in enumerate(chunk):
        with cols[i]:
            fig, ax = plt.subplots(figsize=(6, 4))
            bottom = pd.Series([0] * len(holdings_by_label["Lo"]["df"].index), index=holdings_by_label["Lo"]["df"].index)
            for label, color in zip(["Lo", "Sean", "Sean/Lo"], ['#76c7c0', '#3a7ca5', '#1f4e79']):
                values = holdings_by_label[label]["df"][code].astype(float)
                ax.bar(values.index, values, bottom=bottom, label=label, color=color, width=20)
                bottom += values
            ax.set_title(f"{code} 持股數變化")
            ax.set_xlabel("月")
            ax.set_ylabel("股數")
            ax.set_ylim(0, max_y)
            ax.legend()
            plt.xticks(rotation=30)
            st.pyplot(fig)
