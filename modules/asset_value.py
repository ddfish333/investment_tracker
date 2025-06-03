#module/asset_value.py
# -*- coding: utf-8 -*-
import pandas as pd
from modules.fx_fetcher import fetch_monthly_fx
from modules.price_fetcher import fetch_monthly_prices_batch
from modules.time_utils import to_period_index, get_today_period
from modules.transaction_parser import parse_transaction
from modules.cash_parser import parse_cash_balances

def calculate_monthly_asset_value(filepath_transaction, filepath_cash=None):
    # --- 處理股票交易資料 ---
    df = parse_transaction(filepath_main=filepath_transaction, filepath_ownership=filepath_transaction)
    df = to_period_index(df, column='月份')

    today_month = get_today_period()
    all_months = pd.period_range(df['月份'].min(), today_month, freq='M')

    grouped = df.groupby(['月份', '股票代號', '出資者']).agg({
        '股數': 'sum',
        '成本': 'sum'
    }).reset_index()

    all_owners = sorted(df['出資者'].unique())
    full_index = pd.MultiIndex.from_product([
        all_months,
        grouped['股票代號'].unique(),
        all_owners
    ], names=['月份', '股票代號', '出資者'])

    grouped = grouped.set_index(['月份', '股票代號', '出資者']).reindex(full_index, fill_value=0).reset_index()

    grouped['累計股數'] = grouped.groupby(['股票代號', '出資者'])['股數'].cumsum()
    grouped['累計成本'] = grouped.groupby(['股票代號', '出資者'])['成本'].cumsum()

    market_map = df.drop_duplicates('股票代號').set_index('股票代號')['台股/美股'].to_dict()
    currency_map = df.drop_duplicates('股票代號').set_index('股票代號')['幣別'].to_dict()
    ticker_map = (
        df.drop_duplicates('股票代號').set_index('股票代號')['Yahoo代碼'].to_dict()
        if 'Yahoo代碼' in df.columns
        else df.set_index('股票代號').apply(lambda r: r.name, axis=1).to_dict()
    )

    grouped['Yahoo代碼'] = grouped['股票代號'].map(ticker_map)
    grouped['幣別'] = grouped['股票代號'].map(currency_map).fillna('TWD')

    fx_df = fetch_monthly_fx(all_months)
    fx_rate = fx_df.squeeze().to_dict()

    needed_codes = grouped['Yahoo代碼'].dropna().unique()
    stock_price_df = fetch_monthly_prices_batch(needed_codes, all_months)

    def calculate_market_value(row):
        month = row['月份']
        code = row['Yahoo代碼']
        shares = row['累計股數']
        fx = fx_rate.get(month, 30) if row['幣別'] == 'USD' else 1
        price = stock_price_df.at[month, code] if (month in stock_price_df.index and code in stock_price_df.columns) else 0
        return shares * fx * price

    grouped['市值'] = grouped.apply(calculate_market_value, axis=1)

    summary_stock_df = grouped.groupby(['月份', '出資者'])['市值'].sum().unstack(fill_value=0)

    tw = grouped[grouped['股票代號'].map(market_map) == '台股'].groupby(['月份', '出資者'])['市值'].sum().unstack(fill_value=0)
    us = grouped[grouped['股票代號'].map(market_map) == '美股'].groupby(['月份', '出資者'])['市值'].sum().unstack(fill_value=0)

    for owner in all_owners:
        summary_stock_df[f'{owner}_TW_STOCK'] = tw.get(owner, 0)
        summary_stock_df[f'{owner}_US_STOCK'] = us.get(owner, 0)

    grouped['股票ID'] = grouped['出資者'] + '_' + grouped['股票代號']
    stock_value_df = grouped.pivot_table(
        index='月份',
        columns='股票ID',
        values='市值',
        aggfunc='sum'
    ).fillna(0)
    stock_value_df.columns.name = None

    # --- 現金資料處理 ---
    if filepath_cash:
        summary_cash_df = parse_cash_balances(filepath=filepath_cash)
    else:
        summary_cash_df = pd.DataFrame(index=all_months)

    # --- 合併股票與現金為總資產 ---
    summary_df = summary_stock_df.add(summary_cash_df, fill_value=0)

    # --- 重算每位出資者的總資產欄位（股票 + 現金） ---
    for owner in all_owners:
        summary_df[owner] = (
            summary_df.get(f'{owner}_TW_STOCK', 0)
            + summary_df.get(f'{owner}_US_STOCK', 0)
            + summary_df.get(f'{owner}_TWD_CASH', 0)
            + summary_df.get(f'{owner}_USD_CASH', 0)
        )

    # --- 重算 Total 欄位為 Sean + Lo ---
    summary_df['Total'] = summary_df[all_owners].sum(axis=1)

    return summary_df, summary_stock_df, summary_cash_df, df, stock_price_df, stock_value_df, fx_df, all_months
