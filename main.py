
import pandas as pd
from collections import defaultdict

# === 檔案路徑設定 ===
transactions_file = "transactions.xlsx"
dividends_file = "dividends.xlsx"
year_end_file = "year_end_prices.xlsx"

# === 匯率與價格資料讀取 ===
df_year_end = pd.read_excel(year_end_file)

def get_year_end_price(code, year):
    row = df_year_end[(df_year_end['股票代號'] == code) & (df_year_end['年度'] == year)]
    if row.empty:
        return None, None
    return float(row.iloc[0]['年末股價']), float(row.iloc[0]['年末匯率'])

# === FIFO 成本處理 ===
def calculate_fifo(transactions, year, owner_tag):
    holdings = []
    realized_profit = 0.0
    unrealized_profit = 0.0

    for _, row in transactions.iterrows():
        if row['備註'] != owner_tag:
            continue
        date = pd.to_datetime(row['交易日期'])
        y = date.year
        if y > year:
            continue
        code = str(row['股票代號'])
        price = row['價格']
        qty = int(row['買賣股數'])
        fee = float(row['手續費']) if not pd.isna(row['手續費']) else 0.0
        tax = float(row['稅金']) if not pd.isna(row['稅金']) else 0.0

        if qty > 0:
            holdings.append([code, qty, price, fee, tax])
        else:
            qty_to_sell = -qty
            while qty_to_sell > 0 and holdings:
                h_code, h_qty, h_price, h_fee, h_tax = holdings[0]
                if h_code != code:
                    holdings.pop(0)
                    continue
                sell_qty = min(h_qty, qty_to_sell)
                cost_basis = sell_qty * h_price + h_fee * (sell_qty / h_qty) + h_tax * (sell_qty / h_qty)
                revenue = sell_qty * price - fee * (sell_qty / qty) - tax * (sell_qty / qty)
                realized_profit += revenue - cost_basis
                qty_to_sell -= sell_qty
                if sell_qty < h_qty:
                    holdings[0][1] -= sell_qty
                else:
                    holdings.pop(0)

    # 計算未實現損益
    for code, qty, price, fee, tax in holdings:
        if qty <= 0:
            continue
        year_end_price, fx = get_year_end_price(code, year)
        if year_end_price:
            unrealized_profit += qty * (year_end_price - price)

    return realized_profit, unrealized_profit

# === 股利收入統計 ===
def calculate_dividends(dividends, year, owner_tag):
    total = 0.0
    for _, row in dividends.iterrows():
        if row['動作'] != '股息':
            continue
        date = pd.to_datetime(row['交易日期'])
        if date.year != year:
            continue
        if owner_tag not in str(row['資產名稱']):
            continue
        if pd.isna(row['現金股利']):
            continue
        total += float(row['現金股利'])
    return total

# === 每月持股數量報表 ===
def generate_monthly_holdings(transactions):
    df = transactions.copy()
    df["交易日期"] = pd.to_datetime(df["交易日期"])
    df["年月"] = df["交易日期"].dt.to_period("M")
    df["股票代號"] = df["股票代號"].astype(str)
    df["買賣股數"] = df["買賣股數"].astype(int)

    grouped = (
        df.dropna(subset=["備註"])
          .groupby(["年月", "備註", "股票代號"])["買賣股數"]
          .sum()
          .reset_index()
          .sort_values(by=["備註", "股票代號", "年月"])
    )

    grouped["年月"] = grouped["年月"].astype(str)
    grouped["持股數量"] = grouped.groupby(["備註", "股票代號"])["買賣股數"].cumsum()
    df_monthly = grouped.drop(columns="買賣股數")
    df_monthly.columns = ["年月", "帳戶", "股票代號", "持股數量"]
    df_monthly = df_monthly[df_monthly["持股數量"] != 0]
    df_monthly.to_excel("每月持股數量.xlsx", index=False)
    print("📊 每月持股數量已輸出！")

# === 主程序 ===
def main():
    df_tx = pd.read_excel(transactions_file)
    df_dv = pd.read_excel(dividends_file)
    years = sorted(df_tx['交易日期'].dropna().apply(lambda x: pd.to_datetime(x).year).unique())

    result = []
    for year in years:
        for owner in ['Sean', 'Lo', 'Sean/Lo']:
            realized, unrealized = calculate_fifo(df_tx, year, owner)
            dividends = calculate_dividends(df_dv, year, owner)
            total_gain = realized + unrealized + dividends
            result.append({
                '年度': year,
                '帳戶': owner,
                '已實現損益': realized,
                '未實現損益': unrealized,
                '股利收入': dividends,
                '總報酬': total_gain,
            })

    df_result = pd.DataFrame(result)
    df_result.to_excel("年度損益報表.xlsx", index=False)
    print("✅ 年度損益報表已完成！請查看：年度損益報表.xlsx")

    generate_monthly_holdings(df_tx)

if __name__ == "__main__":
    main()
