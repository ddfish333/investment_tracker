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

def fetch_monthly_prices_batch(codes, months, overwrite=False):
    # 清理輸入資料
    codes = sorted(set(str(code).strip().upper() for code in codes if code))
    months = to_period_index(months)  # ✅ 統一轉為 PeriodIndex

    # 讀取或建立價格快照資料表
    if os.path.exists(PRICE_SNAPSHOT_PATH):
        stock_price_df = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        stock_price_df = ensure_period_index(stock_price_df)  # ✅ 防止添入 timestamp index
    else:
        stock_price_df = pd.DataFrame()

    stock_price_df = stock_price_df.copy()
    needed_months = set(months)

    for code in codes:
        if code not in stock_price_df.columns:
            stock_price_df[code] = pd.NA

        date_col = "資料日期"
        if date_col not in stock_price_df.columns:
            stock_price_df[date_col] = pd.NaT

        existing_months = set(stock_price_df[code].dropna().index.to_list())
        if overwrite:
            code_target_months = sorted(needed_months)
        else:
            code_target_months = sorted(needed_months - existing_months)

        for month in code_target_months:
            logger.info("📱 從 Yahoo 補抓 %s @ %s", code, month)
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
                    price_date = close.index[-1].date()
                    if month not in stock_price_df.index:
                        stock_price_df.loc[month] = pd.Series(dtype='float64')
                    stock_price_df.at[month, code] = price
                    stock_price_df.at[month, date_col] = pd.Timestamp(price_date)
                    logger.info("✅ %s @ %s ➔ %.2f (%s)", code, month, price, price_date)
            except Exception as e:
                logger.error("❌ 無法取得 %s 的價格：%s", code, e)

    stock_price_df = stock_price_df.sort_index()

    # 【修正】只轉換數值欄（排除 '資料日期'）
    value_cols = [col for col in stock_price_df.columns if col != "資料日期"]
    stock_price_df[value_cols] = stock_price_df[value_cols].apply(pd.to_numeric, errors='coerce')

    if "資料日期" in stock_price_df.columns:
        stock_price_df["資料日期"] = pd.to_datetime(stock_price_df["資料日期"], errors='coerce')

    if not stock_price_df.empty:
        os.makedirs(os.path.dirname(PRICE_SNAPSHOT_PATH), exist_ok=True)
        stock_price_df.to_parquet(PRICE_SNAPSHOT_PATH)
        logger.info("📀 價格快照已儲存至：%s", PRICE_SNAPSHOT_PATH)

    return stock_price_df
