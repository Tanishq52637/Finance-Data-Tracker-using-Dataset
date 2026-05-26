# analysis.py
# Finance Data Tracker
# This file loads the CSV, cleans the data, and runs all the
# summary calculations that the dashboard and charts use.

import pandas as pd
import numpy as np
import os

# ─── LOAD & CLEAN ────────────────────────────────────────────────────────────


def load_data(filepath="data.csv"):
    """
    Reads the CSV and does basic cleaning.
    Returns a cleaned DataFrame ready for analysis.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Could not find {filepath}. Make sure data.csv is in the same folder."
        )

    df = pd.read_csv(filepath)

    # Parse dates properly
    df["date"] = pd.to_datetime(df["date"], dayfirst=False)

    # Clean up text columns
    df["category"] = df["category"].str.strip().str.title()
    df["type"] = df["type"].str.strip().str.lower()
    df["payment_method"] = df["payment_method"].str.strip()

    # Remove rows where amount is missing or negative (data entry errors)
    df = df.dropna(subset=["amount"])
    df = df[df["amount"] > 0]

    # Add useful derived columns
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")  # Jan, Feb ...
    df["year"] = df["date"].dt.year
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.day_name()

    # Separate income and expense for easier filtering later
    df["is_expense"] = df["type"] == "expense"
    df["is_income"] = df["type"] == "income"

    return df


# ─── SUMMARY STATS ───────────────────────────────────────────────────────────


def get_summary(df):
    """
    Returns a dict with the key financial KPIs for the full dataset.
    Used on the dashboard header cards.
    """
    total_income = df[df["is_income"]]["amount"].sum()
    total_expense = df[df["is_expense"]]["amount"].sum()
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(net_savings, 2),
        "savings_rate": round(savings_rate, 2),
        "total_txns": len(df),
        "avg_monthly_expense": round(
            df[df["is_expense"]].groupby("month")["amount"].sum().mean(), 2
        ),
    }


# ─── MONTHLY BREAKDOWN ───────────────────────────────────────────────────────


def get_monthly_summary(df):
    """
    Returns a DataFrame with income, expense, and savings per month.
    Months are sorted Jan → Dec.
    """
    month_order = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    income_by_month = df[df["is_income"]].groupby("month_name")["amount"].sum()
    expense_by_month = df[df["is_expense"]].groupby("month_name")["amount"].sum()

    monthly = pd.DataFrame(
        {
            "income": income_by_month,
            "expense": expense_by_month,
        }
    ).fillna(0)

    monthly["savings"] = monthly["income"] - monthly["expense"]
    monthly["savings_rate"] = (monthly["savings"] / monthly["income"] * 100).round(1)

    # Sort by calendar order
    monthly = monthly.reindex([m for m in month_order if m in monthly.index])

    return monthly


# ─── CATEGORY BREAKDOWN ──────────────────────────────────────────────────────


def get_category_summary(df):
    """
    Returns total spending per category (expenses only), sorted high to low.
    Also includes % share of total spending.
    """
    expenses = df[df["is_expense"]]
    cat_summary = (
        expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    )

    cat_df = pd.DataFrame(
        {
            "total": cat_summary,
            "percent": (cat_summary / cat_summary.sum() * 100).round(1),
        }
    )

    return cat_df


# ─── PAYMENT METHOD BREAKDOWN ────────────────────────────────────────────────


def get_payment_summary(df):
    """
    How much was spent via UPI, credit card, cash, bank transfer.
    """
    pay_summary = df[df["is_expense"]].groupby("payment_method")["amount"].sum()
    pay_df = pd.DataFrame(
        {
            "total": pay_summary,
            "percent": (pay_summary / pay_summary.sum() * 100).round(1),
        }
    ).sort_values("total", ascending=False)

    return pay_df


# ─── TOP EXPENSES ─────────────────────────────────────────────────────────────


def get_top_expenses(df, n=10):
    """
    Returns the n biggest single expense transactions.
    Useful for spotting big-ticket spends.
    """
    return (
        df[df["is_expense"]]
        .nlargest(n, "amount")[
            ["date", "category", "description", "amount", "payment_method"]
        ]
        .reset_index(drop=True)
    )


# ─── MONTHLY CATEGORY HEATMAP DATA ───────────────────────────────────────────


def get_category_monthly_pivot(df):
    """
    Returns a pivot table: rows = categories, columns = months.
    Used for the heatmap chart.
    """
    expenses = df[df["is_expense"]]

    pivot = expenses.pivot_table(
        index="category",
        columns="month_name",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    )

    # Reorder columns by calendar month
    month_order = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])

    return pivot


# ─── CUMULATIVE SAVINGS ───────────────────────────────────────────────────────


def get_cumulative_savings(df):
    """
    Returns day-wise cumulative savings (income - expense) across the year.
    Shows the overall wealth accumulation trend.
    """
    df_sorted = df.sort_values("date").copy()
    df_sorted["signed_amount"] = df_sorted.apply(
        lambda row: row["amount"] if row["is_income"] else -row["amount"], axis=1
    )

    daily = df_sorted.groupby("date")["signed_amount"].sum()
    cumulative = daily.cumsum()

    return cumulative


# ─── QUICK HEALTH CHECK ───────────────────────────────────────────────────────


def financial_health_check(df):
    """
    Generates a simple financial health report with warnings/tips.
    Based on basic personal finance rules (50/30/20 rule, etc.)
    """
    summary = get_summary(df)
    cat_df = get_category_summary(df)
    monthly_df = get_monthly_summary(df)

    tips = []
    warnings = []

    # Savings rate check (20% is the benchmark)
    if summary["savings_rate"] < 10:
        warnings.append(
            f"⚠️  Your savings rate is only {summary['savings_rate']}%. Try to save at least 20% of income."
        )
    elif summary["savings_rate"] < 20:
        tips.append(
            f"💡 Savings rate is {summary['savings_rate']}%. Getting there — aim for 20%+."
        )
    else:
        tips.append(f"✅ Great savings rate of {summary['savings_rate']}%! Keep it up.")

    # Check if any month had negative savings
    negative_months = monthly_df[monthly_df["savings"] < 0]
    if not negative_months.empty:
        months_str = ", ".join(negative_months.index.tolist())
        warnings.append(f"⚠️  You spent more than you earned in: {months_str}.")

    # Check if rent > 30% of income (common rule)
    if "Rent" in cat_df.index:
        rent_pct = cat_df.loc["Rent", "percent"]
        if rent_pct > 30:
            warnings.append(
                f"⚠️  Rent is {rent_pct}% of total expenses — that's on the higher side."
            )

    # Check top spending category
    top_cat = cat_df.index[0]
    top_pct = cat_df["percent"].iloc[0]
    tips.append(f"📊 Biggest spend category: {top_cat} ({top_pct}% of expenses).")

    return {"tips": tips, "warnings": warnings, "summary": summary}


# ─── MAIN — quick sanity check ───────────────────────────────────────────────

if __name__ == "__main__":
    df = load_data("data.csv")

    print("=== DATA LOADED ===")
    print(f"Total rows   : {len(df)}")
    print(f"Date range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Categories   : {df['category'].nunique()}")
    print()

    summary = get_summary(df)
    print("=== FINANCIAL SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k:<25}: ₹{v:,.0f}" if "rate" not in k else f"  {k:<25}: {v}%")
    print()

    health = financial_health_check(df)
    print("=== HEALTH CHECK ===")
    for tip in health["tips"]:
        print(" ", tip)
    for warn in health["warnings"]:
        print(" ", warn)
