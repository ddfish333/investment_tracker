# asset_value.py
import pandas as pd
from datetime import datetime
from modules.fx_fetcher import fetch_monthly_fx
from modules.price_fetcher import fetch_monthly_prices_batch


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
                record['幣別'] = row.get('幣別', 'TWD')
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

    today = pd.Timestamp.today()
    today_month = pd.Period(today, freq='M')
    if today.day == 1:
        today_month = (today - pd.offsets.MonthBegin(1)).to_period('M')

    fx_months = pd.period_range(grouped['月份'].min(), today_month, freq='M')
    fx_df = fetch_monthly_fx(fx_months)
    fx_rate = fx_df.squeeze().to_dict()

    price_df = fetch_monthly_prices_batch(grouped['Yahoo代碼'].dropna().unique(), fx_months)

    debug_records = []
    for idx, row in grouped.iterrows():
        month = row['月份']
        code = row['Yahoo代碼']
        shares = row['累計股數']
        fx = fx_rate.get(month, 30) if row['幣別'] == 'USD' else 1
        price = price_df.at[month, code] if (month in price_df.index and code in price_df.columns) else 0
        market_value = shares * fx * price
        grouped.at[idx, '市值'] = market_value
        debug_records.append({
            '月份': month, '代號': row['股票代號'], '擁有者': row['擁有者'],
            '股數': shares, '價格': price, '匯率': fx, '市值': market_value
        })

    summary_df = grouped.groupby(['月份', '擁有者'])['市值'].sum().unstack(fill_value=0)
    summary_df['Total'] = summary_df.sum(axis=1)

    tw = grouped[grouped['股票代號'].map(market_map) == '台股'].groupby(['月份', '擁有者'])['市值'].sum().unstack(fill_value=0)
    us = grouped[grouped['股票代號'].map(market_map) == '美股'].groupby(['月份', '擁有者'])['市值'].sum().unstack(fill_value=0)

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

    latest_debug_records = [r for r in debug_records if r['月份'] == summary_df.index.max()]

    return summary_df, detail_df, df, monthly_Lo, monthly_Sean, monthly_Joint, price_df, detail_value_df, debug_records, fx_df, latest_debug_records
