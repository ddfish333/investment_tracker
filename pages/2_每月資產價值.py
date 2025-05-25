# pages/2_每月資產價值.py
```python
import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from modules.asset_value import calculate_monthly_asset_value

# 設定 Streamlit 頁面
st.set_page_config(page_title="每月資產價值", layout="wide")

# 中文設定
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 計算並取得總覽與明細
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# 顯示標題與最新資產
lo_curr = summary_df['Lo'].iloc[-1]
sean_curr = summary_df['Sean'].iloc[-1]
st.title(f"💰 每月資產價值（台幣） Lo: {lo_curr:,.0f}元 | Sean: {sean_curr:,.0f}元")

# 總資產走勢
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df[['Lo','Sean','Total']])

# 個股資產明細（卡片式）
st.subheader("個股資產明細")
codes = detail_df.columns.get_level_values('Code').unique().tolist()
# 取最後一期的資產值
last_vals = {c: detail_df.xs(c, level='Code', axis=1).sum(axis=1).iloc[-1] for c in codes}
# 先有持股再已售罄，並依資產大小排序
sorted_codes = sorted(codes, key=lambda c: (last_vals[c]==0, -last_vals[c]))

cols = st.columns(3)
for idx, code in enumerate(sorted_codes):
    with cols[idx % 3]:
        val = last_vals[code]
        status = "(已售罄)" if val==0 else f"({val:,.0f}元)"
        st.markdown(f"#### {code} {status}")
        df = detail_df.xs(code, level='Code', axis=1).copy()
        df['Total'] = df.sum(axis=1)
        # 灰階顏色
        if val == 0:
            st.line_chart(df, use_container_width=True, color='#888888')
        else:
            st.line_chart(df, use_container_width=True)
```
