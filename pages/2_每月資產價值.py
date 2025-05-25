# pages/2_每月資產價值.py
```python
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value

# --- Streamlit Page: 每月資產價值 (以台幣計價) ---
st.set_page_config(layout="wide")

# 設定中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 計算資產
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# 顯示總資產
total_lo = summary_df['Lo'].iloc[-1]
total_sean = summary_df['Sean'].iloc[-1]
st.title(f"💰 每月資產價值（以台幣計價） — Lo: {total_lo:,.0f}元, Sean: {total_sean:,.0f}元")
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df[['Lo', 'Sean']])

# CSV 下載
st.download_button(
    label="下載總資產資料 (CSV)",
    data=summary_df.to_csv(encoding='utf-8-sig'),
    file_name='summary_asset.csv',
    mime='text/csv'
)

# 個股篩選與排序：先非零再零，顏色正常 vs 灰階
codes = list(detail_df.columns.levels[1])
last_hold = {code: (detail_df.xs(code, level='Code', axis=1)['Lo'] + detail_df.xs(code, level='Code', axis=1)['Sean'] + detail_df.xs(code, level='Code', axis=1)['Sean/Lo']).iloc[-1] for code in codes}
sorted_codes = sorted(codes, key=lambda c: (last_hold[c] == 0, -last_hold[c]))

st.subheader("個股資產明細")
cols = st.columns(3)
for idx, code in enumerate(sorted_codes):
    col = cols[idx % 3]
    with col:
        last = last_hold[code]
        title = f"{code} {'(已售罄)' if last == 0 else f'({int(last)}元)'}"
        st.markdown(f"### {title}")
        df_code = detail_df.xs(code, level='Code', axis=1).rename(columns={'Lo':'Lo','Sean':'Sean','Sean/Lo':'Sean/Lo'})
        df_code['Total'] = df_code.sum(axis=1)
        # 顏色灰階 or 正常
        colors = ['#D3D3D3' if last==0 else None]*3 + [None]
        st.line_chart(df_code)
```
