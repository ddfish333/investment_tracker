# fx_fetcher.py
import pandas as pd
import os
import logging
from config import FX_SNAPSHOT_PATH
from modules.time_utils import to_period_index, ensure_period_index

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_monthly_fx(months):
    # 確保輸入為 PeriodIndex（freq="M"）
    months = to_period_index(months)

    # 若快照檔存在，先讀入，否則新建空表
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
        fx_df = ensure_period_index(fx_df)

        # ✅ 若缺少 USD 欄位，自動補上
        if "USD" not in fx_df.columns:
            fx_df["USD"] = pd.NA
    else:
        fx_df = pd.DataFrame(columns=["USD"], index=pd.period_range(min(months), max(months), freq="M"))

    # 整理出缺少的月份
    fx_df = fx_df.copy()
    needed_months = pd.period_range(min(months), max(months), freq="M")

    missing_months = [m for m in needed_months if m not in fx_df.index or pd.isna(fx_df.at[m, "USD"])]

    # 補上缺的匯率資料（暫用固定值 30.0）
    for month in missing_months:
        fx_df.loc[month, "USD"] = 30.0
        logger.info(f"✅ 匯率資料補齊：{month} ➔ 30.0")

    # 對齊格式與順序
    fx_df = fx_df.reindex(index=needed_months).sort_index()

    # 儲存快照
    fx_df.to_parquet(FX_SNAPSHOT_PATH)
    logger.info(f"💾 匯率快照已儲存至：{FX_SNAPSHOT_PATH}")

    return fx_df