# test_fx_fetch.py
import pandas as pd
import yfinance as yf
import os

FX_SNAPSHOT_PATH = "data/monthly_fx_history.parquet"

def fetch_monthly_fx_fixed(months, default_rate=30.0):
    unique_months = sorted(set(months))
    result = {}

    for month in unique_months:
        start_date = month.to_timestamp(how="start")
        end_date = month.to_timestamp(how="end") + pd.Timedelta(days=1)

        try:
            data = yf.download("TWD=X", start=start_date, end=end_date, progress=False)
            close = data["Close"].dropna()
            if not close.empty:
                median_rate = round(float(close.median()), 4)
                result[month] = {"USD": median_rate, "來源": "Yahoo Finance"}
                print(f"✅ {month} 匯率 ➜ {median_rate}")
                continue
        except Exception as e:
            print(f"❌ {month} 抓取錯誤：{e}")

        print(f"⚠️ {month} 匯率設為預設值 {default_rate}")
        result[month] = {"USD": default_rate, "來源": "預設值"}

    df = pd.DataFrame.from_dict(result, orient="index")
    df.index.name = "月份"
    df["TWD"] = 1.0

    os.makedirs(os.path.dirname(FX_SNAPSHOT_PATH), exist_ok=True)
    df.to_parquet(FX_SNAPSHOT_PATH)
    print(f"💾 已儲存至 {FX_SNAPSHOT_PATH}")
    return df

if __name__ == "__main__":
    test_months = pd.period_range("2019-01", "2025-6", freq="M")
    fx_df = fetch_monthly_fx_fixed(test_months)
    print(fx_df)
