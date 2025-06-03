# pages/1_目前持股與現金.py
import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
from modules.asset_value import calculate_monthly_asset_value
from modules.fx_fetcher import fetch_monthly_fx
from config import TRANSACTION_FILE, PRICE_SNAPSHOT_PATH

# --- 頁面設定 ---
st.set_page_config(page_title="目前持股與現金", layout="wide")

# --- 顯示日期標題 ---
today = datetime.today()
today_str = today.strftime("%Y-%m-%d")
st.title(f"📌 目前持股與現金（資料時間：{today_str}）")

# --- 載入資料 ---
_, _, _, raw_df, _, _, _, _ = calculate_monthly_asset_value(TRANSACTION_FILE)

# --- 計算目前持股數量並合併即時股價與匯率 ---
st.subheader("📌 目前持股與即時股價")

# Step 1: 整理目前持股
holdings = (
    raw_df.groupby(['出資者', '股票代號', '幣別'])['股數']
    .sum()
    .reset_index()
    .query("股數 > 0")
    .sort_values(by=['出資者', '股數'], ascending=[True, False])
)

# Step 2: 抓取即時股價或快照
tickers = holdings['股票代號'].unique().tolist()
price_date_str = ""
try:
    price_data = yf.download(tickers=tickers, period="5d", interval="1d", progress=False)
    if isinstance(price_data.columns, pd.MultiIndex) and 'Close' in price_data.columns.levels[0]:
        close_df = price_data['Close'].ffill().iloc[-1]
        prices = close_df.to_dict()
        price_date_str = price_data.index[-1].strftime("%Y-%m-%d")
    else:
        raise ValueError("無法取得正確格式的股價資料")
except Exception:
    snapshot = pd.read_parquet(PRICE_SNAPSHOT_PATH)
    snapshot = snapshot.reset_index() if 'date' not in snapshot.columns else snapshot
    date_col = 'date' if 'date' in snapshot.columns else '日期'
    latest_date = snapshot[date_col].max()
    prices = snapshot[snapshot[date_col] == latest_date].set_index('Ticker')['Close'].to_dict()
    price_date_str = str(latest_date)

# Step 3: 合併即時價格
holdings['即時股價'] = holdings['股票代號'].map(prices).fillna(0)
holdings['股價日期'] = price_date_str
holdings['市值（原幣）'] = holdings['股數'] * holdings['即時股價']

# Step 4: 匯率處理
try:
    fx_df = fetch_monthly_fx([today_str[:7]])
    fx_rate_value = fx_df.iloc[0]['USD']
    fx_date_str = today_str
except Exception:
    fx_rate_value = 32.0
    fx_date_str = "未知"

holdings['匯率'] = holdings['幣別'].apply(lambda c: fx_rate_value if c == 'USD' else 1.0)
holdings['市值（TWD）'] = holdings['市值（原幣）'] * holdings['匯率']
holdings['匯率日期'] = fx_date_str

# Step 5: 顯示表格
st.dataframe(
    holdings[['出資者', '股票代號', '股數', '即時股價', '股價日期', '市值（原幣）', '匯率', '市值（TWD）', '匯率日期']].style.format({
        '股數': "{:.2f}",
        '即時股價': "{:.2f}",
        '市值（原幣）': "{:,.0f}",
        '匯率': "{:.2f}",
        '市值（TWD）': "{:,.0f}"
    })
)

# Step 6: 顯示台股與美股原幣合計
st.subheader("📊 台股與美股原幣市值合計")
category_map = {
    'TWD': '台股',
    'USD': '美股'
}
holdings['市場類別'] = holdings['幣別'].map(category_map)

summary = holdings.groupby(['出資者', '市場類別'])['市值（原幣）'].sum().unstack(fill_value=0)
total_row = pd.DataFrame(summary.sum(axis=0)).T
total_row.index = ['Total']
summary = pd.concat([summary, total_row])
st.dataframe(summary.style.format("{:,.0f}"))
