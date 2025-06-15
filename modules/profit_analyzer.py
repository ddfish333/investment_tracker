import pandas as pd

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
