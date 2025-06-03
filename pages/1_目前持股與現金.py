import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.express as px
import streamlit as st
from modules.asset_value import calculate_monthly_asset_value
from modules.fx_fetcher import fetch_monthly_fx
from config import TRANSACTION_FILE, PRICE_SNAPSHOT_PATH, CASH_ACCOUNT_FILE
from modules.cash_parser import get_latest_cash_detail, parse_cash_balances

# --- 頁面設定 ---
st.set_page_config(page_title="目前持股與現金", layout="wide")

# --- 載入資料 ---
raw_df = calculate_monthly_asset_value(
    filepath_transaction=TRANSACTION_FILE,
    filepath_cash=CASH_ACCOUNT_FILE
).raw_df

# --- 整理目前持股 ---
holdings = (
    raw_df.groupby(['出資者', '股票代號', '幣別'])['股數']
    .sum()
    .reset_index()
    .query("股數 > 0")
    .sort_values(by=['出資者', '股數'], ascending=[True, False])
)

# --- 抓取即時股價 ---
def get_latest_prices(tickers):
    try:
        price_data = yf.download(tickers=tickers, period="5d", interval="1d", progress=False)
        if isinstance(price_data.columns, pd.MultiIndex) and 'Close' in price_data.columns.levels[0]:
            close_df = price_data['Close'].ffill().iloc[-1]
            return close_df.to_dict(), price_data.index[-1].strftime("%Y-%m-%d")
        raise ValueError("無法取得正確格式的股價資料")
    except Exception:
        snapshot = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        snapshot = snapshot.reset_index() if 'date' not in snapshot.columns else snapshot
        latest_date = snapshot['date' if 'date' in snapshot.columns else '日期'].max()
        prices = snapshot[snapshot['date' if 'date' in snapshot.columns else '日期'] == latest_date]
        return prices.set_index('Ticker')['Close'].to_dict(), str(latest_date)

prices, price_date_str = get_latest_prices(holdings['股票代號'].unique().tolist())
holdings['即時股價'] = holdings['股票代號'].map(prices).fillna(0)
holdings['股價日期'] = price_date_str
holdings['市值（原幣）'] = holdings['股數'] * holdings['即時股價']

# --- 匯率處理 ---
today = datetime.today()
today_str = today.strftime("%Y-%m-%d")

def get_fx_rate():
    try:
        fx_df = fetch_monthly_fx([today_str[:7]])
        return fx_df.iloc[0]['USD'], today_str
    except Exception:
        return 32.0, "未知"

fx_rate_value, fx_date_str = get_fx_rate()
holdings['匯率'] = holdings['幣別'].apply(lambda c: fx_rate_value if c == 'USD' else 1.0)
holdings['市值（TWD）'] = holdings['市值（原幣）'] * holdings['匯率']
holdings['匯率日期'] = fx_date_str

# --- 現金資料 ---
cash_df = parse_cash_balances()
latest_month = cash_df.index.max()

# --- 真正的資料來源時間 ---
data_dates = {
    "💰 現金資料": latest_month.strftime("%Y-%m"),
    "📈 股價資料": price_date_str,
    "💱 匯率資料": fx_date_str
}
min_date = min(data_dates.values())

# --- 標題區塊 ---
st.title(f"📌 目前持股與現金（資料時間：{min_date}）")
st.caption("📌 各資料來源時間：")
for label, dt in data_dates.items():
    st.caption(f"{label} ➤ {dt}")

# --- 顯示表格 ---
st.subheader("📌 目前持股與即時股價")

def merge_us_holdings(df):
    is_us = df['幣別'] == 'USD'
    non_us = df[~is_us].copy()
    us_grouped = (
        df[is_us]
        .drop(columns=['出資者'])
        .groupby(['股票代號', '幣別', '即時股價', '股價日期', '匯率', '匯率日期'], as_index=False)
        .agg({'股數': 'sum', '市值（原幣）': 'sum', '市值（TWD）': 'sum'})
    )
    us_grouped.insert(0, '出資者', 'Sean/Lo')
    return pd.concat([non_us, us_grouped], ignore_index=True)

merged_holdings = merge_us_holdings(holdings)

st.dataframe(
    merged_holdings[['出資者', '股票代號', '股數', '即時股價', '股價日期', '市值（原幣）', '匯率', '市值（TWD）', '匯率日期']].style.format({
        '股數': "{:.2f}",
        '即時股價': "{:.2f}",
        '市值（原幣）': "{:,.0f}",
        '匯率': "{:.2f}",
        '市值（TWD）': "{:,.0f}"
    })
)

# --- 資產總和 ---
holdings['市場類別'] = holdings['幣別'].map({'TWD': '台股資產(TWD)', 'USD': '美股資產(USD)'})
summary = holdings.groupby(['出資者', '市場類別'])['市值（原幣）'].sum().unstack(fill_value=0)

cash_twd = cash_df.filter(like='_TWD_CASH').loc[latest_month]
cash_usd = cash_df.filter(like='_USD_CASH').loc[latest_month]

cash_twd.index = cash_twd.index.str.replace('_TWD_CASH', '')
cash_usd.index = cash_usd.index.str.replace('_USD_CASH', '')

# 從現金明細中取得分類資訊
cash_detail = get_latest_cash_detail()
usd_detail = cash_detail[cash_detail['幣別'] == 'USD']

# 若缺欄位，補上空值
if '帳戶類型' not in usd_detail.columns:
    usd_detail['帳戶類型'] = '未分類'

usd_saving = usd_detail[usd_detail['帳戶類型'] == '美金定存'].groupby('擁有者')['金額分攤'].sum()
usd_cash = usd_detail[usd_detail['帳戶類型'] != '美金定存'].groupby('擁有者')['金額分攤'].sum()

summary['台幣現金(TWD)'] = summary.index.map(lambda name: cash_twd.get(name, 0))
summary['美金現金(USD)'] = summary.index.map(lambda name: usd_cash.get(name, 0))
summary['美金定存(USD)'] = summary.index.map(lambda name: usd_saving.get(name, 0))
summary.loc['Total'] = summary.sum(numeric_only=True)

st.dataframe(summary.style.format("{:,.0f}"))

# --- 現金細項分類表格 ---
st.subheader("📋 最新月份現金分類明細")
latest_cash = get_latest_cash_detail()
st.dataframe(latest_cash.style.format({
    "金額": "{:,.0f}",
    "TWD金額": "{:,.0f}",
    "金額分攤": "{:,.0f}"
}))
