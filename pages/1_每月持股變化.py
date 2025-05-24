import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.holding_parser import parse_monthly_holdings

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 讀取資料與解析持股
monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, df = parse_monthly_holdings("data/transactions.xlsx")

# 計算總持股與排序依據（依股票代號的總持股數量排序）
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

# 股票依總持股排序
sorted_codes = sorted(all_codes, key=lambda c: code_total[c], reverse=True)

# Streamlit Layout
st.set_page_config(layout="wide")
st.title("📊 每月持股變化總覽（疊加直方圖）")

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

            ax.set_title(f"{code} 每月持股數量")
            ax.set_xlabel("月")
            ax.set_ylabel("股數")
            ax.legend()
            if code_to_currency.get(code, "TWD") == "USD":
                ax.set_ylim(0, usd_max * 1.1)
            else:
                ax.set_ylim(0, twd_max * 1.1)

            ax.tick_params(axis='x', labelrotation=30)
            plt.tight_layout()
            st.pyplot(fig)
