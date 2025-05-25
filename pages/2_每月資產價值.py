```python
# pages/2_每月資產價值.py
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

# 顯示總資產走勢與篩選、匯出
total_lo = summary_df['Lo'].iloc[-1]
total_sean = summary_df['Sean'].iloc[-1]
st.title(f"💰 每月資產價值（以台幣計價），目前 Lo: {total_lo:,.0f}元, Sean: {total_sean:,.0f}元")
st.subheader("總資產走勢：Lo vs Sean")
st.line_chart(summary_df)

# 下載總資產 CSV
st.download_button(
    label="下載總資產資料 (CSV)",
    data=summary_df.to_csv(encoding='utf-8-sig'),
    file_name='summary_asset.csv',
    mime='text/csv'
)

# 各股票選擇控制
all_codes = list(detail_df.columns.levels[1])
selected = st.multiselect("選擇要顯示的股票代號", all_codes, default=all_codes)

st.subheader("各股票資產走勢明細")
for code in selected:
    st.markdown(f"### {code} 資產走勢")
    df_code = detail_df.xs(code, level='Code', axis=1)
    df_code.columns = ['Lo', 'Sean']
    # 加總 Total
    df_code['Total'] = df_code['Lo'] + df_code['Sean']
    st.line_chart(df_code)

# 下載明細資料 CSV
if selected:
    export_df = detail_df.loc[:, (slice(None), selected)]
    # 重構為平面表
    export_flat = export_df.stack(level='Owner', axis=1)
    csv_data = export_flat.to_csv(encoding='utf-8-sig')
    st.download_button(
        label="下載選取股票明細 (CSV)",
        data=csv_data,
        file_name='detail_asset.csv',
        mime='text/csv'
    )
```
