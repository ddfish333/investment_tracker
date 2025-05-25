# pages/4_每月股票價格.py
```python
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.stock_monthlyprice import get_stock_monthly_prices

# --- Streamlit Page: 每月股票價格 ---
st.set_page_config(layout="wide")

# 中文字體設定
def set_chinese_font():
    font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(font_path):
        prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = prop.get_name()
    else:
        plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False

set_chinese_font()

# 選擇要檢視的股票代號
default_list = ['2330', 'TSLA']
stocks = st.multiselect('選擇要檢視的股票（台股 / 美股後綴US）', options=default_list, default=default_list)

if stocks:
    # 取得每月台幣價格
    df_prices = get_stock_monthly_prices(stocks, "data/transactions.xlsx")

    st.title("📊 每月股票收盤價（以台幣計價）")

    # 單張折線圖顯示所有選項
    st.subheader("整體折線圖")
    st.line_chart(df_prices)

    # 個別折線圖與表格
    for code in stocks:
        st.subheader(f"{code} 月末收盤價走勢")
        st.line_chart(df_prices[[code]])

    st.subheader("原始數據表格")
    st.dataframe(df_prices)
