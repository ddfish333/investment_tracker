# pages/1_每月持股變化.py
import streamlit as st
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

# 顏色與背景設置
plt.style.use("dark_background")
plt.rcParams['axes.facecolor'] = '#0E1117'
plt.rcParams['figure.facecolor'] = '#0E1117'
plt.rcParams['axes.edgecolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['legend.facecolor'] = '#0E1117'

# 載入交易資料
monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, raw_df, color_map = \
    parse_monthly_holdings("data/transactions.xlsx")

st.set_page_config(layout="wide")
st.title("Sean & Lo 每月持股變化")

# 顏色定義
color_dict = {
    "Lo": "#87CEEB",
    "Sean": "#4682B4",
    "Sean/Lo": "#1E3F66",
}
gray_dict = {
    "Lo": "#D3D3D3",
    "Sean": "#A9A9A9",
    "Sean/Lo": "#696969",
}

def is_current_zero(code):
    """
    判斷最後一個月份持股是否為零
    """
    last = all_months[-1]
    return (
        monthly_Lo.at[last, code] +
        monthly_Sean.at[last, code] +
        monthly_SeanLo.at[last, code]
    ) == 0

def is_us_stock(code):
    """判斷是否為美股代碼，依原始交易標示欄位"""
    try:
        return raw_df.loc[raw_df['股票代號'] == code, '台股/美股'].iloc[0] == '美股'
    except:
        return str(code).upper().endswith("US")

# 計算台股與美股 Y 軸最大值
us_codes = [c for c in all_codes if is_us_stock(c)]
tw_codes = [c for c in all_codes if not is_us_stock(c)]

max_tw = max(
    (monthly_Lo[c] + monthly_Sean[c] + monthly_SeanLo[c]).max()
    for c in tw_codes
) * 1.1 if tw_codes else 0

max_us = max(
    (monthly_Lo[c] + monthly_Sean[c] + monthly_SeanLo[c]).max()
    for c in us_codes
) * 1.1 if us_codes else 0

# 按最後月份持股大小排序（大到小）
all_codes_sorted = sorted(
    all_codes,
    key=lambda c: (
        monthly_Lo[c].iloc[-1] +
        monthly_Sean[c].iloc[-1] +
        monthly_SeanLo[c].iloc[-1]
    ),
    reverse=True
)

# 顯示圖表
cols = st.columns(2)
for idx, code in enumerate(all_codes_sorted):
    with cols[idx % 2]:
        fig, ax = plt.subplots(figsize=(4.8, 2.2))
        current_zero = is_current_zero(code)
        palette = gray_dict if current_zero else color_dict

        ax.bar(monthly_Lo.index, monthly_Lo[code], color=palette["Lo"], label="Lo", width=20)
        ax.bar(
            monthly_Sean.index,
            monthly_Sean[code],
            bottom=monthly_Lo[code],
            color=palette["Sean"],
            label="Sean",
            width=20,
        )
        ax.bar(
            monthly_SeanLo.index,
            monthly_SeanLo[code],
            bottom=monthly_Lo[code] + monthly_Sean[code],
            color=palette["Sean/Lo"],
            label="Sean/Lo",
            width=20,
        )

        ax.set_title(f"{code} 持股變化圖", fontsize=10)
        ax.tick_params(axis='x', labelrotation=45, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        # 設定 Y 軸上限
        max_val = max_us if is_us_stock(code) else max_tw
        ax.set_ylim(0, max_val)
        ax.legend(fontsize=7)
        plt.tight_layout()
        st.pyplot(fig)
