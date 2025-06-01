import pandas as pd
from modules.time_utils import to_period_index

def parse_cash_balances(filepath="data/cash_accounts.xlsx"):
    df = pd.read_excel(filepath, sheet_name="monthly_balance")
    df["月份"] = to_period_index(df["日期"])
    df = df[["月份", "擁有者", "等值金額"]]
    summary = df.groupby(["月份", "擁有者"])["等值金額"].sum().unstack()
    summary = summary.sort_index().ffill().fillna(0)  # ✨ 用 ffill 填滿空欄，再補 0


    all_months = pd.period_range(df["月份"].min(), df["月份"].max(), freq="M")
    summary = summary.reindex(all_months, fill_value=0)
    summary.index.name = "月份"

    return summary

def parse_cash_detail(filepath="data/cash_accounts.xlsx"):
    df = pd.read_excel(filepath, sheet_name="monthly_balance")
    df["月份"] = to_period_index(df["日期"])
    df["帳戶全名"] = df["銀行"] + "_" + df["帳戶"]
    df = df[["月份", "擁有者", "帳戶全名", "等值金額"]]

    detail = df.groupby(["月份", "擁有者", "帳戶全名"])["等值金額"].sum()
    return detail
