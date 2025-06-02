import streamlit as st
import pandas as pd
from modules.parse_transaction import parse_transaction

st.set_page_config(page_title="Debug parse_transaction", layout="wide")
st.title("🧪 parse_transaction() Debug 工具")

# 檔案路徑
filepath_main = "data/transactions.xlsx"
filepath_ownership = "data/transactions.xlsx"  # 你應該是把 ownership sheet 放在同一份

# 呼叫函式
df = parse_transaction(filepath_main, filepath_ownership)

# 顯示結果
st.subheader("📄 預覽 df（含分拆後的每位出資者）")
st.dataframe(df)

st.subheader("🧠 欄位型別")
st.write(df.dtypes)

st.subheader("🧼 缺值統計")
st.write(df.isna().sum())

st.subheader("📊 數值欄位統計")
st.write(df.describe())
