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

# 將 index 轉為 timestamp，方便控制 x 軸標籤格式
monthly_holding.index = monthly_holding.index.to_timestamp()

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化（直方圖總覽）")

# 分批每4張顯示
chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            values = monthly_holding[code].astype(float)
            colors = ['skyblue'] * len(values)

            # 若最後一段全為 0，代表出清，則整段變灰
            if (values != 0).any() and values[values != 0].iloc[-1] == 0:
                colors = ['lightgray'] * len(values)

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(monthly_holding.index, values, color=colors)

            # 美化 x 軸：只顯示年份
            ax.set_xticks(
                [d for d in monthly_holding.index if d.month == 1]
            )
            ax.set_xticklabels(
                [d.strftime('%Y') for d in monthly_holding.index if d.month == 1]
            )

            ax.set_title(f"Lo 每月 {code} 持股數變化")
            ax.set_xlabel("年")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, 15000)
            plt.tight_layout()
            st.pyplot(fig)
