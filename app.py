import streamlit as st
from analysis import (
    load_data,
    get_summary,
    get_monthly_summary,
    financial_health_check,
)

from charts import (
    plot_monthly_bar,
    plot_category_donut,
    plot_heatmap,
    plot_cumulative_savings,
)

st.set_page_config(page_title="Finance Data Tracker", layout="wide")

st.title("Finance Data Tracker Dashboard")

# Load data
df = load_data("data.csv")

# Summary cards
summary = get_summary(df)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Income", f"₹{summary['total_income']:,.0f}")
col2.metric("Total Expense", f"₹{summary['total_expense']:,.0f}")
col3.metric("Net Savings", f"₹{summary['net_savings']:,.0f}")
col4.metric("Savings Rate", f"{summary['savings_rate']}%")

st.divider()

# Charts
st.subheader("Monthly Income vs Expense")

fig1, _ = plot_monthly_bar(df)
st.pyplot(fig1)

st.subheader("Expense Category Breakdown")

fig2, _ = plot_category_donut(df)
st.pyplot(fig2)

st.subheader("Spending Heatmap")

fig3, _ = plot_heatmap(df)
st.pyplot(fig3)

st.subheader("Cumulative Savings")

fig4, _ = plot_cumulative_savings(df)
st.pyplot(fig4)

# Financial health
health = financial_health_check(df)

st.subheader("Financial Health Report")

for tip in health["tips"]:
    st.success(tip)

for warn in health["warnings"]:
    st.warning(warn)
