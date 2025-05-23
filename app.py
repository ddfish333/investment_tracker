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
df["交易日期"] = pd.to_datetime(df["交易日期"])
df["月份"] = df["交易日期"].dt.to_period("M")

# 按備註分組：Lo、Sean、Sean/Lo
df = df[df["備註"].isin(["Lo", "Sean", "Sean/Lo"])]

all_codes = sorted(df["股票代號"].dropna().astype(str).unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化表格
holdings = {
    "Lo": pd.DataFrame(index=all_months, columns=all_codes).fillna(0),
    "Sean": pd.DataFrame(index=all_months, columns=all_codes).fillna(0),
    "Sean/Lo": pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
}
current_holding = {key: {code: 0 for code in all_codes} for key in holdings.keys()}

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        code = str(row["股票代號"])
        qty = int(row["買賣股數"])
        owner = row["備註"]
        current_holding[owner][code] += qty

    for owner in holdings:
        for code in all_codes:
            holdings[owner].at[month, code] = current_holding[owner][code]

# 處理 x 軸
for owner in holdings:
    holdings[owner].index = holdings[owner].index.to_timestamp()

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 每月持股變化（Lo、Sean、Sean/Lo 疊加直方圖）")

chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

colors = {
    "Lo": "#91cfff",         # 淺藍
    "Sean": "#409eff",       # 中藍
    "Sean/Lo": "#007acc"     # 深藍
}

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))

            base = pd.Series([0]*len(all_months), index=holdings["Lo"].index)

            for owner in ["Lo", "Sean", "Sean/Lo"]:
                values = holdings[owner][code].astype(float)
                ax.bar(values.index, values.values, bottom=base.values, color=colors[owner], label=owner)
                base += values

            ax.set_title(f"{code} 每月持股變化（累加）")
            ax.set_xlabel("年")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, 15000)
            ax.tick_params(axis='x', rotation=30)
            ax.legend()
            st.pyplot(fig)
