# pages/2_每月資產價值.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value

st.set_page_config(layout="wide")

# 字體設定
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 計算 summary & detail
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# 顯示總資產
st.title("💰 每月資產價值（以台幣計價）")
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df)

# 各股明細
st.subheader("各股票資產走勢明細")
for code in detail_df.columns.levels[0]:
    st.markdown(f"### {code}")
    df_code = detail_df[code].rename(columns={'Joint':'Sean/Lo'})
    st.line_chart(df_code)
