# modules/asset_value.py
import pandas as pd
from modules.price_fetcher import fetch_month_end_prices, fetch_month_end_fx
from modules.holding_parser import parse_monthly_holdings

def calculate_monthly_asset_value(transaction_path):
    """
    計算並回傳：
      - summary_df (index=months，欄位為 Lo, Sean): 各自持股台幣價值總和
      - detail_df (index=months，MultiIndex 欄位 (code, owner)): 各支股票、各人的台幣持股價值
    """
    # 解包 parse_monthly_holdings 的返回值
    monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months, *_ = parse_monthly_holdings(transaction_path)

    # 抓取月末股價與匯率
    price_df = fetch_month_end_prices(all_codes, all_months)
    fx_series = fetch_month_end_fx(all_months)

    # 構建 detail DataFrame
    parts = []
    for owner, holdings in zip(["Lo", "Sean", "Joint"], [monthly_Lo, monthly_Sean, monthly_SeanLo]):
        val = holdings * price_df
        # 美股以 USD 轉 TWD
        mask_us = [str(c).endswith("US") for c in all_codes]
        if any(mask_us):
            val.loc[:, mask_us] = val.loc[:, mask_us].multiply(fx_series, axis=0)
        # 建立 MultiIndex
        val.columns = pd.MultiIndex.from_product([all_codes, [owner]])
        parts.append(val)

    detail_df = pd.concat(parts, axis=1).sort_index(axis=1)

    # 計算 summary: 每人資產 = 自有 + Joint/2
    half_joint = detail_df.xs('Joint', axis=1, level=1) / 2
    lo_total = detail_df.xs('Lo', axis=1, level=1).add(half_joint, fill_value=0).sum(axis=1)
    sean_total = detail_df.xs('Sean', axis=1, level=1).add(half_joint, fill_value=0).sum(axis=1)
    summary_df = pd.DataFrame({'Lo': lo_total, 'Sean': sean_total}, index=all_months)

    return summary_df, detail_df


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

# Debug: 檢查個股每月股價
from modules.holding_parser import parse_monthly_holdings
from modules.price_fetcher import fetch_month_end_prices

# 取出所有月份，並抓 2330 (台股) 及 QQQ (美股) 的月末股價
_, _, _, codes, months, *_ = parse_monthly_holdings("data/transactions.xlsx")
# 這裡只傳想檢查的兩支
price_check = fetch_month_end_prices(["2330", "QQQ"], months)
st.subheader("🔍 月末收盤價檢查：2330 與 QQQ")
st.dataframe(price_check)

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
