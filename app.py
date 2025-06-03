import streamlit as st
import time
import random

st.set_page_config(layout="wide")
st.title("資產怪獸 ASSET MONSTER")

# --- 動態小動畫模擬 ---
with st.empty():
    for i in range(20):
        eye = random.choice(["👀", "🧿", "👁️"])
        mouth = random.choice(["🦷", "👄", "🫦"])
        face = f"**Asset Monster is waking up... {eye}{mouth}{eye}**"
        st.markdown(face)
        time.sleep(0.1)

st.markdown("""
### 🧠 Asset Monster: Tame Your Portfolio

Meet Asset Monster — your intelligent financial tracker.  
It devours your stocks, cash, and foreign currency, then spits out clean, actionable insights.

- 📈 Real-time asset monitoring  
- 💱 Multi-currency automatic valuation  
- 📊 Intuitive visual breakdowns for clarity and control  
- 🔍 Zoom in on details or view the big picture — anytime

Whether you’re managing your personal empire or just starting to track your wealth, Asset Monster gives you structure without the spreadsheet chaos.

> It's not just about tracking. It's about mastering.

Scroll down and let the Beast crunch the numbers. You feed it data — it feeds you back control.
""")
