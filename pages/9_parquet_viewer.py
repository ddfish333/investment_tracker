import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Parquet 檔案瀏覽器", layout="wide")
st.title("📦 Parquet 檔案瀏覽器")

# 指定資料夾路徑（可根據實際情況調整）
parquet_folder = "data"

# 取得所有 parquet 檔案清單
all_files = [f for f in os.listdir(parquet_folder) if f.endswith(".parquet")]

if not all_files:
    st.warning("找不到任何 .parquet 檔案")
else:
    selected_file = st.selectbox("請選擇要讀取的 Parquet 檔案：", all_files)
    parquet_path = os.path.join(parquet_folder, selected_file)

    try:
        df = pd.read_parquet(parquet_path)

        # 如果 index 是 datetime 或 period，就排序降冪顯示最新在前
        if isinstance(df.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            df = df.sort_index(ascending=False)

        st.success(f"✅ 讀取成功：{selected_file}，共 {df.shape[0]} 筆 x {df.shape[1]} 欄")

        if st.checkbox("📄 顯示原始資料表"):
            st.dataframe(df, use_container_width=True)

        if st.checkbox("📈 顯示欄位描述統計"):
            st.write(df.describe())

        if st.checkbox("🔍 顯示前幾筆資料"):
            st.write(df.head(10))

        if st.checkbox("🧱 顯示 Index 與欄位資訊"):
            st.write("Index 型別：", type(df.index))
            st.write("欄位：", df.columns.tolist())
    except Exception as e:
        st.error(f"❌ 讀取 parquet 失敗：{e}")
