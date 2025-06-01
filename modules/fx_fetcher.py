# fx_fetcher.py
import pandas as pd
import os
import sys
import logging
from datetime import datetime

# 確保可以引用 config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import FX_SNAPSHOT_PATH

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_monthly_fx(months):
    months = pd.to_datetime(months.to_timestamp()).to_period("M")

    # 若快照檔存在，先讀入
    if os.path.exists(FX_SNAPSHOT_PATH):
        fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
        fx_df.index = pd.to_datetime(fx_df.index).to_period("M")
    else:
        fx_df = pd.DataFrame(columns=["USD"], index=pd.period_range(min(months), max(months), freq="M"))

    fx_df = fx_df.copy()
    needed_months = pd.period_range(min(months), max(months), freq="M")

    missing_months = []
    for m in needed_months:
        if m not in fx_df.index or pd.isna(fx_df.at[m, "USD"]):
            missing_months.append(m)

    for month in missing_months:
        # 實際上建議這邊改為查詢央行或提供匯率API，如此處簡化為固定匯率（示意）
        fx_df.loc[month, "USD"] = 30.0
        logger.info(f"✅ 匯率資料補齊：{month} ➔ 30.0")

    fx_df = fx_df.reindex(index=needed_months).sort_index()
    fx_df.to_parquet(FX_SNAPSHOT_PATH)
    logger.info(f"💾 匯率快照已儲存至：{FX_SNAPSHOT_PATH}")

    return fx_df
