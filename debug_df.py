# debug_df.py
from modules.asset_value import calculate_monthly_asset_value
import pandas as pd

summary_df, detail_df, *_ = calculate_monthly_asset_value("data/transactions.xlsx")

print("✅ summary_df 預覽：")
print(summary_df.head())

print("\n✅ detail_df 預覽：")
print(detail_df.head())
