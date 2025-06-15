import pandas as pd
from collections import deque

def expand_joint_transactions_by_ownership(transactions_df: pd.DataFrame, ownership_df: pd.DataFrame) -> pd.DataFrame:
    """
    將交易資料中出資者為 Joint 的紀錄，根據 ownership_df 的出資比例展開，
    分配給實際擁有者（Sean、Lo 等）。
    """
    joint_df = transactions_df[transactions_df['出資者'] == 'Joint']
    non_joint_df = transactions_df[transactions_df['出資者'] != 'Joint']

    expanded_rows = []

    for _, txn in joint_df.iterrows():
        txn_id = txn['交易編號']
        matching_ownerships = ownership_df[ownership_df['交易編號'] == txn_id]

        if matching_ownerships.empty:
            raise ValueError(f"❌ 找不到交易編號 {txn_id} 的出資比例設定！")

        for _, row in matching_ownerships.iterrows():
            owner = row['擁有者']
            ratio = row['出資比例']

            split_txn = txn.copy()
            split_txn['出資者'] = owner

            # 需要按比例分攤的欄位
            for col in ['股數', '手續費', '證交稅', '金額', '收入', '成本']:
                if col in split_txn:
                    split_txn[col] = split_txn[col] * ratio

            expanded_rows.append(split_txn)

    expanded_df = pd.DataFrame(expanded_rows)
    final_df = pd.concat([non_joint_df, expanded_df], ignore_index=True)
    return final_df

def calculate_realized_profit(transactions_df: pd.DataFrame, fx_df: pd.DataFrame) -> pd.DataFrame:
    """
    使用 FIFO 計算已實現損益。
    資料需包含：出資者、股票代號、交易編號、日期、類別、股數、單價、幣別、收入、手續費、證交稅。
    """
    transactions_df = transactions_df.sort_values(by=['出資者', '股票代號', '日期'])
    results = []

    for (owner, stock), group in transactions_df.groupby(['出資者', '股票代號']):
        buy_queue = deque()

        for _, row in group.iterrows():
            if row['類別'] == '買入':
                buy_queue.append({
                    '股數': row['股數'],
                    '單價': row['單價'],
                    '幣別': row['幣別'],
                    '日期': row['日期'],
                    '手續費': row.get('手續費', 0),
                    '證交稅': row.get('證交稅', 0)
                })

            elif row['類別'] == '賣出':
                remain = row['股數']
                proceeds = row['收入']
                sell_date = row['日期']
                fx_rate = fx_df.loc[(sell_date.to_period('M'), row['幣別'])] if (sell_date.to_period('M'), row['幣別']) in fx_df.index else 30.0
                total_cost = 0
                realized_rows = []

                while remain > 0 and buy_queue:
                    buy_lot = buy_queue[0]
                    use_shares = min(remain, buy_lot['股數'])

                    cost = use_shares * buy_lot['單價']
                    total_cost += cost

                    realized_rows.append({
                        '出資者': owner,
                        '股票代號': stock,
                        '賣出日期': sell_date,
                        '股數': use_shares,
                        '收入_TWD': proceeds * fx_rate * (use_shares / row['股數']),
                        '成本_TWD': cost * fx_rate,
                        '報酬_TWD': (proceeds * fx_rate * (use_shares / row['股數'])) - (cost * fx_rate)
                    })

                    remain -= use_shares
                    buy_lot['股數'] -= use_shares
                    if buy_lot['股數'] == 0:
                        buy_queue.popleft()

                results.extend(realized_rows)

    return pd.DataFrame(results)
