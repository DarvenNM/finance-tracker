import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage

st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ---------------- TITLE ----------------
st.markdown("""
<style>
h1 {
    color: #1f4e79;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>💰 Personal Finance Tracker</h1>", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT,
    month TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

# ---------------- SIDEBAR ----------------
menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- REGISTER ----------------
if choice == "Register":

    st.subheader("📝 Create Account")

    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type="password")

    if st.button("Register"):
        try:
            cursor.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (new_user, new_password)
            )
            conn.commit()
            st.success("Account Created Successfully!")
        except:
            st.error("Username Already Exists")

# ---------------- LOGIN ----------------
if choice == "Login":

    if not st.session_state.logged_in:

        st.subheader("🔐 Login")

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_btn"):

            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )

            user = cursor.fetchone()

            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid Username or Password")

        st.stop()

# ---------------- BLOCK IF NOT LOGGED IN ----------------
if not st.session_state.logged_in:
    st.info("🔐 Please Login First")
    st.stop()

# ---------------- DASHBOARD HEADER ----------------
st.sidebar.info(f"Logged in as {st.session_state.username}")

if st.sidebar.button("Logout", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

st.info(f"👋 Welcome, {st.session_state.username}")
st.subheader("💰 Quick Balance Calculator")

income = st.number_input("Enter Income", min_value=0.0, key="income_input")
expense = st.number_input("Enter Expense", min_value=0.0, key="expense_input")

if st.button("Calculate Balance", key="calc_balance_btn"):

    balance = income - expense

    st.success(f"Remaining Balance: ₹{balance:.2f}")

# ---------------- TRANSACTION INPUT ----------------
transaction_type = st.selectbox(
    "Transaction Type",
    ["Income", "Expense"]
)

category = st.selectbox(
    "Category",
    ["Salary", "Food", "Travel", "Shopping", "Bills", "Others"]
)

amount = st.number_input("Amount", min_value=0.0)

date = st.date_input("Date")
month = date.strftime("%B")

if st.button("Add Transaction"):
    cursor.execute("""
        INSERT INTO transactions
        (username, type, category, amount, date, month)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        st.session_state.username,
        transaction_type,
        category,
        amount,
        str(date),
        month
    ))

    conn.commit()
    st.success("Transaction Added Successfully!")
# Display Data

st.subheader("📋 Transaction History")

selected_month = st.selectbox(
    "📅 Select Month",
    [
        "All",
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]
)

if selected_month == "All":

    df = pd.read_sql_query(
        """
        SELECT *
        FROM transactions
        WHERE username = ?
        """,
        conn,
        params=(st.session_state.username,)
    )

else:

    df = pd.read_sql_query(
        """
        SELECT *
        FROM transactions
        WHERE username = ?
        AND month = ?
        """,
        conn,
        params=(
            st.session_state.username,
            selected_month
        )
    )

st.dataframe(df)
csv = df.to_csv(index=False)

st.download_button(
    label="📥 Download Transactions",
    data=csv,
    file_name="transactions.csv",
    mime="text/csv"
)
# Delete Transaction

st.subheader("🗑️ Delete Transaction")

delete_id = st.number_input(
    "Enter Transaction ID to Delete",
    min_value=1,
    step=1
)

if st.button("Delete"):
    cursor.execute(
        "DELETE FROM transactions WHERE id=?",
        (delete_id,)
    )
    conn.commit()
    st.success("Transaction Deleted Successfully!")
    st.rerun()

# Calculations
if selected_month == "All":

    income = pd.read_sql_query(
        """
        SELECT SUM(amount) as total
        FROM transactions
        WHERE username = ?
        AND type='Income'
        """,
        conn,
        params=(st.session_state.username,)
    )

else:

    income = pd.read_sql_query(
        """
        SELECT SUM(amount) as total
        FROM transactions
        WHERE username = ?
        AND type='Income'
        AND month = ?
        """,
        conn,
        params=(
            st.session_state.username,
            selected_month
        )
    )

if selected_month == "All":

    expense = pd.read_sql_query(
        """
        SELECT SUM(amount) as total
        FROM transactions
        WHERE username = ?
        AND type='Expense'
        """,
        conn,
        params=(st.session_state.username,)
    )

else:

    expense = pd.read_sql_query(
        """
        SELECT SUM(amount) as total
        FROM transactions
        WHERE username = ?
        AND type='Expense'
        AND month = ?
        """,
        conn,
        params=(
            st.session_state.username,
            selected_month
        )
    )

total_income = income["total"][0]
total_expense = expense["total"][0]

if pd.isna(total_income):
    total_income = 0

if pd.isna(total_expense):
    total_expense = 0

balance = total_income - total_expense


st.subheader("📊 Financial Dashboard")
budget = st.number_input(
    "💰 Set Monthly Budget",
    min_value=0.0,
    value=10000.0
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 Income", f"₹{total_income}")

with col2:
    st.metric("💸 Expense", f"₹{total_expense}")

with col3:
    st.metric("🏦 Balance", f"₹{balance}")
st.subheader("🏆 Savings Goal Tracker")

goal = st.number_input(
    "Enter Your Savings Goal",
    min_value=1000.0,
    value=50000.0,
    step=1000.0
)

progress = min(balance / goal, 1.0)

st.progress(progress)

st.write(
    f"Progress: {progress*100:.1f}%"
)

remaining_goal = goal - balance
budget_usage = (total_expense / budget) * 100 if budget > 0 else 0

if remaining_goal > 0:
    st.info(
        f"₹{remaining_goal:.2f} left to reach your goal"
    )
else:
    st.success(
        "🎉 Savings Goal Achieved!"
    )    
    st.subheader("📢 Budget Status")
    st.subheader("📈 Monthly Income vs Expense Trend")

trend_data = pd.read_sql_query(
    """
    SELECT month, type, SUM(amount) as total
    FROM transactions
    WHERE username = ?
    GROUP BY month, type
    """,
    conn,
    params=(st.session_state.username,)
)

if not trend_data.empty:

    pivot_df = trend_data.pivot(
        index="month",
        columns="type",
        values="total"
    ).fillna(0)

    st.line_chart(pivot_df)
    st.subheader("🤖 Smart Financial Advisor")

if total_income > 0:

    expense_ratio = (total_expense / total_income) * 100
    savings_ratio = (balance / total_income) * 100

    st.write(f"📊 Expense Ratio: {expense_ratio:.2f}%")
    st.write(f"💰 Savings Ratio: {savings_ratio:.2f}%")

    # CASE 1: Income low + expenses high
    if expense_ratio > 90:
        st.error("🚨 Critical Financial Alert")
        st.write(
            """
            Your expenses are extremely high compared to your income.

            💡 Advisor Suggestions:
            - Stop non-essential shopping immediately
            - Avoid online impulse purchases
            - Reduce food ordering / outside food
            - Switch to a strict monthly budget plan
            - Try tracking every expense daily
            """
        )

    # CASE 2: High spending
    elif expense_ratio > 70:
        st.warning("⚠️ High Spending Detected")

        st.write(
            """
            You are spending a large portion of your income.

            💡 Advisor Suggestions:
            - Reduce shopping and entertainment expenses
            - Plan weekly budget for food and travel
            - Avoid unnecessary subscriptions
            - Try saving at least 20% of income
            """
        )

    # CASE 3: Moderate spending
    elif expense_ratio > 50:
        st.info("📉 Moderate Spending Pattern")

        st.write(
            """
            Your spending is okay but can be improved.

            💡 Advisor Suggestions:
            - Increase savings habit (auto-save if possible)
            - Track where money leaks happen
            - Reduce small frequent expenses (coffee, snacks)
            """
        )

    # CASE 4: Healthy
    else:
        st.success("🎉 Excellent Financial Health")

        st.write(
            """
            You are managing your money well!

            💡 Advisor Suggestions:
            - Increase investments or savings goal
            - Build emergency fund (3–6 months expenses)
            - Consider investing in SIP or fixed deposits
            """
        )

else:
    st.warning("No income data available for analysis")

remaining_budget = budget - total_expense

if total_expense > budget:

    st.error(
        f"⚠️ Budget Exceeded by ₹{total_expense - budget:.2f}"
    )
    st.subheader("🔔 Budget Alert Notification")

    if budget_usage >= 100:

       st.error(
        f"🚨 Budget Exceeded! You have used {budget_usage:.1f}% of your budget."
    )

    elif budget_usage >= 80:

       st.warning(
        f"⚠️ Warning! You have already used {budget_usage:.1f}% of your budget."
    )

    else:

       st.success(
        f"✅ Budget usage is healthy ({budget_usage:.1f}%)."
    )
else:

    st.success(
        f"✅ Remaining Budget: ₹{remaining_budget:.2f}"
    )
def create_pdf(total_income, total_expense, balance):
    pdf_file = "finance_report.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, f"Finance Report - {st.session_state.username}")

    c.setFont("Helvetica", 12)
    c.drawString(100, 760, f"Total Income: ₹{total_income}")
    c.drawString(100, 740, f"Total Expense: ₹{total_expense}")
    c.drawString(100, 720, f"Balance: ₹{balance}")

    c.save()

    return pdf_file    
if st.session_state.logged_in:
    pdf_file = create_pdf(total_income, total_expense, balance)

    with open(pdf_file, "rb") as file:
        st.download_button(
            label="📄 Download Finance Report",
            data=file,
            file_name="Finance_Report.pdf",
            mime="application/pdf"
        )
st.subheader("📧 Email Finance Report")

receiver_email = st.text_input(
    "Enter Recipient Email"
)

if st.button("📧 Send Report"):

    send_email(
        receiver_email,
        pdf_file
    )

    st.success("✅ Report Sent Successfully!")

st.caption(
    "Note: If the report is not visible in your Inbox, please check your Spam/Junk folder."
)
# Expense Pie Chart

expense_data = pd.read_sql_query(
    """
    SELECT category, SUM(amount) as total
    FROM transactions
    WHERE type='Expense'
    AND username=?
    GROUP BY category
    """,
    conn,
    params=(st.session_state.username,)
)

st.write("Expense Data")
st.dataframe(expense_data)

if len(expense_data) > 0:

    st.subheader("Expense Distribution")

    fig, ax = plt.subplots(figsize=(5,5))

    ax.pie(
        expense_data["total"],
        labels=expense_data["category"],
        autopct="%1.1f%%"
    )

    st.pyplot(fig)

else:
    st.warning("No expense data available")
    st.subheader("Expense by Category")

fig2, ax2 = plt.subplots()

ax2.bar(
    expense_data["category"],
    expense_data["total"]
)

ax2.set_xlabel("Category")
ax2.set_ylabel("Amount")
ax2.set_title("Expense by Category")

st.pyplot(fig2)
st.markdown("---")
st.markdown(
    "<center>💻 Developed by Darven NM | Personal Finance Tracker</center>",
    unsafe_allow_html=True
)