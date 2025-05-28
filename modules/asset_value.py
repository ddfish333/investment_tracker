import pandas as pd
import numpy as np
import yfinance as yf
import re


def calculate_monthly_asset_value(filepath):
    df = pd.read_excel(filepath)
    df['交易日期'] = pd.to_datetime(df['交易日期'])
    df['月份'] = df['交易日期'].dt.to_period('M')
    df['股票代號'] = df['股票代號'].astype(str)

    records = []
    for _, row in df.iterrows():
        for owner, ratio in zip(['Sean', 'Lo'], [row['Sean 出資比例'], row['Lo 出資比例']]):
            if ratio > 0:
                record = row.copy()
                record['擁有者'] = owner
                shares = row['買賣股數'] * ratio
                record['股數'] = shares
                record['成本'] = shares * row['價格'] + row['手續費'] + row['稅金']
                record['幣別'] = row['幣別'] if '幣別' in row else 'TWD'
                records.append(record)

    split_df = pd.DataFrame.from_records(records)

    grouped = split_df.groupby(['月份', '股票代號', '擁有者']).agg({
        '股數': 'sum',
        '成本': 'sum'
    }).reset_index()

    full_index = pd.MultiIndex.from_product([
        grouped['月份'].unique(),
        grouped['股票代號'].unique(),
        ['Sean', 'Lo']
    ], names=['月份', '股票代號', '擁有者'])

    grouped = grouped.set_index(['月份', '股票代號', '擁有者']).reindex(full_index, fill_value=0).reset_index()

    grouped['累計股數'] = grouped.groupby(['股票代號', '擁有者'])['股數'].cumsum()
    grouped['累計成本'] = grouped.groupby(['股票代號', '擁有者'])['成本'].cumsum()

    market_map = df.drop_duplicates('股票代號').set_index('股票代號')['台股/美股'].to_dict()
    currency_map = df.drop_duplicates('股票代號').set_index('股票代號')['幣別'].to_dict()
    ticker_map = df.drop_duplicates('股票代號').set_index('股票代號')['Yahoo代碼'].to_dict() if 'Yahoo代碼' in df.columns else df.set_index('股票代號').apply(lambda r: r.name, axis=1).to_dict()

    grouped['Yahoo代碼'] = grouped['股票代號'].map(ticker_map)
    grouped['幣別'] = grouped['股票代號'].map(currency_map).fillna('TWD')

    price_data = {}
    for code in grouped['Yahoo代碼'].dropna().unique():
        try:
            px = yf.download(code, start=df['交易日期'].min(), end=pd.Timestamp.today(), interval='1mo', progress=False)
            close = px['Close']
            close.index = close.index.to_period('M')
            close = close[~close.index.duplicated(keep='last')]
            close.name = code
            price_data[code] = close
        except:
            price_data[code] = pd.Series(dtype=float, name=code)

    if price_data:
        price_df = pd.concat(price_data.values(), axis=1)
        price_df.index.name = '月份'
    else:
        price_df = pd.DataFrame()

    fx_rate = pd.Series([30.0] * len(price_df.index), index=price_df.index)

    def get_price(row):
        ticker = row['Yahoo代碼']
        month = row['月份']
        try:
            px = price_df.at[month, ticker]
            return row['累計股數'] * px * (fx_rate[month] if row['幣別'] == 'USD' else 1)
        except:
            return 0.0

    grouped['市值'] = grouped.apply(get_price, axis=1)

    summary_df = grouped.groupby(['月份', '擁有者'])['市值'].sum().unstack(fill_value=0)
    summary_df['Total'] = summary_df.sum(axis=1)

    def market_split(df, market_type):
        return df[df['股票代號'].map(market_map) == market_type].groupby(['月份', '擁有者'])['市值'].sum().unstack(fill_value=0)

    tw = market_split(grouped, '台股')
    us = market_split(grouped, '美股')
    for owner in ['Sean', 'Lo']:
        summary_df[f'{owner}_TW'] = tw.get(owner, 0)
        summary_df[f'{owner}_US'] = us.get(owner, 0)

    detail_df = grouped.pivot_table(index='月份', columns=['股票代號', '擁有者'], values='累計股數', aggfunc='sum').fillna(0)
    detail_df.columns.set_names(['Code', 'Owner'], inplace=True)

    detail_value_df = grouped.pivot_table(index='月份', columns=['股票代號', '擁有者'], values='市值', aggfunc='sum').fillna(0)
    detail_value_df.columns.set_names(['Code', 'Owner'], inplace=True)

    monthly_Sean = detail_df.xs('Sean', level='Owner', axis=1)
    monthly_Lo = detail_df.xs('Lo', level='Owner', axis=1)
    monthly_Joint = pd.DataFrame(index=monthly_Sean.index, columns=monthly_Sean.columns).fillna(0)

    return summary_df, detail_df, df, monthly_Lo, monthly_Sean, monthly_Joint, price_df, detail_value_df
