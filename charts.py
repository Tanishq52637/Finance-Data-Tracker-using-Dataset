# charts.py
# Finance Data Tracker — Visualization Module
# All Matplotlib/Seaborn charts live here.
# Each function saves a PNG to the /charts folder and also returns
# the Figure so the dashboard can embed it directly.

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — works without a display

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
import os

from analysis import (
    load_data,
    get_monthly_summary,
    get_category_summary,
    get_payment_summary,
    get_category_monthly_pivot,
    get_cumulative_savings,
    get_top_expenses,
)

# ─── GLOBAL STYLE ─────────────────────────────────────────────────────────────

# Tried a few themes — this one looks cleanest for finance stuff
plt.rcParams.update(
    {
        "figure.facecolor": "#1e1e2e",
        "axes.facecolor": "#1e1e2e",
        "axes.edgecolor": "#44475a",
        "axes.labelcolor": "#cdd6f4",
        "axes.titlecolor": "#cdd6f4",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.color": "#6c7086",
        "ytick.color": "#6c7086",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.facecolor": "#313244",
        "legend.edgecolor": "#44475a",
        "legend.labelcolor": "#cdd6f4",
        "legend.fontsize": 9,
        "grid.color": "#313244",
        "grid.linewidth": 0.6,
        "text.color": "#cdd6f4",
        "font.family": "sans-serif",
    }
)

# Colour palette — India flag colours + a few extras
COLORS = {
    "income": "#a6e3a1",  # green
    "expense": "#f38ba8",  # red/pink
    "savings": "#89b4fa",  # blue
    "accent": "#cba6f7",  # purple
    "orange": "#fab387",
    "yellow": "#f9e2af",
    "teal": "#94e2d5",
    "sky": "#89dceb",
}

CATEGORY_PALETTE = [
    "#f38ba8",
    "#fab387",
    "#f9e2af",
    "#a6e3a1",
    "#94e2d5",
    "#89dceb",
    "#89b4fa",
    "#cba6f7",
    "#f5c2e7",
    "#eba0ac",
    "#313244",
    "#45475a",
]

OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  Saved → {path}")
    return path


def _rupee(x, pos):
    """Formatter that adds ₹ and K/L suffix to axis ticks."""
    if x >= 100000:
        return f"₹{x/100000:.1f}L"
    elif x >= 1000:
        return f"₹{x/1000:.0f}K"
    return f"₹{int(x)}"


# ─── 1. MONTHLY INCOME vs EXPENSE BAR CHART ──────────────────────────────────


def plot_monthly_bar(df):
    """
    Grouped bar chart: Income vs Expense per month.
    Also draws a savings line on top.
    """
    monthly = get_monthly_summary(df)

    x = np.arange(len(monthly))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(13, 5))
    fig.suptitle(
        "Monthly Income vs Expense (2024)", fontsize=15, fontweight="bold", y=1.01
    )

    bars1 = ax1.bar(
        x - width / 2,
        monthly["income"],
        width,
        label="Income",
        color=COLORS["income"],
        alpha=0.85,
    )
    bars2 = ax1.bar(
        x + width / 2,
        monthly["expense"],
        width,
        label="Expense",
        color=COLORS["expense"],
        alpha=0.85,
    )

    # Savings line on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(
        x,
        monthly["savings"],
        color=COLORS["savings"],
        marker="o",
        linewidth=2,
        markersize=6,
        label="Net Savings",
        zorder=5,
    )
    ax2.axhline(0, color="#44475a", linewidth=0.8, linestyle="--")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(_rupee))
    ax2.set_ylabel("Net Savings", color=COLORS["savings"])
    ax2.tick_params(axis="y", colors=COLORS["savings"])

    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly.index)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_rupee))
    ax1.set_ylabel("Amount (₹)")
    ax1.grid(axis="y", alpha=0.4)

    # Annotate bars with value labels
    for bar in bars1:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            _rupee(bar.get_height(), None),
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=COLORS["income"],
        )
    for bar in bars2:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            _rupee(bar.get_height(), None),
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=COLORS["expense"],
        )

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    fig.tight_layout()
    return fig, _save(fig, "01_monthly_income_expense.png")


# ─── 2. CATEGORY PIE / DONUT CHART ───────────────────────────────────────────


def plot_category_donut(df):
    """
    Donut chart showing % share of each expense category.
    """
    cat_df = get_category_summary(df)

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.suptitle("Expense Breakdown by Category", fontsize=14, fontweight="bold")

    wedges, texts, autotexts = ax.pie(
        cat_df["total"],
        labels=None,
        colors=CATEGORY_PALETTE[: len(cat_df)],
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        pctdistance=0.78,
        startangle=140,
        wedgeprops={"linewidth": 1.5, "edgecolor": "#1e1e2e", "width": 0.5},
    )

    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("#1e1e2e")
        t.set_fontweight("bold")

    # Legend outside the chart
    legend_labels = [
        f"{cat} — ₹{total:,.0f}" for cat, total in zip(cat_df.index, cat_df["total"])
    ]
    patches = [
        mpatches.Patch(color=CATEGORY_PALETTE[i], label=legend_labels[i])
        for i in range(len(cat_df))
    ]
    ax.legend(
        handles=patches, loc="center left", bbox_to_anchor=(1.0, 0.5), framealpha=0.1
    )

    # Centre text
    ax.text(
        0,
        0,
        f"₹{cat_df['total'].sum()/100000:.1f}L\nTotal Spend",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#cdd6f4",
    )

    fig.tight_layout()
    return fig, _save(fig, "02_category_donut.png")


# ─── 3. SPENDING HEATMAP ─────────────────────────────────────────────────────


def plot_heatmap(df):
    """
    Seaborn heatmap — Category vs Month spending intensity.
    Really useful for spotting seasonal patterns.
    """
    pivot = get_category_monthly_pivot(df)

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle(
        "Category × Month Spending Heatmap (₹)", fontsize=14, fontweight="bold"
    )

    # Format annotations to show K values
    annot = pivot.applymap(lambda v: f"₹{v/1000:.1f}K" if v > 0 else "—")

    sns.heatmap(
        pivot,
        ax=ax,
        annot=annot,
        fmt="",
        cmap="RdYlGn_r",
        linewidths=0.5,
        linecolor="#1e1e2e",
        cbar_kws={"label": "Amount Spent (₹)", "shrink": 0.6},
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Category")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    fig.tight_layout()
    return fig, _save(fig, "03_heatmap_category_month.png")


# ─── 4. CUMULATIVE SAVINGS LINE CHART ────────────────────────────────────────


def plot_cumulative_savings(df):
    """
    Shows how savings grew (or shrank) over the year.
    The steeper the slope, the better the saving period.
    """
    cum_savings = get_cumulative_savings(df)

    fig, ax = plt.subplots(figsize=(13, 4.5))
    fig.suptitle("Cumulative Savings Trend — 2024", fontsize=14, fontweight="bold")

    # Colour under curve green if positive, red if negative
    ax.fill_between(
        cum_savings.index,
        cum_savings.values,
        0,
        where=(cum_savings.values >= 0),
        color=COLORS["income"],
        alpha=0.25,
        label="Positive",
    )
    ax.fill_between(
        cum_savings.index,
        cum_savings.values,
        0,
        where=(cum_savings.values < 0),
        color=COLORS["expense"],
        alpha=0.25,
        label="Negative",
    )

    ax.plot(
        cum_savings.index,
        cum_savings.values,
        color=COLORS["savings"],
        linewidth=2.2,
        zorder=5,
    )

    ax.axhline(0, color="#44475a", linewidth=1, linestyle="--")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_rupee))
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Net Savings")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(framealpha=0.2)

    # Final value annotation
    final_val = cum_savings.iloc[-1]
    ax.annotate(
        f"Year-end\n{_rupee(final_val, None)}",
        xy=(cum_savings.index[-1], final_val),
        xytext=(-80, 20),
        textcoords="offset points",
        color=COLORS["savings"],
        fontsize=9,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": COLORS["savings"]},
    )

    fig.tight_layout()
    return fig, _save(fig, "04_cumulative_savings.png")


# ─── 5. PAYMENT METHOD BAR ───────────────────────────────────────────────────


def plot_payment_methods(df):
    """
    Horizontal bar chart of spending by payment method.
    """
    pay_df = get_payment_summary(df)

    # Clean up labels for display
    label_map = {
        "upi": "UPI",
        "credit_card": "Credit Card",
        "bank_transfer": "Bank Transfer",
        "cash": "Cash",
    }
    pay_df.index = [label_map.get(i, i) for i in pay_df.index]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.suptitle("Spending by Payment Method", fontsize=13, fontweight="bold")

    colors = [COLORS["savings"], COLORS["accent"], COLORS["orange"], COLORS["teal"]]
    bars = ax.barh(
        pay_df.index,
        pay_df["total"],
        color=colors[: len(pay_df)],
        height=0.5,
        alpha=0.85,
    )

    # Labels on bars
    for bar, (_, row) in zip(bars, pay_df.iterrows()):
        ax.text(
            bar.get_width() + 1000,
            bar.get_y() + bar.get_height() / 2,
            f"₹{row['total']:,.0f}  ({row['percent']}%)",
            va="center",
            fontsize=9,
            color="#cdd6f4",
        )

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_rupee))
    ax.set_xlabel("Total Amount Spent")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, pay_df["total"].max() * 1.35)

    fig.tight_layout()
    return fig, _save(fig, "05_payment_methods.png")


# ─── 6. TOP 10 EXPENSES ───────────────────────────────────────────────────────


def plot_top_expenses(df):
    """
    Horizontal bar chart of the 10 biggest single transactions.
    """
    top = get_top_expenses(df, n=10)
    labels = [
        (
            f"{row['description'][:28]}..."
            if len(row["description"]) > 28
            else row["description"]
        )
        for _, row in top.iterrows()
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Top 10 Single Expenses", fontsize=13, fontweight="bold")

    bar_colors = [
        COLORS["expense"] if i < 3 else COLORS["orange"] if i < 6 else COLORS["yellow"]
        for i in range(len(top))
    ]

    bars = ax.barh(
        labels[::-1],
        top["amount"][::-1].values,
        color=bar_colors[::-1],
        height=0.6,
        alpha=0.85,
    )

    for bar in bars:
        ax.text(
            bar.get_width() + 200,
            bar.get_y() + bar.get_height() / 2,
            f"₹{bar.get_width():,.0f}",
            va="center",
            fontsize=8.5,
            color="#cdd6f4",
        )

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_rupee))
    ax.set_xlabel("Amount (₹)")
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, top["amount"].max() * 1.25)

    fig.tight_layout()
    return fig, _save(fig, "06_top_expenses.png")


# ─── 7. SAVINGS RATE MONTHLY ─────────────────────────────────────────────────


def plot_savings_rate(df):
    """
    Line chart showing savings rate % across months.
    20% benchmark line drawn for reference.
    """
    monthly = get_monthly_summary(df)

    fig, ax = plt.subplots(figsize=(11, 4))
    fig.suptitle("Monthly Savings Rate (%)", fontsize=13, fontweight="bold")

    ax.plot(
        monthly.index,
        monthly["savings_rate"],
        color=COLORS["accent"],
        marker="o",
        linewidth=2.2,
        markersize=7,
        label="Savings Rate",
    )

    # 20% rule benchmark
    ax.axhline(
        20,
        color=COLORS["income"],
        linewidth=1.2,
        linestyle="--",
        alpha=0.7,
        label="20% Target",
    )
    ax.axhline(0, color=COLORS["expense"], linewidth=0.8, linestyle="--", alpha=0.5)

    # Shade regions
    ax.fill_between(
        monthly.index,
        monthly["savings_rate"],
        20,
        where=(monthly["savings_rate"] >= 20),
        color=COLORS["income"],
        alpha=0.12,
        label="Above target",
    )
    ax.fill_between(
        monthly.index,
        monthly["savings_rate"],
        0,
        where=(monthly["savings_rate"] < 0),
        color=COLORS["expense"],
        alpha=0.15,
        label="Deficit",
    )

    # Annotate each point
    for i, (month, row) in enumerate(monthly.iterrows()):
        ax.text(
            i,
            row["savings_rate"] + 1.2,
            f"{row['savings_rate']:.1f}%",
            ha="center",
            fontsize=8,
            color=COLORS["accent"],
        )

    ax.set_ylabel("Savings Rate (%)")
    ax.set_xlabel("Month")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(framealpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig, _save(fig, "07_savings_rate.png")


# ─── GENERATE ALL CHARTS ─────────────────────────────────────────────────────


def generate_all_charts(filepath="data.csv"):
    print("Loading data...")
    df = load_data(filepath)

    print("Generating charts...")
    plot_monthly_bar(df)
    plot_category_donut(df)
    plot_heatmap(df)
    plot_cumulative_savings(df)
    plot_payment_methods(df)
    plot_top_expenses(df)
    plot_savings_rate(df)

    print(f"\nDone! All 7 charts saved to /{OUTPUT_DIR}/")
    return df


if __name__ == "__main__":
    generate_all_charts()
