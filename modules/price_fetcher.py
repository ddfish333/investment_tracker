import pandas as pd
import yfinance as yf
import os
from datetime import datetime

# 直接刪除不要的 .TW/.TWO
# 讓 Excel 資料表會指定完整代碼

print("📁 實際寫入目錄：", os.getcwd())
os.makedirs("data", exist_ok=True)

PRICE_SNAPSHOT_PATH = "data/monthly_price_history.parquet"

def fetch_monthly_prices_batch(codes, months):
    # 這裡不重新格式化代碼，直接使用來自 Excel 的代碼
    codes = sorted(set(str(code).strip().upper() for code in codes if code))

    if os.path.exists(PRICE_SNAPSHOT_PATH):
        price_df = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        price_df.index = pd.to_datetime(price_df.index).to_period("M")
    else:
        price_df = pd.DataFrame()

    price_df = price_df.copy()
    needed_months = set(months)
    missing_codes = []

    for code in codes:
        if code not in price_df.columns:
            missing_codes.append(code)
        else:
            missing_months = needed_months - set(price_df[code].dropna().index)
            if missing_months:
                missing_codes.append(code)

    if missing_codes:
        print("📡 從 Yahoo 補抓缺少的代碼：", missing_codes)
        start = min(months).strftime("%Y-%m-%d")
        end = (max(months) + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")

        for code in missing_codes:
            try:
                data = yf.download(
                    tickers=code,
                    start=start,
                    end=end,
                    interval="1mo",
                    auto_adjust=True,
                    progress=False
                )
                close = data["Close"]
                close.index = close.index.to_period("M")
                price_df[code] = price_df.get(code, pd.Series(dtype="float64"))
                price_df.update(close.to_frame(code))
            except Exception as e:
                print(f"❌ 無法取得 {code} 的價格：{e}")

    all_months = pd.period_range(min(months), max(months), freq="M")
    price_df = price_df.reindex(index=all_months).sort_index()
    price_df.to_parquet(PRICE_SNAPSHOT_PATH)

    return price_df

def fetch_month_end_fx(months, base="USD", quote="TWD"):
    # 模擬固定匯率
    return pd.Series([30.0] * len(months), index=months)
