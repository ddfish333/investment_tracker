# -*- coding: utf-8 -*-
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import yfinance as yf
from datetime import datetime
from modules.asset_value import calculate_monthly_asset_value, fetch_month_end_fx

# --- Streamlit Page Setup ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# --- 計算資產 ---
summary_df, detail_df, raw_df, monthly_Lo, monthly_Sean, monthly_Joint, price_df = calculate_monthly_asset_value("data/transactions.xlsx")

# --- 抓取最新價格並更新最後一筆資產資料 ---
def fetch_latest_prices(codes):
    tickers = [c if c.endswith('.TW') or c.endswith('.TWO') or c.isalpha() else f"{c}.TW" for c in codes]
    data = yf.download(tickers, period="5d", interval="1d", auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        return data['Close'].ffill().iloc[-1].to_dict()
    else:
        return data['Close'].ffill().to_dict()

all_codes = detail_df.columns.get_level_values('Code').unique().tolist()
latest_prices = fetch_latest_prices(all_codes)

# 建立股票代碼與市場類別的對照表
market_map = raw_df.drop_duplicates('股票代號').set_index('股票代號')['台股/美股'].to_dict()
currency_map = raw_df.drop_duplicates('股票代號').set_index('股票代號')['幣別'].to_dict()

# 建立新 row 保留結構
new_row = pd.Series(0, index=summary_df.columns)

# 抓取匯率
latest_month = pd.Timestamp.today().to_period('M')
fx_series = fetch_month_end_fx([latest_month])
fx_rate = fx_series.iloc[0] if not fx_series.empty else 30.0

# 資產明細除錯表
debug_records = []

for code in all_codes:
    for owner in ['Sean', 'Lo']:
        col = (code, owner)
        if col in detail_df.columns:
            qty = detail_df[col].iloc[-1]
            price = latest_prices.get(code)
            base_code = code.replace('.TW', '').replace('.TWO', '')
            market = market_map.get(base_code, '台股')
            currency = currency_map.get(base_code, 'TWD')
            if price is not None and not pd.isna(qty):
                fx = fx_rate if currency == 'USD' else 1
                value = qty * price * fx
                new_row[owner] += value
                if f"{owner}_TW" in new_row.index and market == "台股":
                    new_row[f"{owner}_TW"] += value
                elif f"{owner}_US" in new_row.index and market == "美股":
                    new_row[f"{owner}_US"] += value
                debug_records.append({
                    "代號": code,
                    "股數": qty,
                    "價格": price,
                    "匯率": fx,
                    "市值": value,
                    "擁有者": owner
                })

# 合計總資產
new_row['Total'] = new_row.get('Sean', 0) + new_row.get('Lo', 0)

# 加入新的一筆資料
summary_df.loc[pd.Timestamp.today().to_period('M')] = new_row
summary_df = summary_df.sort_index()

# 讀出最新資產資訊
sean_curr = new_row['Sean']
lo_curr = new_row['Lo']
total_curr = new_row['Total']
sean_tw = new_row.get('Sean_TW', 0)
sean_us = new_row.get('Sean_US', 0)
lo_tw = new_row.get('Lo_TW', 0)
lo_us = new_row.get('Lo_US', 0)
total_tw = sean_tw + lo_tw
total_us = sean_us + lo_us

# --- 顯示資產摘要 ---
st.title(f"\U0001F4B8 每月資產價值（以台幣計值）")
st.markdown(f"**Sean**：NT${sean_curr:,.0f} 元（台股 NT${sean_tw:,.0f}／美股 NT${sean_us:,.0f}）")
st.markdown(f"**Lo**：NT${lo_curr:,.0f} 元（台股 NT${lo_tw:,.0f}／美股 NT${lo_us:,.0f}）")
st.markdown(f"**合計總資產**：NT${total_curr:,.0f} 元（台股 NT${total_tw:,.0f}／美股 NT${total_us:,.0f}）")

# --- 總資產跑動 ---
st.subheader("總資產跑動：Sean vs Lo vs Total")
st.line_chart(summary_df[['Sean', 'Lo', 'Total']])

# --- 各股票資產跑動詳細 ---
st.subheader("各股票資產跑動詳細")

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("detail_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.xs(owner, axis=1, level='Owner').copy()

        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df_display = df.copy().round(0).fillna(0).astype(int)
        df_display.columns.name = "stock"
        df_display.index = df_display.index.strftime("%Y-%m")
        df_display.index.name = "date"

        owner_curr = new_row[owner]
        st.markdown(f"#### {owner} 每月資產變化（目前資產 NT${owner_curr:,.0f} 元）")
        st.bar_chart(df_display)

# --- 除錯：顯示原始表格 ---
st.subheader("\U0001F50D 除錯用資料表")
st.markdown("**原始交易紀錄**")
st.dataframe(raw_df)

st.markdown("**Yahoo 月底股價資料（含最新價格）**")
latest_label = datetime.today().strftime("最新價格（%Y/%m/%d）")
latest_prices_df = pd.Series(latest_prices).to_frame(latest_label)
latest_prices_df.index.name = price_df.columns.name if isinstance(price_df.columns, pd.MultiIndex) else 'Ticker'
latest_prices_df = latest_prices_df.T
combined_price_df = pd.concat([price_df, latest_prices_df])
combined_price_df.index = combined_price_df.index.map(lambda x: str(x))
combined_price_df = combined_price_df.sort_index(ascending=False)
st.dataframe(combined_price_df.round(2))

# --- 除錯：顯示最新價格換算明細表 ---
st.markdown("**最新價格換算明細**")
st.dataframe(pd.DataFrame(debug_records))
