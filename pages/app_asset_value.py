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

# 取得持股資料
monthly_holding_dict = parse_monthly_holdings("data/transactions.xlsx")

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("📊 每月持股變化總覽（疊加直方圖）")

# 統一 Y 軸上限：三者合併最大值 + 10%
combined_sum = sum([df.fillna(0) for df in monthly_holding_dict.values()])
y_max = combined_sum.max().max() * 1.1

# 所有股票代號
all_codes = sorted(set().union(*[df.columns for df in monthly_holding_dict.values()]))

# 每4張一批
chunk_size = 4
chunks = [all_codes[i:i + chunk_size] for i in range(0, len(all_codes), chunk_size)]

for chunk in chunks:
    cols = st.columns(2)
    for i, code in enumerate(chunk):
        with cols[i % 2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            bottom = None
            for label, df in monthly_holding_dict.items():
                if code in df.columns:
                    data = df[code].fillna(0)
                    ax.bar(df.index, data, label=label, bottom=bottom, width=25)
                    if bottom is None:
                        bottom = data.copy()
                    else:
                        bottom += data

            ax.set_title(f"{code} 每月持股數量")
            ax.set_xlabel("月")
            ax.set_ylabel("股數")
            ax.set_ylim(0, y_max)
            ax.tick_params(axis='x', labelrotation=30)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
