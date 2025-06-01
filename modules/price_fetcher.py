# price_fetcher.py
import pandas as pd
import yfinance as yf
import logging
import os
from datetime import datetime
from config import PRICE_SNAPSHOT_PATH
from modules.time_utils import to_period_index, ensure_period_index

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_monthly_prices_batch(codes, months):
    # 清理輸入資料
    codes = sorted(set(str(code).strip().upper() for code in codes if code))
    months = to_period_index(months)  # ✅ 統一轉為 PeriodIndex

    # 讀取或建立價格快照資料表
    if os.path.exists(PRICE_SNAPSHOT_PATH):
        price_df = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        price_df = ensure_period_index(price_df)  # ✅ 防止混入 timestamp index
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

    # 從 Yahoo 補抓缺少資料
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

    # ✅ 補當月空白 row（避免圖表缺欄位）
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
