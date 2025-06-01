# time_utils.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def ensure_period_index(df: pd.DataFrame, freq="M") -> pd.DataFrame:
    """
    保證 df.index 為 PeriodIndex，若非則轉換為指定 freq 的 PeriodIndex。
    用於時間序列一致性處理。
    """
    if not isinstance(df.index, pd.PeriodIndex):
        logger.info("🔄 index 非 PeriodIndex，自動轉換中...")
        df.index = pd.to_datetime(df.index).to_period(freq)
    return df

def to_period_index(obj, freq="M"):
    """
    將 Series、Index、list 等時間資料轉換為 PeriodIndex。
    如果傳入的是 Series，會自動略過其 index，避免 RangeIndex 錯誤。
    """
    if isinstance(obj, pd.PeriodIndex):
        return obj
    elif isinstance(obj, pd.Series):
        return pd.to_datetime(obj.values).to_period(freq)  # ✅ 避免 Series index 被誤用
    elif isinstance(obj, (pd.DatetimeIndex, list, pd.Index)):
        return pd.to_datetime(obj).to_period(freq)
    else:
        raise TypeError(f"❌ 無法轉換為 PeriodIndex: {type(obj)}")

def to_timestamp(obj):
    """
    將 Period 或 PeriodIndex 轉回 Timestamp 或 DatetimeIndex。
    用於抓取資料時與外部 API 相容。
    """
    if isinstance(obj, pd.PeriodIndex):
        return obj.to_timestamp()
    elif isinstance(obj, pd.Period):
        return obj.to_timestamp()
    else:
        raise TypeError(f"❌ 非 Period 資料，無法轉換為 Timestamp: {type(obj)}")

def period_label(p: pd.Period) -> str:
    """
    將 Period（例如 Period('2023-06')）轉成字串 "2023-06"
    可用於顯示或存檔命名。
    """
    return str(p)
