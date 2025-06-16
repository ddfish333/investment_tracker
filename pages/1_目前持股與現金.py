import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.express as px
from modules.asset_value import calculate_monthly_asset_value
from modules.fx_fetcher import get_latest_fx_rate
from config import TRANSACTION_FILE, PRICE_SNAPSHOT_PATH, CASH_ACCOUNT_FILE
from modules.cash_parser import get_latest_cash_detail, parse_cash_balances

# --- 頁面設定 ---
st.set_page_config(page_title="目前持股與現金", layout="wide")

# --- 載入資料（改為完整結果物件） ---
result = calculate_monthly_asset_value(
    filepath_transaction=TRANSACTION_FILE,
    filepath_cash=CASH_ACCOUNT_FILE
)
raw_df = result.raw_df
summary_df = result.summary_df
summary_stock_df = result.summary_stock_df
summary_cash_df = result.summary_cash_df
stock_price_df = result.stock_price_df
fx_df = result.fx_df

# --- 從 snapshot 中抓取日期資訊 ---
latest_month = stock_price_df.index.max()
price_date_str = stock_price_df.loc[latest_month, '資料日期'].strftime('%Y-%m-%d')

# --- 匯率資訊 ---
fx_rate_value = fx_df.loc[latest_month, 'USD']
fx_date_str = fx_df.loc[latest_month, '來源'] if '來源' in fx_df.columns else price_date_str

# --- 現金資料 ---
cash_df = parse_cash_balances()
latest_month_cash = cash_df.index.max()

# --- 真正的資料來源時間 ---
data_dates = {
    "💰 現金資料": latest_month_cash.strftime("%Y-%m"),
    "📈 股價資料(美股)": price_date_str,
    "💱 匯率資料": fx_date_str
}
min_date = min(data_dates.values())

# --- 標題區塊 ---
st.title(f"📌 目前持股與現金（資料時間：{min_date}）")
st.caption("📌 各資料來源時間：")
for label, dt in data_dates.items():
    st.caption(f"{label} ➔ {dt}")

# --- 顯示表格 ---
st.subheader("📌 目前持股與即時股價")
holdings = result.raw_df.groupby(['出資者', '股票代號', '幣別'])['股數'].sum().reset_index()
latest_prices = stock_price_df.loc[latest_month].drop('資料日期')
holdings['即時股價'] = holdings['股票代號'].map(latest_prices.to_dict()).fillna(0)
holdings['股價日期'] = price_date_str
holdings['市值（原幣）'] = holdings['股數'] * holdings['即時股價']
holdings['匯率'] = holdings['幣別'].apply(lambda c: fx_rate_value if c == 'USD' else 1.0)
holdings['市值（TWD）'] = holdings['市值（原幣）'] * holdings['匯率']
holdings['匯率日期'] = fx_date_str

st.dataframe(
    holdings[['出資者', '股票代號', '股數', '即時股價', '股價日期', '市值（原幣）', '匯率', '市值（TWD）', '匯率日期']].style.format({
        '股數': "{:.0f}",
        '即時股價': "{:.2f}",
        '市值（原幣）': "{:,.0f}",
        '匯率': "{:.2f}",
        '市值（TWD）': "{:,.0f}"
    })
)

# --- 資產總和 ---
holdings['市場類別_TWD'] = holdings['幣別'].map({'TWD': '台股資產(TWD)', 'USD': '美股資產(TWD)'})
holdings['市場類別_USD'] = holdings['幣別'].map({'USD': '美股資產(USD)'})

summary_TWD = holdings.groupby(['出資者', '市場類別_TWD'])['市值（TWD）'].sum().unstack(fill_value=0)
summary_USD = holdings.groupby(['出資者', '市場類別_USD'])['市值（原幣）'].sum().unstack(fill_value=0)
summary_USD = holdings.dropna(subset=['市場類別_USD']) \
    .groupby(['出資者', '市場類別_USD'])['市值（原幣）'].sum().unstack(fill_value=0)

# 修正空欄位名稱為美股資產(USD)
# 預設就不產生空欄位，因此不需要 rename
pass

# 移除重複欄位再 join
if "美股資產(USD)" in summary_TWD.columns:
    summary_TWD = summary_TWD.drop(columns=["美股資產(USD)"])

summary = summary_TWD.join(summary_USD, how='outer').fillna(0).reset_index()

# 加入現金資料明細
cash_detail = get_latest_cash_detail()
cash_df_summary = cash_detail.pivot_table(
    index='擁有者',
    columns='分類',
    values='金額分攤',
    aggfunc='sum'
).fillna(0)

summary['美金現金(USD)'] = summary['出資者'].map(lambda x: cash_df_summary.loc[x, ['美金活存', '美金投資帳戶']].sum() / fx_rate_value if x in cash_df_summary.index else 0)
summary['美金現金(TWD)'] = summary['美金現金(USD)'] * fx_rate_value
summary['美金定存(USD)'] = summary['出資者'].map(lambda x: cash_df_summary.loc[x, ['美金定存']].sum() / fx_rate_value if x in cash_df_summary.index else 0)
summary['美金定存(TWD)'] = summary['美金定存(USD)'] * fx_rate_value
summary['台幣現金(TWD)'] = summary['出資者'].map(lambda x: cash_df_summary.loc[x, ['台幣活存', '台幣投資帳戶']].sum() if x in cash_df_summary.index else 0)

# --- 加入總資產（TWD） ---
summary['總資產(TWD)'] = (
    summary.get('台股資產(TWD)', 0) +
    summary.get('美股資產(TWD)', 0) +
    summary.get('美金現金(TWD)', 0) +
    summary.get('美金定存(TWD)', 0) +
    summary.get('台幣現金(TWD)', 0)
)

# --- 總和列處理區塊 PATCH ---

# Debug: 檢查欄位是否唯一
if not summary.columns.is_unique:
    st.warning(f"⚠️ summary 欄位名稱出現重複，將自動去除：{summary.columns[summary.columns.duplicated()].tolist()}")
    summary = summary.loc[:, ~summary.columns.duplicated()]  # 移除重複欄位

# 建立總和列
float_cols = summary.select_dtypes(include='number').columns

# 避免非數字欄位被誤加總，例如出資者/擁有者
total_row = {col: summary[col].sum() if col in float_cols else 'Total' for col in summary.columns}

# ✅ 直接 concat，不使用 ParserBase 去 dedup（避免 AttributeError）
summary = pd.concat([summary, pd.DataFrame([total_row])], ignore_index=True)

# 顯示
st.dataframe(summary.style.format({col: "{:,.0f}" for col in float_cols}))

# --- 現金細項分類表格 ---
st.subheader("📋 最新月份現金分類明細")
latest_cash = get_latest_cash_detail()
st.dataframe(latest_cash.style.format({
    "金額": "{:,.0f}",
    "TWD金額": "{:,.0f}",
    "金額分攤": "{:,.0f}"
}))