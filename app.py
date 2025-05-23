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
df["來源"] = df["備註"].fillna("其他")
df["幣別"] = df["幣別"].fillna("TWD")

# 整理代號與月份
all_codes = sorted(df["股票代號"].dropna().unique(), key=lambda x: str(x))
all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

# 初始化三種來源的表格與持股追蹤
def initialize_holdings():
    return pd.DataFrame(index=all_months, columns=all_codes).fillna(0), {code: 0 for code in all_codes}

monthly_Lo, current_Lo = initialize_holdings()
monthly_Sean, current_Sean = initialize_holdings()
monthly_SeanLo, current_SeanLo = initialize_holdings()

# FIFO 累積
for month in all_months:
    rows = df[df["月份"] == month]
    for _, row in rows.iterrows():
        code = row["股票代號"]
        qty = int(row["買賣股數"])
        source = row["來源"]
        if source == "Lo":
            current_Lo[code] += qty
        elif source == "Sean":
            current_Sean[code] += qty
        elif source == "Sean/Lo":
            current_SeanLo[code] += qty

    for code in all_codes:
        monthly_Lo.at[month, code] = current_Lo[code]
        monthly_Sean.at[month, code] = current_Sean[code]
        monthly_SeanLo.at[month, code] = current_SeanLo[code]

# datetime index for plotting
monthly_Lo.index = monthly_Lo.index.to_timestamp()
monthly_Sean.index = monthly_Sean.index.to_timestamp()
monthly_SeanLo.index = monthly_SeanLo.index.to_timestamp()

# 計算總持股做為排序依據與Y軸最大值計算（依照幣別區分）
code_to_currency = df.groupby("股票代號")["幣別"].first().to_dict()
code_total = {}
twd_max, usd_max = 0, 0
for code in all_codes:
    total = (monthly_Lo[code] + monthly_Sean[code] + monthly_SeanLo[code]).max()
    code_total[code] = total
    if code_to_currency.get(code, "TWD") == "USD":
        usd_max = max(usd_max, total)
    else:
        twd_max = max(twd_max, total)

# 持股多的放前面
sorted_codes = sorted(all_codes, key=lambda c: code_total[c], reverse=True)

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 Lo 每月持股變化")

chunk_size = 4
chunks = [sorted_codes[i:i+chunk_size] for i in range(0, len(sorted_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(monthly_Lo.index, monthly_Lo[code], color='#87CEEB', label='Lo', width=20)
            ax.bar(monthly_Sean.index, monthly_Sean[code], color='#4682B4', label='Sean', bottom=monthly_Lo[code], width=20)
            ax.bar(monthly_SeanLo.index, monthly_SeanLo[code], color='#1E3F66', label='Sean/Lo',
                   bottom=monthly_Lo[code] + monthly_Sean[code], width=20)

            ax.set_title(f"{code} 持股數量變化")
            ax.set_xlabel("月")
            ax.set_ylabel("持股")
            ax.legend()
            
            if code_to_currency.get(code, "TWD") == "USD":
                ax.set_ylim(0, usd_max * 1.1)
            else:
                ax.set_ylim(0, twd_max * 1.1)

            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
