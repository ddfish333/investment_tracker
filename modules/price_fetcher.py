```python
# modules/price_fetcher.py
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr

# 使用 yfinance 取代 pandas_datareader
yf.pdr_override()


def fetch_month_end_prices(codes, months):
    """
    抓取歷史每月月底收盤價：
      - codes: 可識別為台股(不以US結尾)或美股(以'US'結尾)
      - months: DatetimeIndex，各月的最後一天
    回傳 DataFrame，index=months, columns=codes
    """
    # 計算時間範圍
    start = months.min().to_period('M').to_timestamp()
    end = months.max().to_period('M').to_timestamp() + pd.offsets.MonthEnd(0)
    # 儲存結果
    df_list = []
    for code in codes:
        if str(code).endswith('US'):
            ticker = code.rstrip('US')  # e.g. 'AAPLUS' -> 'AAPL'
        else:
            ticker = f"{code}.TW"
        try:
            hist = pdr.get_data_yahoo(ticker, start=start, end=end + pd.Timedelta(days=1))
            # 以月為頻率取最後一筆Close
            monthly = hist['Close'].resample('M').last()
        except Exception:
            monthly = pd.Series(index=pd.date_range(start=start, end=end, freq='M'), data=pd.NA)
        monthly.name = code
        df_list.append(monthly)
    price_df = pd.concat(df_list, axis=1)
    # 重新索引到指定months
    price_df = price_df.reindex(months)
    return price_df.astype(float)


def fetch_month_end_fx(months, base='USD', quote='TWD'):
    """
    抓取美元兌新台幣月末匯率(FRED資料)：
      - months: DatetimeIndex，各月最後一天
    回傳 Series，index=months
    """
    # FRED 上 USD/TWD 匯率代碼為 DEXTAUS
    fred_code = 'DEXTAUS'
    start = months.min().to_period('M').to_timestamp()
    end = months.max().to_period('M').to_timestamp()
    fx = pdr.DataReader(fred_code, 'fred', start, end)
    monthly_fx = fx[fred_code].resample('M').last()
    monthly_fx = monthly_fx.reindex(months).ffill()
    monthly_fx.name = 'FX'
    return monthly_fx.astype(float)
```
