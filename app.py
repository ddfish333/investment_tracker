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

# 三種來源
owners = ["Lo", "Sean", "Sean/Lo"]
colors = {
    "Lo": "#7FC8F8",
    "Sean": "#1D8FE1",
    "Sean/Lo": "#165E91"
}

# 整理所有股票代號與月份
all_codes = sorted(df["股票代號"].dropna().astype(str).unique())
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化
data_by_owner = {}
for owner in owners:
    owner_df = df[df["備註"] == owner].copy()
    owner_df["股票代號"] = owner_df["股票代號"].astype(str)

    monthly_holding = pd.DataFrame(index=all_months, columns=all_codes).fillna(0)
    current_holding = {code: 0 for code in all_codes}

    for month in all_months:
        rows = owner_df[owner_df["月份"] == month]
        for _, row in rows.iterrows():
            code = row["股票代號"]
            qty = int(row["買賣股數"])
            current_holding[code] += qty
        for code in all_codes:
            monthly_holding.at[month, code] = current_holding[code]

    data_by_owner[owner] = monthly_holding

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化")

# 分批每4張顯示
chunk_size = 4
chunks = [all_codes[i:i+chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))

            for owner in owners:
                df_owner = data_by_owner[owner]
                values = df_owner[code].astype(float)
                color = colors[owner]

                # 判斷是否已歸零後不再持有
                zero_index = None
                for idx in range(len(values)):
                    if values.iloc[idx] == 0 and idx > 0 and values.iloc[idx - 1] > 0:
                        zero_index = idx
                        break
                if zero_index is not None:
                    bar_colors = [color] * zero_index + ["lightgray"] * (len(values) - zero_index)
                else:
                    bar_colors = [color] * len(values)

                ax.bar(df_owner.index.to_timestamp(), values, color=bar_colors, label=owner)

            ax.set_title(f"Lo 每月 {code} 持股變化")
            ax.set_xlabel("年")
            ax.set_ylabel("持股數")
            ax.set_ylim(0, 15000)
            ax.tick_params(axis='x', labelrotation=30)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)