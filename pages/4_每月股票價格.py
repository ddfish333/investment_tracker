import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd  # ⬆️ 加上 pandas
from modules.stock_monthlyprice import get_monthly_prices
from modules.fx_fetcher import fetch_monthly_fx  # 放在最上面

# ⭐️ 必須第一行啟用 Streamlit config
st.set_page_config(page_title="每月股票價格", layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if fm.findSystemFonts(fontpaths=[font_path]):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False

# --- Streamlit Setup ---
st.title("📈 每月股票價格 API 測試")

# 股票代碼輸入與時間範圍設定
symbol = st.text_input("請輸入股票代碼（如：2330.TW 或 AAPL）", value="2330.TW")
start_date = st.date_input("開始日期", value=pd.to_datetime("2019-01-01"))
end_date = st.date_input("結束日期")

# 抓資料
if st.button("取得價格資料", key="fetch_stock_data"):
    try:
        df = get_monthly_prices(symbol, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        df_display = df.sort_index(ascending=False)  # 顯示用（最新在上）
        df_plot = df.sort_index(ascending=True)      # 畫圖用（時間順序）

        st.success(f"成功取得 {symbol} 的月資料，共 {len(df)} 筆")
        st.line_chart(df_plot)
        st.dataframe(df_display)
    except Exception as e:
        st.error(f"❌ 無法取得資料：{e}")

if st.button("取得匯率資料", key="fetch_fx_data"):
    try:
        df = get_monthly_prices(symbol, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        df_display = df.sort_index(ascending=False)
        df_plot = df.sort_index(ascending=True)

        st.success(f"成功取得 {symbol} 的月資料，共 {len(df)} 筆")
        st.line_chart(df_plot)
        st.dataframe(df_display)

        # ⬇️ 加入 USD 匯率資料
        df_fx = fetch_monthly_fx(df.index.to_period("M").unique())
        df_merged = df.join(df_fx[["USD"]], how="left")
        df_merged_display = df_merged.sort_index(ascending=False)
        df_merged_plot = df_merged.sort_index(ascending=True)

        st.subheader("📉 匯率合併資料（含 USD 匯率）")
        st.line_chart(df_merged_plot["USD"])
        st.dataframe(df_merged_display)

    except Exception as e:
        st.error(f"❌ 無法取得資料：{e}")