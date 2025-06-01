# price_fetcher.py
import pandas as pd
import yfinance as yf
import logging
import os
from datetime import datetime

try:
    from config import PRICE_SNAPSHOT_PATH
except ImportError:
    PRICE_SNAPSHOT_PATH = "data/monthly_price_history.parquet"

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_monthly_prices_batch(codes, months):
    codes = sorted(set(str(code).strip().upper() for code in codes if code))
    months = [pd.Period(m, freq="M") for m in months]

    if os.path.exists(PRICE_SNAPSHOT_PATH):
        price_df = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        if not isinstance(price_df.index, pd.PeriodIndex):
            price_df.index = pd.to_datetime(price_df.index).to_period("M")
    else:
        price_df = pd.DataFrame(index=pd.period_range(min(months), max(months), freq="M"))

    price_df = price_df.copy()
    needed_months = pd.period_range(min(months), max(months), freq="M")
    missing_codes = []

    for code in codes:
        if code not in price_df.columns:
            missing_codes.append(code)
        else:
            existing_months = set(price_df[code].dropna().index.to_list())
            missing_months = set(needed_months) - existing_months
            if missing_months:
                missing_codes.append(code)

    if missing_codes:
        logger.info("📡 從 Yahoo 補抓缺少的代碼：%s", missing_codes)
        for code in missing_codes:
            for month in needed_months:
                start_date = pd.Timestamp(month.start_time.date())
                end_date = pd.Timestamp(month.end_time.date()) + pd.Timedelta(days=1)
                try:
                    data = yf.download(
                        tickers=code,
                        start=start_date,
                        end=end_date,
                        interval="1d",
                        auto_adjust=True,
                        progress=False
                    )
                    if data.empty:
                        logger.warning("⚠️ 無資料：%s (%s ~ %s)", code, start_date, end_date)
                        continue
                    close = data["Close"].dropna()
                    if not close.empty:
                        price = float(close.iloc[-1])
                        price_df.loc[month, code] = price
                        logger.info("✅ %s @ %s ➔ %.2f", code, month, price)
                except Exception as e:
                    logger.error("❌ 無法取得 %s 的價格：%s", code, e)

    # ✅ PATCH: 補當月空缺，如果快照沒有最新月資料，就從上一月補一份並留空價格
    today_label = pd.Period(datetime.today(), freq="M")
    if today_label not in price_df.index:
        logger.info("🧩 補上當月空白資料：%s", today_label)
        last_month = price_df.index.max()
        price_df.loc[today_label] = price_df.loc[last_month] * pd.NA

    price_df = price_df.reindex(index=needed_months.union([today_label])).sort_index()

    if not price_df.empty:
        os.makedirs(os.path.dirname(PRICE_SNAPSHOT_PATH), exist_ok=True)
        price_df = price_df.astype("float64")
        price_df.to_parquet(PRICE_SNAPSHOT_PATH)
        logger.info("💾 價格快照已儲存至：%s", PRICE_SNAPSHOT_PATH)

    return price_df
