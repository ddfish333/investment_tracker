# config.py
# 儲存全域參數，方便集中管理與日後擴充

# 股票價格快照路徑
PRICE_SNAPSHOT_PATH = "data/monthly_price_history.parquet"

# 匯率快照路徑
FX_SNAPSHOT_PATH = "data/monthly_fx_history.parquet"

# 交易紀錄 Excel 檔案路徑
TRANSACTION_FILE = "data/transactions.xlsx"

# 可加上更多參數設定
# 例如：LOG_LEVEL = "INFO", DEFAULT_FX_RATE = 30.0
