# pages/2_每月資產價值.py
```python
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from modules.asset_value import calculate_monthly_asset_value

# --- Streamlit 設定 ---
st.set_page_config(page_title="每月資產價值", layout="wide")

# 中文字體
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 計算資產
summary_df, detail_df = calculate_monthly_asset_value("data/transactions.xlsx")

# 標題與當前資產
lo_curr = summary_df['Lo'].iloc[-1]
sean_curr = summary_df['Sean'].iloc[-1]
st.title(f"💰 每月資產價值（台幣） Lo: {lo_curr:,.0f}元 | Sean: {sean_curr:,.0f}元")

# 總資產走勢
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df[['Lo','Sean','Total']])

# CSV 下載
st.download_button(
    "下載總資產 CSV", summary_df.to_csv(encoding='utf-8-sig'), "summary_asset.csv", "text/csv"
)

# 個股明細卡片
st.subheader("個股資產明細")

# 排序：先有持股再無持股
codes = list(detail_df.columns.get_level_values('Code').unique())
last_sum = {code: detail_df.xs(code, level='Code', axis=1).sum(axis=1).iloc[-1] for code in codes}
sorted_codes = sorted(codes, key=lambda c: (last_sum[c]==0, -last_sum[c]))

# 顯示卡片
cols = st.columns(3)
for idx, code in enumerate(sorted_codes):
    col = cols[idx % 3]
    with col:
        val = last_sum[code]
        title = f"{code} " + ("(已售罄)" if val==0 else f"({val:,.0f}元)")
        st.markdown(f"#### {title}")
        df_code = detail_df.xs(code, level='Code', axis=1)
        df_code['Total'] = df_code.sum(axis=1)
        color = '#D3D3D3' if val==0 else None
        st.line_chart(df_code, use_container_width=True)
```
