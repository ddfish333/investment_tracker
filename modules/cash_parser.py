# cash_parser.py
import pandas as pd
from modules.time_utils import to_period_index, get_today_period
from config import CASH_ACCOUNT_FILE, CASH_ACCOUNT_SHEET, FX_SNAPSHOT_PATH


def load_fx_rates():
    fx_df = pd.read_parquet(FX_SNAPSHOT_PATH)
    fx_df.index = to_period_index(fx_df.index)
    fx_long = fx_df.stack().reset_index()
    fx_long.columns = ["Month", "Currency", "Rate"]
    return fx_long.set_index(["Month", "Currency"])["Rate"]


def parse_cash_balances(filepath=CASH_ACCOUNT_FILE, sheet_name=CASH_ACCOUNT_SHEET):
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    df["月份"] = to_period_index(df["日期"])
    fx = load_fx_rates()

    def convert(row):
        month, currency, amount = row["月份"], row["幣別"], row["金額"]
        if currency == "TWD":
            return amount
        try:
            return amount * fx.loc[(month, currency)]
        except KeyError:
            raise ValueError(f"❌ 找不到 {month} 的 {currency} 匯率")

    df["TWD金額"] = df.apply(convert, axis=1)

    df = df[df["出資比例"].notnull()]
    df["金額分攤"] = df["TWD金額"] * df["出資比例"]

    grouped = df.groupby(["月份", "擁有者", "幣別"])["金額分攤"].sum().reset_index()
    grouped = grouped.pivot_table(index="月份", columns=["擁有者", "幣別"], values="金額分攤", aggfunc="sum").fillna(0)
    grouped.columns = [f"{owner}_{currency}_CASH" for owner, currency in grouped.columns]

    # 補齊到當月
    today_month = get_today_period()
    all_months = pd.period_range(grouped.index.min(), today_month, freq="M")
    grouped = grouped.reindex(all_months, fill_value=0)
    grouped.index.name = "月份"

    return grouped


def parse_cash_detail(filepath=CASH_ACCOUNT_FILE, sheet_name=CASH_ACCOUNT_SHEET):
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    df["月份"] = to_period_index(df["日期"])
    df["帳戶全名"] = df["銀行"] + "_" + df["帳戶"]
    fx = load_fx_rates()

    def convert(row):
        month, currency, amount = row["月份"], row["幣別"], row["金額"]
        if currency == "TWD":
            return amount
        try:
            return amount * fx.loc[(month, currency)]
        except KeyError:
            raise ValueError(f"❌ 找不到 {month} 的 {currency} 匯率")

    df["TWD金額"] = df.apply(convert, axis=1)

    df = df[df["出資比例"].notnull()]
    df["金額分攤"] = df["TWD金額"] * df["出資比例"]

    detail = df.groupby(["月份", "擁有者", "帳戶全名"])["金額分攤"].sum()
    detail.name = "TWD金額"

    return detail