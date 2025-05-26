import pandas as pd

def parse_monthly_holdings(filepath):
    import streamlit as st  # 若你在 Streamlit 裡用，這行請保留
    df = pd.read_excel(filepath)

    # 檢查必要欄位是否存在
    required_columns = ["交易日期", "股票代號", "買賣股數", "幣別", "備註"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"❌ 資料缺少必要欄位：{col}")

    df["交易日期"] = pd.to_datetime(df["交易日期"])
    df["月份"] = df["交易日期"].dt.to_period("M")
    df["來源"] = df["備註"].fillna("其他")
    df["幣別"] = df["幣別"].fillna("TWD")

    all_codes = sorted(df["股票代號"].dropna().unique(), key=lambda x: str(x))
    all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

    def initialize():
        return pd.DataFrame(index=all_months.to_timestamp(), columns=all_codes).fillna(0), {code: 0 for code in all_codes}

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
            monthly_Lo.at[month.to_timestamp(), code] = current_Lo[code]
            monthly_Sean.at[month.to_timestamp(), code] = current_Sean[code]
            monthly_SeanLo.at[month.to_timestamp(), code] = current_SeanLo[code]

    return monthly_Lo, monthly_Sean, monthly_SeanLo, all_codes, all_months.to_timestamp()
