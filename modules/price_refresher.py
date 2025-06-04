import pandas as pd
import yfinance as yf
import os
import logging
from datetime import datetime
from config import PRICE_SNAPSHOT_PATH, FX_SNAPSHOT_PATH
from modules.time_utils import ensure_period_index
from modules.fx_fetcher import fetch_monthly_fx  # ✅ 加入匯率更新模組

# --- 設定 logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refresh_current_month_prices(codes):
    """
    重新抓取「當月」的股價與匯率（以今天為基準），並更新到快照檔中。
    """
    if not codes:
        logger.warning("❗ 未提供任何股票代碼，略過刷新。")
        return

    # 今日的「月份」
    today = pd.Timestamp.today()
    current_month = today.to_period("M")

    # 嘗試讀取股價快照檔
    if os.path.exists(PRICE_SNAPSHOT_PATH):
        stock_price_df = pd.read_parquet(PRICE_SNAPSHOT_PATH)
        stock_price_df = ensure_period_index(stock_price_df)
    else:
        stock_price_df = pd.DataFrame()

    stock_price_df = stock_price_df.copy()

    # 刪除當月股價資料
    if current_month in stock_price_df.index:
        logger.info("🧹 移除舊的當月股價資料 (%s)", current_month)
        stock_price_df.drop(index=current_month, inplace=True)

    # 確保欄位都有
    for code in codes:
        if code not in stock_price_df.columns:
            stock_price_df[code] = pd.NA

    # 抓取今天的價格
    for code in codes:
        logger.info("📥 抓取 %s 的今日價格 (%s)", code, today.date())
        try:
            data = yf.download(
                tickers=code,
                start=today,
                end=today + pd.Timedelta(days=1),
                interval="1d",
                auto_adjust=True,
                progress=False
            )
            if data.empty or "Close" not in data:
                logger.warning("⚠️ 無法取得 %s 的資料", code)
                continue
            close = data["Close"].dropna()
            if close.empty:
                logger.warning("⚠️ %s 沒有可用收盤價", code)
                continue
            price = float(close.iloc[-1])
            if current_month not in stock_price_df.index:
                stock_price_df.loc[current_month] = pd.Series(dtype='float64')
            stock_price_df.at[current_month, code] = price
            logger.info("✅ %s 當月價格為 %.2f", code, price)
        except Exception as e:
            logger.error("❌ 抓取 %s 價格時出錯：%s", code, e)

    # 儲存 parquet
    if not stock_price_df.empty:
        os.makedirs(os.path.dirname(PRICE_SNAPSHOT_PATH), exist_ok=True)
        stock_price_df = stock_price_df.astype("float64")
        stock_price_df.to_parquet(PRICE_SNAPSHOT_PATH)
        logger.info("📀 已更新價格快照至：%s", PRICE_SNAPSHOT_PATH)

    # --- 刪除當月匯率資料 ---
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
        fx_df = fx_df.copy()
        if current_month in fx_df.index:
            logger.info("🧹 移除舊的匯率資料 (%s)", current_month)
            fx_df.drop(index=current_month, inplace=True)
        fx_df.to_parquet(FX_SNAPSHOT_PATH)  # ✅ 確保有寫回檔案

    # 補抓當月匯率並寫入快照
    try:
        new_fx_df = fetch_monthly_fx([current_month])
        if os.path.exists(FX_SNAPSHOT_PATH):
            fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
            fx_df = fx_df.combine_first(new_fx_df)
        else:
            fx_df = new_fx_df
        fx_df.to_parquet(FX_SNAPSHOT_PATH)
        logger.info("💱 當月匯率也已成功更新")
    except Exception as e:
        logger.error("❌ 更新匯率失敗：%s", e)
