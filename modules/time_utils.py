#time_utils.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def to_period_index(obj, freq="M", column=None):
    """
    將 Series、Index、list 或 DataFrame 的特定欄位轉換為 PeriodIndex。
    - 若傳入的是 Series、Index、list，則轉換為 PeriodIndex 回傳
    - 若傳入的是 DataFrame 且指定欄位，則將該欄轉為 Period
    """
    if isinstance(obj, (pd.PeriodIndex, pd.arrays.PeriodArray)):
        return obj
    elif isinstance(obj, pd.Series):
        return pd.to_datetime(obj.values).to_period(freq)
    elif isinstance(obj, pd.DataFrame):
        if column and column in obj.columns:
            # 🔒 防止你對已經是 Period 的欄位重複轉換
            if not pd.api.types.is_period_dtype(obj[column]):
                if pd.api.types.is_datetime64_any_dtype(obj[column]):
                    obj[column] = obj[column].dt.to_period(freq)
                else:
                    obj[column] = pd.to_datetime(obj[column]).dt.to_period(freq)
            return obj
        else:
            raise ValueError(f"❌ DataFrame 必須指定 column 欄位才可轉換為 Period: {column}")
    elif isinstance(obj, (pd.DatetimeIndex, list, pd.Index)):
        return pd.to_datetime(obj).to_period(freq)
    else:
        raise TypeError(f"❌ 無法轉換為 PeriodIndex: {type(obj)}")


def ensure_period_index(df: pd.DataFrame, freq="M") -> pd.DataFrame:
    """
    保證 df.index 為 PeriodIndex，若非則轉換為指定 freq 的 PeriodIndex。
    用於時間序列一致性處理。
    """
    if not isinstance(df.index, pd.PeriodIndex):
        logger.info("🔄 index 非 PeriodIndex，自動轉換中...")
        df.index = pd.to_datetime(df.index).to_period(freq)
    return df

def get_today_period():
    """
    傳回今天所屬月份的 Period(M) 格式。
    若今天是 1 號，則回傳上個月。
    """
    today = pd.Timestamp.today()
    if today.day == 1:
        return (today - pd.offsets.MonthBegin(1)).to_period("M")
    return today.to_period("M")
