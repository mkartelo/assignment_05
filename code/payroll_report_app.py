"""
payroll_report_app.py — the quarter at a glance, for someone who never opens a terminal.

Every Friday since September the office manager at Salt City Coffee has downloaded
a payroll export from the Assignment 04 app; before that she typed the same file
by hand. The owner now wants to know where the hours went this quarter, the
accountant wants pay by month and department, and the manager wants to see who
has been missing shifts. This page answers all three from the pile of exports.

Same shape as Assignment 04: the page *assembles* the pipeline — one call to
`build_history` does the cleaning — and then shows the reports, filtered by the
department and dates the user picks.

Run it:  Run and Debug -> "Streamlit Run: Current File"
Test it: pytest tests/test_pipeline.py -k app
"""
# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignments 03 and 04 — plus two
# new ones, st.date_input and st.bar_chart. README Step 8 has the exact widgets,
# keys and labels; the tests in tests/test_pipeline.py -k app check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster   <- load_employees()                           (fixed; not uploaded)
#   uploads  <- st.file_uploader, key="exports", accept_multiple_files=True
#               (an empty list until files are chosen)
#   if there are uploads:
#       history <- build_history([load_export(u) for u in uploads], roster)
#       st.warning naming any employeeid with no department (not on the roster);
#           the reports below use only the rows that matched
#       st.selectbox, key="department": "All" plus each department
#       st.date_input, key="dates": a (start, end) range, defaulting to the first
#           and last pay_date — compare against pay_date.dt.date to filter
#       the selection as a subheader
#       four st.metric cards in st.columns(4): Weeks, Employees, Total hours,
#           Total gross pay — counts are .nunique(), totals are .sum()
#       st.bar_chart of pay_by_month(selected), with month as the x axis
#       st.dataframe of summarize_employees(selected)
#       st.dataframe of hours_grid(selected), then of missed_weeks(that grid)
#       st.download_button, key="download": pay_by_month(...).to_csv(index=False)
#
# What the page does NOT do: cleaning, grouping, pivoting. If you find yourself
# writing a groupby or a pivot_table here, that logic belongs in the package.
import streamlit as st
from payroll.extract import load_employees, load_export
from payroll.summarize import build_history
from payroll.summarize import summarize_employees
from payroll.reshape import hours_grid, missed_weeks, pay_by_month

st.title("Salt City Coffee — Quarterly Payroll Report")
st.write("Upload your weekly payroll exports to view the quarterly report.")

roster = load_employees()

uploads = st.file_uploader(
    "Upload payroll exports",
    key="exports",
    accept_multiple_files=True
)

if uploads:
    history = build_history(
        [load_export(u) for u in uploads],
        roster
    )

    unmatched = history[history["department"].isna()]

    if not unmatched.empty:
        st.warning(
            "Unmatched employee IDs: "
            + ", ".join(unmatched["employeeid"].astype(str).unique())
        )

    history = history.dropna(subset=["department"])

    departments = ["All"] + sorted(history["department"].unique().tolist())

    department = st.selectbox(
        "Department",
        departments,
        key="department"
    )

    start = history["pay_date"].min().date()
    end = history["pay_date"].max().date()

    dates = st.date_input(
        "Pay date range",
        value=(start, end),
        key="dates"
    )

    selected = history.copy()

    if department != "All":
        selected = selected[selected["department"] == department]

    if len(dates) == 2:
        selected = selected[
            (selected["pay_date"].dt.date >= dates[0])
            & (selected["pay_date"].dt.date <= dates[1])
        ]

    st.subheader("Quarterly Payroll Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Weeks", selected["week_ending"].nunique())
    c2.metric("Employees", selected["employee_id"].nunique())
    c3.metric("Total hours", f'{selected["hours_worked"].sum():,.2f}')
    c4.metric("Total gross pay", f'${selected["gross_pay"].sum():,.2f}')

    monthly = pay_by_month(selected)

    st.subheader("Pay by Month")
    st.bar_chart(monthly, x="month")

    st.subheader("Employee Summary")
    st.dataframe(summarize_employees(selected))

    grid = hours_grid(selected)

    st.subheader("Hours by Week")
    st.dataframe(grid)

    st.subheader("Missed Weeks")
    st.dataframe(missed_weeks(grid))

    st.download_button(
        "Download Monthly Payroll CSV",
        data=monthly.to_csv(index=False),
        file_name="monthly_payroll.csv",
        mime="text/csv",
        key="download"
    )
