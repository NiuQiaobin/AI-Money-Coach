import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from database import init_db, add_transaction, get_transactions, delete_transaction, get_budgets, set_budget, get_month_summary, seed_demo_data, clear_all_data, add_savings_goal, get_savings_goals, add_savings_contribution, get_savings_contributions, update_savings_goal, delete_savings_goal
from calendar import month_name

st.set_page_config(page_title="AI Money Coach", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

COLORS = ["#78977F", "#9A86C4", "#B8CDBB", "#C9B9E2", "#D9A98C", "#6F8FAF", "#D6B36A", "#A7A7A7"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root{--cream:#F8F8F3;--sage:#E8F0E8;--green:#294B3B;--lav:#EAE3F7;--purple:#9A86C4;--muted:#87918A;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp,[data-testid="stAppViewContainer"]{background:var(--cream);color:var(--green)}
.block-container{padding-top:2.2rem;padding-bottom:3rem;max-width:1250px}
section[data-testid="stSidebar"]{background:var(--sage);border-right:1px solid #DCE6DC}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],section[data-testid="stSidebar"] label{font-family:'Nunito',sans-serif!important;font-weight:900!important;color:var(--green)!important}
[data-testid="stHeader"]{background:var(--cream)}

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E3E9E1;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 4px 16px rgba(41,75,59,0.035);
    transition: all 0.2s ease;
}

[data-testid="stMetricLabel"] {
    color: #87918A;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
}

[data-testid="stMetricValue"] {
    font-family: 'DM Sans', sans-serif !important;
    color: #294B3B;
    font-size: 27px !important;
    font-weight: 700 !important;
}

/* Soft Sage & Lavender metric badges */
[data-testid="stMetricDelta"] {
    display: inline-flex;
    align-items: center;
    width: fit-content;
    padding: 4px 10px;
    border-radius: 20px;
    background: #E8F0E8 !important;
    color: #527B62 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
}

/* Positive change */
[data-testid="stMetricDelta"] svg {
    fill: currentColor;
}

/* Keep the badge typography elegant */
[data-testid="stMetricDelta"] p {
    color: inherit !important;
    font-size: 12px !important;
    font-weight: 700 !important;
}
/* Global progress bar - Sage Green */
[data-testid="stProgressBar"] > div {
    background-color: #E8F0E8 !important;
    border-radius: 20px !important;
}

[data-testid="stProgressBar"] > div > div,
[data-testid="stProgressBar"] div[style*="width"] {
    background-color: #78977F !important;
    border-radius: 20px !important;
}

div.stButton>button,div.stFormSubmitButton>button{background:var(--green);color:#fff;border:0;border-radius:12px;font-weight:700}
div.stButton>button:hover,div.stFormSubmitButton>button:hover{background:#3B6651;color:#fff}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{border-radius:10px}
.st-key-budget_checkin {
    background: transparent;
    border: 1px solid #D9DED7;
    border-radius: 18px;
    padding: 20px;
    min-height: 420px;
    height: auto;
    box-sizing: border-box;
}
.st-key-budget_checkin h3 {
    margin-top: 0;
}

.st-key-budget_checkin [data-testid="stCaptionContainer"] {
    margin-bottom: 16px;
}



/* Budget progress bar - lavender theme */
.st-key-budget_checkin [data-testid="stProgressBar"] {
    margin-bottom: 12px;
}

.st-key-budget_checkin [data-testid="stProgressBar"] > div {
    background: #D9CEED !important;
    border-radius: 20px !important;
    overflow: hidden !important;
}

/* Actual filled progress area */
.st-key-budget_checkin [data-testid="stProgressBar"] > div > div,
.st-key-budget_checkin [data-testid="stProgressBar"] div[style*="width"] {
    background: #9A86C4 !important;
    border-radius: 20px !important;
}


.card{background:#fff;border:1px solid #E9EDE7;border-radius:18px;padding:20px}
.small-muted{color:#87918A;font-size:13px}
</style>
""", unsafe_allow_html=True)

init_db()
CATEGORIES = ["Food & Dining", "Shopping", "Transport", "Bills", "Entertainment", "Health", "Education", "Housing", "Salary", "Freelance", "Investment", "Other"]
EXPENSE_CATS = CATEGORIES[:8] + ["Other"]
INCOME_CATS = ["Salary", "Freelance", "Investment", "Other income"]
MONEY = "SGD"

def money(v):
    return f"S${float(v):,.2f}"

def month_options():
    today = date.today()
    return [(f"{month_name[m]} {y}", f"{y}-{m:02d}") for y in range(today.year-2, today.year+1) for m in range(1,13)]

st.sidebar.title("💰 AI Money Coach")
st.sidebar.caption("YOUR MONEY, YOUR WAY")
st.sidebar.divider()
def go_to_budget():
    st.session_state["page"] = "Budget Planner"
page = st.sidebar.radio(
    "MENU",
    ["Dashboard", "Transactions", "Budget Planner", "Spending Analytics", "Settings"],
    key="page"
)
st.sidebar.divider()
st.sidebar.caption("Build better money habits 🌱")
st.sidebar.caption("All data is stored locally on this device.")

df = get_transactions()
today = date.today()
current_month = today.strftime("%Y-%m")

if not df.empty:
    df["date"] = df["date"].astype(str)
    first_month = pd.to_datetime(df["date"]).min().strftime("%Y-%m")

    available_months = [
        str(m)
        for m in pd.period_range(
            start=first_month,
            end=current_month,
            freq="M"
        )
    ]
else:
    available_months = [current_month]

if page == "Dashboard":
    st.markdown(
        "<div style='height: 15px;'></div>",
        unsafe_allow_html=True
    )
    selected_month = st.selectbox(
        "Select month to view",
        options=available_months,
        index=available_months.index(current_month),
        format_func=lambda m: f"{month_name[int(m[5:7])]} {m[:4]}"
    )
else:
    selected_month = current_month

month_key = selected_month

month_df = (
    df[df["date"].str.startswith(month_key)].copy()
    if not df.empty else df.copy()
)

income = month_df.loc[
    month_df["type"] == "Income", "amount"
].sum() if not month_df.empty else 0

expenses = month_df.loc[
    month_df["type"] == "Expense", "amount"
].sum() if not month_df.empty else 0

balance = income - expenses

previous_month_key = str(pd.Period(month_key, freq="M") - 1)

previous_month_df = (
    df[df["date"].str.startswith(previous_month_key)]
    if not df.empty else df
)

previous_income = (
    previous_month_df.loc[
        previous_month_df["type"] == "Income", "amount"
    ].sum()
    if not previous_month_df.empty else 0
)

previous_expenses = (
    previous_month_df.loc[
        previous_month_df["type"] == "Expense", "amount"
    ].sum()
    if not previous_month_df.empty else 0
)

previous_balance = previous_income - previous_expenses

def percentage_change(current, previous):
    if previous == 0:
        return "New" if current > 0 else "0.0%"
    change = (current - previous) / abs(previous) * 100
    return f"{change:+.1f}%"

balance_change = percentage_change(balance, previous_balance)
income_change = percentage_change(income, previous_income)
expenses_change = percentage_change(expenses, previous_expenses)


def chart_theme(fig, height=350):
    fig.update_layout(paper_bgcolor="#F8F8F3",plot_bgcolor="#F8F8F3",font=dict(family="DM Sans",color="#294B3B"),margin=dict(t=25,b=35,l=15,r=15),height=height)
    return fig


if page == "Dashboard":
    st.title("Your money, at a glance 👋")
    st.caption(
        f"Here's your financial snapshot for "
        f"{month_name[int(month_key[5:7])]} {month_key[:4]}."
    )

    a, b, c = st.columns(3)

    
    a.metric(
        "Net balance",
        money(balance),
        balance_change,
        delta_color="normal"
    )

    b.metric(
        "Income this month",
        money(income),
        income_change,
        delta_color="normal"
    )

    c.metric(
        "Expenses this month",
        money(expenses),
        expenses_change,
        delta_color="inverse"
    )


    st.write("")

    
    left, right = st.columns([1.25, 1], gap="large")

    # ==========================================
    # LEFT: SPENDING OVERVIEW + CATEGORY BREAKDOWN
    # ==========================================
    with left:
        with st.container(border=True):
            st.subheader("Spending by category")

            if month_df.empty or expenses == 0:
                st.info(
                    "No expenses recorded this month yet. "
                    "Add your first transaction in Transactions."
                )
            else:
                cats = (
                    month_df[month_df["type"] == "Expense"]
                    .groupby("category", as_index=False)["amount"]
                    .sum()
                    .sort_values("amount", ascending=False)
                )

                cats["percentage"] = (
                    cats["amount"] / cats["amount"].sum() * 100
                )

                fig = px.pie(
                    cats,
                    names="category",
                    values="amount",
                    hole=0.72,
                    color_discrete_sequence=COLORS
                )

                fig.update_traces(
                    textinfo="none",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Amount: S$%{value:,.2f}<br>"
                        "Share: %{percent}"
                        "<extra></extra>"
                    ),
                    marker=dict(
                        line=dict(color="#FFFFFF", width=3)
                    )
                )

                fig.update_layout(
                    showlegend=False,
                    margin=dict(t=5, b=5, l=5, r=5),
                    height=245,
                    annotations=[
                        dict(
                            text=(
                                f"<b>{money(expenses)}</b>"
                                "<br><span style='font-size:11px'>"
                                "TOTAL SPENT</span>"
                            ),
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                            font=dict(
                                size=19,
                                color="#294B3B",
                                family="DM Sans"
                            )
                        )
                    ]
                )

                st.plotly_chart(
                    chart_theme(fig, 245),
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.divider()
                st.markdown("**Category breakdown**")

                for _, row in cats.iterrows():
                    color_index = cats.index.get_loc(row.name)
                    color = COLORS[color_index % len(COLORS)]

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(
                            f'<span style="color:{color};'
                            f'font-size:17px">●</span> '
                            f'**{row["category"]}**',
                            unsafe_allow_html=True
                        )

                        st.caption(
                            f'{row["percentage"]:.1f}% of spending'
                        )

                    with col2:
                        st.markdown(
                            f'<div style="text-align:right;'
                            f'font-weight:700;color:#294B3B;'
                            f'padding-top:4px">'
                            f'{money(row["amount"])}</div>',
                            unsafe_allow_html=True
                        )

    # ==========================================
    # RIGHT: COMPACT BUDGET & SAVINGS OVERVIEW
    # ==========================================
    with right:
        with st.container(border=True):
            st.subheader("Your financial progress")
            st.caption("A little progress, a little more control ♡")
            st.markdown("""
            <style>
            /* Spending Budget button */
            .st-key-budget_nav button {
                width: 100% !important;
                background: #C1D3C3 !important;
                background-color: #C1D3C3 !important;
                color: #294B3B !important;
                border: none !important;
                border-radius: 10px !important;
                box-shadow: none !important;
            }

            .st-key-budget_nav button p {
                color: #294B3B !important;
                font-weight: 600 !important;
            }

            .st-key-budget_nav button:hover {
                background: #AEC5B1 !important;
                background-color: #AEC5B1 !important;
                color: #294B3B !important;
            }

            /* Savings Goals button */
            .st-key-savings_nav button {
                width: 100% !important;
                background: #CBBCE3 !important;
                background-color: #CBBCE3 !important;
                color: #493D61 !important;
                border: none !important;
                border-radius: 10px !important;
                box-shadow: none !important;
            }

            .st-key-savings_nav button p {
                color: #493D61 !important;
                font-weight: 600 !important;
            }

            .st-key-savings_nav button:hover {
                background: #BBA9D9 !important;
                background-color: #BBA9D9 !important;
                color: #493D61 !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # ----------------------------------
            # SPENDING BUDGET - SAGE GREEN
            # ----------------------------------
            budgets = get_budgets()

            total_budget = sum(budgets.values()) if budgets else 0

            total_budget_spent = sum(
                month_df[
                    (month_df["type"] == "Expense") &
                    (month_df["category"] == cat)
                ]["amount"].sum()
                for cat in budgets
            ) if budgets and not month_df.empty else 0

            remaining = total_budget - total_budget_spent

            budget_ratio = (
                total_budget_spent / total_budget
                if total_budget > 0 else 0
            )

            budget_progress = min(max(budget_ratio, 0), 1)
            budget_count = len(budgets) if budgets else 0

            st.markdown(
                f'<div style="background-color:#E8F0E8;padding:18px;border-radius:14px;border-left:5px solid #78977F;min-height:205px;margin-top:12px;">'
                f'<div style="color:#294B3B;font-size:17px;font-weight:700;">Spending Budget</div>'
                f'<div style="color:#294B3B;font-size:29px;font-weight:800;margin-top:15px;">${remaining:,.2f}</div>'
                f'<div style="color:#294B3B;font-size:13px;margin-top:2px;">Remaining this month</div>'
                f'<div style="background-color:#D5E1D5;height:9px;border-radius:10px;margin-top:16px;">'
                f'<div style="background-color:#78977F;width:{budget_progress * 100:.1f}%;height:9px;border-radius:10px;"></div>'
                f'</div>'
                f'<div style="color:#294B3B;font-size:12px;margin-top:8px;">{budget_ratio:.0%} of total budget used</div>'
                f'<div style="color:#294B3B;font-size:12px;margin-top:13px;font-weight:600;">{budget_count} budgets</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            with st.container(key="budget_nav"):
                st.button(
                    "View all in Budget Planner →",
                    key="go_to_budget_1",
                    on_click=go_to_budget,
                    use_container_width=True
                )
            # ----------------------------------
            # SAVINGS GOALS - LAVENDER
            # ----------------------------------
            goals = get_savings_goals()

            if not goals.empty:
                total_saved = goals["saved_amount"].fillna(0).sum()
                total_savings_target = goals["target_amount"].sum()
                goal_count = len(goals)
            else:
                total_saved = 0
                total_savings_target = 0
                goal_count = 0

            savings_ratio = (
                total_saved / total_savings_target
                if total_savings_target > 0 else 0
            )

            savings_progress = min(max(savings_ratio, 0), 1)

            st.markdown(
                f'<div style="background-color:#EAE3F7;padding:18px;border-radius:14px;border-left:5px solid #9A86C4;min-height:205px;margin-top:16px;">'
                f'<div style="color:#493D61;font-size:17px;font-weight:700;">Savings Goals</div>'
                f'<div style="color:#493D61;font-size:29px;font-weight:800;margin-top:15px;">${total_saved:,.2f}</div>'
                f'<div style="color:#493D61;font-size:13px;margin-top:2px;">Total saved</div>'
                f'<div style="background-color:#DCD2ED;height:9px;border-radius:10px;margin-top:16px;">'
                f'<div style="background-color:#9A86C4;width:{savings_progress * 100:.1f}%;height:9px;border-radius:10px;"></div>'
                f'</div>'
                f'<div style="color:#493D61;font-size:12px;margin-top:8px;">{savings_ratio:.0%} of total savings target</div>'
                f'<div style="color:#493D61;font-size:12px;margin-top:13px;font-weight:600;">{goal_count} goals</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            with st.container(key="savings_nav"):
                st.button(
                    "View all in Budget Planner →",
                    key="go_to_budget_2",
                    on_click=go_to_budget,
                    use_container_width=True
                )


    
    with st.container(border=True):
        st.subheader("Recent Transactions")
        st.caption("Your latest money activity ✨")

        if df.empty:
            st.info(
                "Your recent activity will appear here "
                "after you add transactions."
            )
        else:
            view = df.head(6).copy()

            for _, row in view.iterrows():
                with st.container():
                    details, amount_col = st.columns(
                        [0.7, 0.3],
                        vertical_alignment="center"
                    )

                    with details:
                        st.markdown(f"**{row['category']}**")
                        st.caption(
                            f"{row['date']} · {row['type']}"
                        )

                        if pd.notna(row["note"]) and str(row["note"]).strip():
                            st.caption(str(row["note"]))

                    with amount_col:
                        if row["type"] == "Income":
                            amount_color = "#2E7D5B"
                            sign = "+"
                        else:
                            amount_color = "#C46B70"
                            sign = "−"

                        st.markdown(
                            f"<div style='text-align:right;"
                            f"font-size:16px;font-weight:800;"
                            f"color:{amount_color}'>"
                            f"{sign}{money(row['amount'])}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            """
                            <div style="
                                border-bottom: 1px solid #E9EDE7;
                                padding-bottom: 8px;
                                margin-bottom: 8px;
                            "></div>
                            """,
                            unsafe_allow_html=True
                        )



elif page == "Transactions":
    st.title("Transactions ✨")
    st.caption("Record income and expenses in one simple place.")
    with st.container(border=True):
        st.subheader("Add a transaction")
        with st.form("transaction_form",clear_on_submit=True):
            col1,col2,col3 = st.columns(3)
            tx_type = col1.selectbox("Type",["Expense","Income"])
            tx_date = col2.date_input("Date",value=date.today())
            tx_amount = col3.number_input("Amount (SGD)",min_value=0.01,value=10.00,step=1.00)
            category = st.selectbox("Category", EXPENSE_CATS if tx_type=="Expense" else INCOME_CATS)
            note = st.text_input("Note (optional)",placeholder="e.g. Lunch with friends")
            submitted = st.form_submit_button("Save transaction",use_container_width=True)
            if submitted:
                add_transaction(tx_date.isoformat(),tx_type,category,float(tx_amount),note.strip())
                st.success("Transaction saved!")
                st.rerun()
    st.subheader("All transactions")
    if df.empty:
        st.info("No transactions yet. Add one above to get started.")
    else:
        f1,f2 = st.columns(2)
        type_filter = f1.selectbox("Filter by type",["All","Expense","Income"])
        category_filter = f2.selectbox("Filter by category",["All"]+sorted(df["category"].unique().tolist()))
        shown = df.copy()
        if type_filter!="All": shown=shown[shown["type"]==type_filter]
        if category_filter!="All": shown=shown[shown["category"]==category_filter]
        st.dataframe(shown[["id","date","type","category","note","amount"]],hide_index=True,use_container_width=True)
        with st.expander("Delete a transaction"):
            ids = shown["id"].tolist()
            if ids:
                selected = st.selectbox("Select transaction ID",ids)
                if st.button("Delete selected transaction"):
                    delete_transaction(int(selected)); st.success("Deleted."); st.rerun()
        st.download_button("Download CSV",df.to_csv(index=False).encode("utf-8"),"money-coach-transactions.csv","text/csv")




elif page == "Budget Planner":
    st.title("Budget & Savings Planner")
    st.caption("Plan your spending today and save for tomorrow.")
    # ==================================
    # BUDGET PLANNER - SAGE & LAVENDER THEME
    # ==================================
    st.markdown("""
    <style>
    /* Page text */
    [data-testid="stAppViewContainer"] {
        background-color: #F8F8F3;
    }

    /* Text inputs, number inputs and select boxes */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #E8F0E8 !important;
        border: 1px solid #D5E1D5 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="select"] input {
        color: #294B3B !important;
    }

    div[data-baseweb="select"] span {
        color: #294B3B !important;
    }

    /* Date input */
    div[data-testid="stDateInput"] input {
        background-color: #E8F0E8 !important;
        color: #294B3B !important;
        border: 1px solid #D5E1D5 !important;
        border-radius: 10px !important;
    }

    /* Input labels */
    [data-testid="stWidgetLabel"] p {
        color: #294B3B !important;
        font-weight: 600 !important;
    }

    /* Form buttons */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #294B3B !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Same track background for all progress bars */
    [data-testid="stProgress"] > div {
        background-color: #E8F0E8 !important;
        border-radius: 20px !important;
    }

    /* Expense progress fill - Sage Green */
    [class*="st-key-expense_progress_"] [data-testid="stProgress"] div[style*="width"] {
        background-color: #78977F !important;
        background: #78977F !important;
    }

    /* Savings progress fill - Lavender */
    [class*="st-key-savings_progress_"] [data-testid="stProgress"] div[style*="width"] {
        background-color: #9A86C4 !important;
        background: #9A86C4 !important;
    }

    /* Rounded progress bars */
    [data-testid="stProgress"] > div,
    [data-testid="stProgress"] div[style*="width"] {
        border-radius: 20px !important;
    }
    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #F8F8F3 !important;
        border: 1px solid #D5E1D5 !important;
        border-radius: 12px !important;
    }

    /* Main headings */
    h1, h2, h3 {
        color: #1F352B !important;
        font-weight: 750 !important;
    }

    /* Section headings */
    [data-testid="stSubheader"] {
        color: #1F352B !important;
    }

    [data-testid="stSubheader"] p {
        color: #1F352B !important;
        font-weight: 700 !important;
    }

    </style>
    """, unsafe_allow_html=True)
    # ==================================
    # Expense Budgets
    # ==================================
    st.subheader("Expense Budgets")
    st.caption("Manage spending limits")

    with st.form("budget_form"):
        cat = st.selectbox(
            "Expense category",
            EXPENSE_CATS
        )

        limit = st.number_input(
            "Monthly budget (SGD)",
            min_value=1.0,
            value=300.0,
            step=10.0
        )

        save = st.form_submit_button("Save budget")

        if save:
            set_budget(cat, float(limit))
            st.success(f"Budget saved for {cat}.")
            st.rerun()

    budgets = get_budgets()

    if budgets:
        st.subheader("Your monthly budgets")

        for cat, lim in budgets.items():
            spent = (
                month_df[
                    (month_df["type"] == "Expense") &
                    (month_df["category"] == cat)
                ]["amount"].sum()
                if not month_df.empty else 0
            )

            ratio = spent / lim if lim else 0

            st.write(
                f"**{cat}** — "
                f"{money(spent)} of {money(lim)}"
            )

            with st.container(key=f"expense_progress_{cat}"):
                st.progress(min(float(ratio), 1.0))

            if ratio > 1:
                st.warning(
                    f"{cat} is over budget by {money(spent-lim)}."
                )
            elif ratio >= 0.8:
                st.info(
                    f"{cat} is getting close to its budget."
                )
    else:
        st.info("No expense budgets yet. Add your first budget above!")

    # ==================================
    # Savings Goals
    # ==================================
    st.divider()

    st.subheader("Savings Goals")
    st.caption("Plan your future")

    with st.form("savings_goal_form"):
        goal_name = st.text_input(
            "Goal name",
            placeholder="e.g. Japan Trip"
        )

        goal_type = st.selectbox(
            "Savings goal type",
            [
                "Travel",
                "Emergency Fund",
                "Big Purchase",
                "Other"
            ]
        )

        target_amount = st.number_input(
            "Target amount (SGD)",
            min_value=1.0,
            value=1000.0,
            step=100.0
        )

        target_date = st.date_input("Target date")

        save_goal = st.form_submit_button(
            "Create savings goal"
        )

        if save_goal:
            if not goal_name.strip():
                st.error("Please enter a goal name.")
            else:
                add_savings_goal(
                    goal_name.strip(),
                    goal_type,
                    float(target_amount),
                    str(target_date)
                )

                st.success(
                    f"Savings goal '{goal_name}' created!"
                )
                st.rerun()

    # Display existing savings goals
    goals = get_savings_goals()

    
    if not goals.empty:
        st.subheader("Your savings goals")

        for _, goal in goals.iterrows():
            saved = float(goal.get("saved_amount", 0) or 0)
            target = float(goal["target_amount"])
            progress = saved / target if target > 0 else 0

            st.write(
                f"**{goal['name']}** — "
                f"{money(saved)} / {money(target)}"
            )

            with st.container(key=f"savings_progress_{goal['id']}"):
                st.progress(min(float(progress), 1.0))

            st.caption(
                f"{progress:.0%} completed · {goal['goal_type']}"
            )

            with st.expander(f"Add contribution to {goal['name']}"):
                with st.form(f"contribution_form_{goal['id']}"):
                    contribution_amount = st.number_input(
                        "Amount (SGD)",
                        min_value=0.01,
                        value=100.0,
                        step=10.0,
                        key=f"amount_{goal['id']}"
                    )

                    contribution_date = st.date_input(
                        "Contribution date",
                        key=f"date_{goal['id']}"
                    )

                    contribution_note = st.text_input(
                        "Note (optional)",
                        placeholder="e.g. Monthly savings",
                        key=f"note_{goal['id']}"
                    )

                    save_contribution = st.form_submit_button(
                        "Save contribution"
                    )

                    if save_contribution:
                        add_savings_contribution(
                            int(goal["id"]),
                            float(contribution_amount),
                            str(contribution_date),
                            contribution_note.strip()
                        )

                        st.success("Contribution saved!")
                        st.rerun()
                                    # Savings contribution history
            with st.expander(f"Savings history - {goal['name']}"):
                history = get_savings_contributions(int(goal["id"]))

                if history.empty:
                    st.info("No contributions recorded yet.")
                else:
                    for _, record in history.iterrows():
                        contribution_date = record["contribution_date"]
                        amount = float(record["amount"])
                        note = record.get("note", "")

                        st.write(
                            f"**{contribution_date}** — {money(amount)}"
                        )

                        if note:
                            st.caption(note)
                            
            # Edit and delete savings goal
            with st.expander(f"Edit goal - {goal['name']}"):
                with st.form(f"edit_goal_form_{goal['id']}"):
                    new_name = st.text_input(
                        "Goal name",
                        value=goal["name"],
                        key=f"edit_name_{goal['id']}"
                    )

                    new_type = st.selectbox(
                        "Goal type",
                        ["Travel", "Emergency Fund", "Big Purchase", "Other"],
                        index=(
                            ["Travel", "Emergency Fund", "Big Purchase", "Other"].index(goal["goal_type"])
                            if goal["goal_type"] in ["Travel", "Emergency Fund", "Big Purchase", "Other"]
                            else 0
                        ),
                        key=f"edit_type_{goal['id']}"
                    )

                    new_target = st.number_input(
                        "Target amount (SGD)",
                        min_value=1.0,
                        value=float(goal["target_amount"]),
                        step=100.0,
                        key=f"edit_target_{goal['id']}"
                    )

                    new_date = st.text_input(
                        "Target date (YYYY-MM-DD)",
                        value=str(goal.get("target_date", "") or ""),
                        key=f"edit_date_{goal['id']}"
                    )

                    update_button = st.form_submit_button("Save changes")

                    if update_button:
                        if not new_name.strip():
                            st.error("Please enter a goal name.")
                        else:
                            update_savings_goal(
                                int(goal["id"]),
                                new_name.strip(),
                                new_type,
                                float(new_target),
                                new_date.strip()
                            )
                            st.success("Savings goal updated!")
                            st.rerun()

            if st.button(
                f"Delete {goal['name']}",
                key=f"delete_goal_{goal['id']}"
            ):
                delete_savings_goal(int(goal["id"]))
                st.success("Savings goal deleted.")
                st.rerun()


    else:
        st.info(
            "No savings goals yet. Create your first goal above!"
        )



elif page == "Spending Analytics":
    st.title("Spending Analytics 📊")
    st.caption("Explore your money patterns over time.")

    if df.empty:
        st.info("Add some transactions first. Your charts will appear here.")

    else:
        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data["month"] = data["date"].dt.strftime("%Y-%m")

        expenses_df = data[data["type"] == "Expense"].copy()

        if not expenses_df.empty:

            # Month selector
            available_months = sorted(
                expenses_df["month"].unique(),
                reverse=True
            )

            month_labels = {
                month: pd.to_datetime(month + "-01").strftime("%B %Y")
                for month in available_months
            }

            selected_month = st.selectbox(
                "Select month",
                available_months,
                format_func=lambda x: month_labels[x]
            )

            # Daily expenses for the selected month
            selected_df = expenses_df[
                expenses_df["month"] == selected_month
            ].copy()

            daily = (
                selected_df
                .groupby(selected_df["date"].dt.day)["amount"]
                .sum()
                .reset_index()
            )

            daily.columns = ["Day", "Expenses"]

            # Include days with no spending
            days_in_month = pd.Period(selected_month).days_in_month

            daily = (
                daily.set_index("Day")
                .reindex(range(1, days_in_month + 1), fill_value=0)
                .rename_axis("Day")
                .reset_index()
            )

            st.subheader(
                f"Daily expenses — {month_labels[selected_month]}"
            )

            fig = px.bar(
                daily,
                x="Day",
                y="Expenses",
                labels={
                    "Day": "Day of month",
                    "Expenses": "Expenses (SGD)"
                },
                color_discrete_sequence=["#9A86C4"]
            )

            fig.update_traces(
                width=0.7,
                marker_line_width=0,
                hovertemplate="Day %{x}<br>Expenses: S$%{y:,.2f}<extra></extra>"
            )

            fig.update_xaxes(
                tickmode="linear",
                tick0=1,
                dtick=2
            )

            fig.update_layout(
                bargap=0.18
            )

            st.plotly_chart(
                chart_theme(fig, 380),
                use_container_width=True
            )

            # Spending by selected month and category
            selected_df = expenses_df[
                expenses_df["month"] == selected_month
            ]

            cat = (
                selected_df
                .groupby("category", as_index=False)["amount"]
                .sum()
                .sort_values("amount", ascending=False)
            )

            st.subheader(
                f"Spending by category — {month_labels[selected_month]}"
            )

            if cat.empty:
                st.info("No expenses recorded for this month.")
            else:
                fig2 = go.Figure(
                    go.Bar(
                        x=cat["amount"],
                        y=cat["category"],
                        orientation="h",
                        width=0.25,
                        marker=dict(
                            color="#78977F",
                            cornerradius=20
                        ),
                        hovertemplate="%{y}<br>Total: S$%{x:,.2f}<extra></extra>"
                    )
                )

                fig2.update_layout(
                    height=max(180, len(cat) * 30 + 60),
                    xaxis_title="Total (SGD)",
                    yaxis_title="",
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(t=15, b=35, l=10, r=15)
                )

                st.plotly_chart(
                    chart_theme(fig2),
                    use_container_width=True
                )

        else:
            st.info("No expense transactions yet.")

else:
    st.title("Settings")
    st.caption("Manage your local demo data.")
    st.warning("Your transactions are stored in a local SQLite database on this computer. They are not synced to the cloud.")
    if st.button("Load sample data",help="Adds clearly labelled example transactions if your database is empty."):
        seed_demo_data(); st.success("Sample data loaded."); st.rerun()
    if st.button("Delete ALL transactions and budgets"):
        st.session_state.confirm_clear=True
    if st.session_state.get("confirm_clear"):
        st.error("This permanently deletes all local transactions and budgets.")
        if st.button("Yes, permanently delete everything"):
            clear_all_data(); st.session_state.confirm_clear=False; st.success("Local data cleared."); st.rerun()

st.sidebar.divider()
st.sidebar.caption("For education and personal tracking only — not financial advice.")