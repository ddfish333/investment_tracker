# modules/holding_parser.py
import pandas as pd


def parse_monthly_holdings(filepath):
    df = pd.read_excel(filepath)
    df["交易日期"] = pd.to_datetime(df["交易日期"])
    df["月份"] = df["交易日期"].dt.to_period("M")
    df["來源"] = df["備註"].fillna("其他")
    df["幣別"] = df["幣別"].fillna("TWD")

    all_codes = sorted(df["股票代號"].dropna().unique(), key=lambda x: str(x))
    all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

    def initialize():
        return pd.DataFrame(index=all_months, columns=all_codes).fillna(0), {code: 0 for code in all_codes}

    monthly_Lo, current_Lo = initialize()
    monthly_Sean, current_Sean = initialize()
    monthly_SeanLo, current_SeanLo = initialize()

    for month in all_months:
        rows = df[df["月份"] == month]
        for _, row in rows.iterrows():
            code = row["股票代號"]
            qty = int(row["買賣股數"])
            source = row["來源"]
            if source == "Lo":
                current_Lo[code] += qty
            elif source == "Sean":
                current_Sean[code] += qty
            elif source == "Sean/Lo":
                current_SeanLo[code] += qty

        for code in all_codes:
    fig, ax = plt.subplots(figsize=(6, 3))
    lo_series = monthly_Lo[code]
    sean_series = monthly_Sean[code]
    seanlo_series = monthly_SeanLo[code]

    # 計算該股票每個月份的總持股數量
    total_series = lo_series + sean_series + seanlo_series
    is_zero = total_series.sum() == 0

    # 根據是否為零設定顏色（深淺灰 vs 藍系）
    if is_zero:
        lo_color = "#d3d3d3"     # 淺灰
        sean_color = "#a9a9a9"   # 中灰
        seanlo_color = "#696969" # 深灰
    else:
        lo_color = "#87CEEB"
        sean_color = "#4682B4"
        seanlo_color = "#0F52BA"

    ax.bar(lo_series.index, lo_series, color=lo_color, label="Lo", width=20)
    ax.bar(sean_series.index, sean_series, bottom=lo_series, color=sean_color, label="Sean", width=20)
    ax.bar(seanlo_series.index, seanlo_series, bottom=lo_series + sean_series, color=seanlo_color, label="Sean/Lo", width=20)

    ax.set_title(f"{code} 持股變化")
    ax.legend()
    st.pyplot(fig)


    # 將 index 轉為 timestamp，供繪圖使用
    monthly_Lo.index = monthly_Lo.index.to_timestamp()
    monthly_Sean.index = monthly_Sean.index.to_timestamp()
    monthly_SeanLo.index = monthly_SeanLo.index.to_timestamp()

    # 加入顏色標籤
    def color_map(series):
        return [
            "#D3D3D3" if v == 0 else c
            for v, c in zip(series, ["#87CEEB"] * len(series))
        ]

    return monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, monthly_Lo.index, df
