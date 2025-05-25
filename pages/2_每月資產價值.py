# pages/2_\u6bcf\u6708\u8cc7\u7522\u50f9\u503c.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from modules.asset_value import calculate_monthly_asset_value

# --- Streamlit Page Setup ---
st.set_page_config(page_title=u"\u6bcf\u6708\u8cc7\u7522\u50f9\u503c", layout="wide")
st.title("\ud83d\udcb0 \u6bcf\u6708\u8cc7\u7522\u660e\u7d30 (\u4ee5\u53f0\u5e63\u8a08\u50f9)")

# --- Font Setup ---
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if font_path:
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = prop.get_name()
plt.rcParams["axes.unicode_minus"] = False

# --- Load Data & Calculate ---
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# --- Show Total Asset Trend ---
st.subheader(f"\u7e3d\u8cc7\u7522\u8d70\u52e2: Lo vs Sean")
st.line_chart(summary_df)

# --- Show Each Stock Trend as Cards ---
st.subheader("\u5404\u500b\u80a1\u7968\u8cc7\u7522\u8d70\u52e2\u660e\u7d30")

# 計算目前各持股最後月份的總價值，用於排序
last_month = detail_df.index[-1]
latest_values = detail_df.loc[last_month]
total_per_stock = latest_values.groupby("Code").sum().sum(level=0)
nonzero_stocks = total_per_stock[total_per_stock > 0].index.tolist()
zero_stocks = total_per_stock[total_per_stock == 0].index.tolist()

# 排序順序: 現有持股在前，已清倉的在後
sorted_codes = nonzero_stocks + zero_stocks

# 卡片式顯示每一個股票的走勢圖
for code in sorted_codes:
    sub_df = detail_df.xs(code, level="Code")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(sub_df.index, sub_df["Lo"], label="Lo")
    ax.plot(sub_df.index, sub_df["Sean"], label="Sean")
    ax.plot(sub_df.index, sub_df["Sean/Lo"], label="Sean/Lo")
    ax.set_title(f"{code} \u8cc7\u7522\u8d70\u52e2\u5716", fontsize=12)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=8)

    if code in zero_stocks:
        for line in ax.lines:
            line.set_alpha(0.2)
        ax.set_title(f"{code} \u5df2\u552e\u7a7a", fontsize=12, color="gray")

    st.pyplot(fig)
