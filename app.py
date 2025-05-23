import streamlit as st
import time

# 設定畫面排版
st.set_page_config(layout="wide")
st.title("📊 投資追蹤系統首頁")

# 說明文字
st.markdown("""
歡迎使用你的投資追蹤分析平台 👋  
請透過左側選單選擇要進行的分析功能。

---

### 可用功能：
- 每月持股變化總覽（疊加直方圖）
- 每月資產價值（台幣換算）
- 年度損益分析（開發中）
""")

# 自動跳轉（延遲 1 秒避免 crash）
time.sleep(1)
st.switch_page("pages/holding_analysis.py")
