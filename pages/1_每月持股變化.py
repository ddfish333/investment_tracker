# pages/1_每月持股變化.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from modules.asset_value import calculate_monthly_asset_value

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if fm.findSystemFonts(fontpaths=[font_path]):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False

# --- Streamlit Setup ---
st.set_page_config(page_title="每月持股變化", layout="wide")
st.title("📊 每月持股變化分析")

# 讀取資產資料
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

if not isinstance(detail_df.columns, pd.MultiIndex):
    st.error("❌ 資料格式錯誤，detail_df 欄位必須是 MultiIndex")
else:
    for owner in ['Sean', 'Lo']:
        df = detail_df.xs(owner, axis=1, level='Owner', drop_level=False).copy()
        if df.empty:
            st.warning(f"⚠️ 找不到 {owner} 的資料")
            continue

        latest = df.iloc[-1]
        sorted_codes = latest[latest > 0].sort_values(ascending=False).index.tolist()
        zero_codes = latest[latest == 0].index.tolist()
        df = df[sorted_codes + zero_codes]

        st.markdown(f"#### {owner} 每月持股變化")

        fig, ax = plt.subplots(figsize=(12, 5))
        bottom = [0] * len(df)

        for code in df.columns:
            try:
                values = df[code].values
                if len(values) != len(df.index):
                    st.warning(f"⚠️ {code} 資料長度不符，跳過該股票")
                    continue
                ax.bar(df.index, values, bottom=bottom, label=str(code))
                bottom = [i + j for i, j in zip(bottom, values)]
            except Exception as e:
                st.error(f"❌ 畫圖失敗：{code}，錯誤訊息：{e}")

        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_ylabel("股數")
        ax.set_xlabel("月份")
        ax.set_title(f"{owner} 每月股票組合")
        st.pyplot(fig)
        