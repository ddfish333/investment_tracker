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

# 轉成年月格式與額外標註年份
monthly_holding.index = monthly_holding.index.to_timestamp()
monthly_holding["月份"] = monthly_holding.index.strftime("%Y-%m")
monthly_holding["年份"] = monthly_holding.index.year.astype(str)

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化（直方圖總覽）")

# 分批每4張顯示
chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

monthly_holding.set_index("月份", inplace=True)

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            values = monthly_holding[code].astype(float)

            # 計算變色：一旦變0就往後全部灰色
            colors = ['skyblue'] * len(values)
            for idx in range(len(values)):
                if values.iloc[idx] == 0 and idx > 0 and values.iloc[idx - 1] > 0:
                    colors[idx:] = ['lightgray'] * (len(values) - idx)
                    break

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(values.index, values.values, color=colors)

            # X軸只顯示每年1月的 label
            xticks = [i for i, x in enumerate(values.index) if x.endswith("-01") or i == 0]
            ax.set_xticks(xticks)
            ax.set_xticklabels([values.index[i][:4] for i in xticks])

            ax.set_title(f"Lo 每月 {code} 持股變化")
            ax.set_xlabel("年份")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, 15000)
            plt.tight_layout()
            st.pyplot(fig)
