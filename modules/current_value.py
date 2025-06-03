# modules/current_value.py
import pandas as pd
import yfinance as yf
from modules.transaction_parser import parse_transaction
from modules.cash_parser import parse_cash_detail

def calculate_current_asset_value(filepath_transaction, fx_rate=32.0):
    df = parse_transaction(filepath_main=filepath_transaction, filepath_ownership=filepath_transaction)

    ticker_map = (
        df.drop_duplicates('股票代號').set_index('股票代號')['Yahoo代碼'].to_dict()
        if 'Yahoo代碼' in df.columns
        else df.set_index('股票代號').apply(lambda r: r.name, axis=1).to_dict()
    )
    df['Yahoo代碼'] = df['股票代號'].map(ticker_map)

    df = df.groupby(['股票代號', '出資者', '台股/美股', '幣別', 'Yahoo代碼']).agg({'股數': 'sum'}).reset_index()
    df = df[df['股數'] > 0]

    tickers = df['Yahoo代碼'].dropna().unique().tolist()
    if tickers:
        raw = yf.download(tickers=tickers, period="1d", interval="1d", progress=False)
        if isinstance(raw.columns, pd.MultiIndex) and 'Close' in raw.columns.levels[0]:
            prices = raw['Close'].iloc[-1]
        else:
            prices = pd.Series(index=tickers, data=[0]*len(tickers))
    else:
        prices = pd.Series(dtype=float)

    df['股價'] = df['Yahoo代碼'].map(prices.to_dict()).fillna(0)
    df['原幣市值'] = df['股數'] * df['股價']
    df['匯率'] = df['幣別'].apply(lambda c: fx_rate if c == 'USD' else 1.0)
    df['TWD市值'] = df['原幣市值'] * df['匯率']
    df['類別'] = df['台股/美股']

    return df

def calculate_current_cash_value(filepath_cash, fx_rate=32.0):
    cash_detail = parse_cash_detail(filepath_cash)
    latest_month = cash_detail.index.get_level_values("月份").max()
    df = cash_detail.loc[latest_month].reset_index()

    df['幣別'] = df['帳戶全名'].apply(lambda x: 'USD' if 'USD' in x.upper() else 'TWD')
    df['匯率'] = df['幣別'].apply(lambda c: fx_rate if c == 'USD' else 1.0)
    df['類別'] = df['幣別'].apply(lambda c: '美金資產 (USD)' if c == 'USD' else '台幣資產 (TWD)')
    df['股票代號'] = None
    df['股數'] = None
    df['股價'] = None
    df['原幣市值'] = df.apply(lambda r: r['TWD金額'] / r['匯率'] if r['匯率'] else 0, axis=1)
    df['TWD市值'] = df['TWD金額']
    df = df.rename(columns={'擁有者': '出資者'})

    return df

def combine_current_asset_and_cash(stock_df, cash_df):
    cols = ['出資者', '類別', '匯率', '股票代號', '股數', '股價', '原幣市值', 'TWD市值']
    stock_df = stock_df[cols].copy()
    cash_df = cash_df[cols].copy()
    combined_df = pd.concat([stock_df, cash_df], ignore_index=True).fillna(0)
    combined_df = combined_df.sort_values(by=['出資者', '類別', 'TWD市值'], ascending=[True, True, False])
    return combined_df