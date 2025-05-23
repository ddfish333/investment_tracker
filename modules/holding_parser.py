import pandas as pd

def parse_monthly_holdings(filepath):
    df = pd.read_excel(filepath)
    df["交易日期"] = pd.to_datetime(df["交易日期"])
    df["月份"] = df["交易日期"].dt.to_period("M")
    df["來源"] = df["備註"].fillna("其他")
    df["幣別"] = df["幣別"].fillna("TWD")

    all_codes = sorted(df["股票代號"].dropna().unique(), key=lambda x: str(x))
    all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")

    def initialize_holdings():
        return pd.DataFrame(index=all_months, columns=all_codes).fillna(0), {code: 0 for code in all_codes}

    monthly_Lo, current_Lo = initialize_holdings()
    monthly_Sean, current_Sean = initialize_holdings()
    monthly_SeanLo, current_SeanLo = initialize_holdings()

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
            monthly_Lo.at[month, code] = current_Lo[code]
            monthly_Sean.at[month, code] = current_Sean[code]
            monthly_SeanLo.at[month, code] = current_SeanLo[code]

    # datetime index
    monthly_Lo.index = monthly_Lo.index.to_timestamp()
    monthly_Sean.index = monthly_Sean.index.to_timestamp()
    monthly_SeanLo.index = monthly_SeanLo.index.to_timestamp()

    return {
        "Lo": monthly_Lo,
        "Sean": monthly_Sean,
        "Sean/Lo": monthly_SeanLo,
    }
