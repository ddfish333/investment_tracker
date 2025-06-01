# -*- coding: utf-8 -*-
import os
import platform
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from datetime import datetime
from modules.asset_value import calculate_monthly_asset_value
from modules.cash_parser import parse_cash_balances, parse_cash_detail

# --- Streamlit Page Setup ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 設定中文字體（根據作業系統自動調整）
if platform.system() == "Darwin":  # macOS
    font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
elif platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/msjh.ttc"
else:
    font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"

if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# --- 計算資產 ---
summary_df, detail_df, raw_df, monthly_Lo, monthly_Sean, monthly_Joint, price_df, detail_value_df, debug_records, fx_df, latest_debug_records = calculate_monthly_asset_value("data/transactions.xlsx")

# --- 顯示資產摘要 ---
sean_curr = summary_df.iloc[-1]['Sean']
lo_curr = summary_df.iloc[-1]['Lo']
total_curr = summary_df.iloc[-1]['Total']
sean_tw = summary_df.iloc[-1].get('Sean_TW', 0)
sean_us = summary_df.iloc[-1].get('Sean_US', 0)
lo_tw = summary_df.iloc[-1].get('Lo_TW', 0)
lo_us = summary_df.iloc[-1].get('Lo_US', 0)
total_tw = sean_tw + lo_tw
total_us = sean_us + lo_us

st.title(f"\U0001F4B8 每月資產價值")
st.markdown(f"**Sean**：TWD {sean_curr:,.0f}（台股 TWD {sean_tw:,.0f}／美股 TWD {sean_us:,.0f}）")
st.markdown(f"**Lo**：TWD {lo_curr:,.0f}（台股 TWD {lo_tw:,.0f}／美股 TWD {lo_us:,.0f}）")
st.markdown(f"**Sean&Lo**：TWD {total_curr:,.0f}（台股 TWD {total_tw:,.0f}／美股 TWD {total_us:,.0f}）")

# --- 總資產跑動 ---
st.subheader("Sean&Lo總資產")
summary_df_display = summary_df.copy()
summary_df_display.index = summary_df_display.index.astype(str)

# 加入篩選功能
default_selection = ['Sean', 'Lo', 'Total']
selected_lines = st.multiselect("請選擇要顯示的資產線", options=default_selection, default=default_selection)
if selected_lines:
    st.line_chart(summary_df_display[selected_lines])
else:
    st.info("請至少選擇一條資產線來顯示。")

# --- 各股票資產跑動詳細 ---
st.subheader("各股票資產跑動詳細")

if not isinstance(detail_value_df.columns, pd.MultiIndex):
    st.error("detail_value_df 的欄位不是 MultiIndex格式，無法分別顯示 Sean/Lo")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_value_df.xs(owner, axis=1, level='Owner').copy()

        if df.empty:
            st.warning(f"找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        df_display = df.copy().round(0).fillna(0).astype(int)
        df_display.columns.name = "stock"
        df_display.index = df_display.index.astype(str)
        df_display.index.name = "date"

        owner_curr = summary_df.iloc[-1][owner]
        st.markdown(f"#### {owner} 每月資產變化（目前資產 NT${owner_curr:,.0f} 元）")
        st.bar_chart(df_display)

# --- 現金資產展示區塊 ---
df = pd.read_excel("data/cash_accounts.xlsx", sheet_name="monthly_balance")
df["月份"] = pd.to_datetime(df["日期"], errors="coerce").dt.to_period("M")

records = []
for _, row in df.iterrows():
    month = row["月份"]
    amount = row["等值金額"]
    sean_ratio = row.get("Sean 出資比例", 0)
    lo_ratio = row.get("Lo 出資比例", 0)
    if row["擁有者"] == "Joint":
        if sean_ratio > 0:
            records.append({"月份": month, "擁有者": "Sean", "等值金額": amount * sean_ratio})
        if lo_ratio > 0:
            records.append({"月份": month, "擁有者": "Lo", "等值金額": amount * lo_ratio})
    else:
        records.append({"月份": month, "擁有者": row["擁有者"], "等值金額": amount})

expanded_df = pd.DataFrame(records)
all_months = pd.period_range(expanded_df["月份"].min(), expanded_df["月份"].max(), freq="M")
all_owners = ["Sean", "Lo"]
full_index = pd.MultiIndex.from_product([all_months, all_owners], names=["月份", "擁有者"])
cash_df = expanded_df.groupby(["月份", "擁有者"])["等值金額"].sum().reindex(full_index, fill_value=None).unstack()
cash_df = cash_df.sort_index().ffill().fillna(0)
cash_detail_series = parse_cash_detail()

# --- 修正每月帳戶明細：強制補齊月份與帳戶（使用 cash_df 作為月份來源） ---
all_months = cash_df.index
all_accounts = cash_detail_series.index.get_level_values(0).unique()
all_owners = ["Sean", "Lo", "Joint"]

full_idx = pd.MultiIndex.from_product([all_months, all_accounts], names=["月份", "帳戶"])
for owner in all_owners:
    if owner in cash_detail_series:
        df_owner = cash_detail_series[owner].reindex(full_idx, fill_value=None)
        cash_detail_series[owner] = df_owner.sort_index().groupby(level=1).ffill().fillna(0)

st.subheader("\U0001F4B3 每月現金餘額（總覽）")
cash_df_display = cash_df.sort_index(ascending=False)
st.dataframe(cash_df_display)

st.subheader("\U0001F4C2 每月各帳戶現金明細（分人）")
tabs = st.tabs(["Sean", "Lo", "Joint"])
owners = ["Sean", "Lo", "Joint"]

for i, owner in enumerate(owners):
    with tabs[i]:
        try:
            detail_df = cash_detail_series.loc[:, owner].unstack(fill_value=0)
            detail_df.index = detail_df.index.astype(str)
            detail_df = detail_df.sort_index(ascending=False)
            detail_df.insert(0, "總計", detail_df.sum(axis=1))
            st.markdown(f"#### {owner} 各帳戶每月現金餘額")
            st.dataframe(detail_df)
        except KeyError:
            st.warning(f"{owner} 沒有資料")

# --- 除錯：顯示原始表格 ---
st.subheader("\U0001F50D 除錯用資料表")
st.markdown("**原始交易紀錄**")
st.dataframe(raw_df)

# --- 合併匯率與股價表格 ---
st.markdown("**\U0001F4CA 每月匯率 + 股票價格（含最新價格）**")
st.caption("\U0001F4A1 匯率來自自動抓取 API，非固定值 30，若抓取失敗才會 fallback")

fx_df_df = fx_df.to_frame(name="USD/TWD 匯率") if isinstance(fx_df, pd.Series) else fx_df
fx_df_df.index = fx_df_df.index.to_timestamp()
price_df.index = price_df.index.to_timestamp()
combined_df = pd.concat([fx_df_df, price_df], axis=1)
combined_df.index = combined_df.index.astype(str)
combined_df = combined_df.sort_index(ascending=False)
st.dataframe(combined_df.round(4))

# --- 除錯：顯示最新價格換算明細（每月） ---
st.markdown("**每月價格換算明細（股數 x 價格 x 匯率） - 只顯示最新月份**")
debug_df = pd.DataFrame(debug_records)

if not debug_df.empty:
    latest_month = debug_df["月份"].max()
    latest_debug_df = debug_df[debug_df["月份"] == latest_month].copy()
    latest_debug_df["最新記錄日期"] = datetime.today().strftime("%Y-%m-%d")

    st.markdown("請選擇要顯示的擁有者")
    tabs = st.tabs(["Sean", "Lo"])
    owners = ["Sean", "Lo"]

    for i, owner in enumerate(owners):
        with tabs[i]:
            owner_df = latest_debug_df[
                (latest_debug_df["擁有者"] == owner) & (latest_debug_df["股數"] > 0)
            ]
            st.markdown(f"\U0001F4C5 最新月份：{latest_month}")
            if owner_df.empty:
                st.info("⚠️ 此月份該擁有者沒有持有股票")
            else:
                st.dataframe(owner_df)
else:
    st.info("目前沒有可顯示的價格換算紀錄。")
