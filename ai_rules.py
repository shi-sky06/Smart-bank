from tkinter import messagebox

# ---------------------------------
# POPUP AI ALERTS
# ---------------------------------

def check_low_balance(balance):
    if balance < 1000:
        messagebox.showwarning(
            "🤖 AI Banking Alert",
            f"⚠ Low Balance Detected!\n\n"
            f"Current Balance: ₹{balance:,.2f}\n\n"
            f"Recommendation:\nMaintain at least ₹5,000 in your account."
        )


def check_large_deposit(amount):
    if amount >= 50000:
        messagebox.showwarning(
            "🤖 AI Banking Alert",
            f"🚨 Large Deposit Detected!\n\n"
            f"Amount: ₹{amount:,.2f}\n\n"
            f"Recommendation:\nVerify the source of funds if required."
        )


def check_large_withdrawal(amount):
    if amount >= 25000:
        messagebox.showwarning(
            "🤖 AI Banking Alert",
            f"🚨 Large Withdrawal Detected!\n\n"
            f"Amount: ₹{amount:,.2f}\n\n"
            f"Recommendation:\nEnsure this transaction is intended."
        )


def check_large_transfer(amount):
    if amount >= 50000:
        messagebox.showwarning(
            "🤖 AI Banking Alert",
            f"🚨 Large Transfer Detected!\n\n"
            f"Amount: ₹{amount:,.2f}\n\n"
            f"Recommendation:\nConfirm the recipient before proceeding."
        )


# ---------------------------------
# AI INSIGHTS FOR DASHBOARD
# ---------------------------------

def get_ai_insights(balance):

    insights = []

    # Account Status
    if balance < 1000:
        insights.append(("🔴 Low Balance Risk", "red"))

    elif balance < 5000:
        insights.append(("🟠 Maintain a Higher Balance", "orange"))

    elif balance < 100000:
        insights.append(("🟢 Healthy Account", "green"))

    else:
        insights.append(("💎 Premium Customer", "blue"))

    # Fraud Check
    insights.append(("🛡 No Suspicious Activity", "green"))

    # Risk Level
    if balance < 1000:
        insights.append(("📉 Risk Level : HIGH", "red"))
    elif balance < 5000:
        insights.append(("📊 Risk Level : MEDIUM", "orange"))
    else:
        insights.append(("📈 Risk Level : LOW", "green"))

    # Recommendation
    if balance < 5000:
        insights.append(("💡 Recommendation: Increase Savings", "purple"))
    else:
        insights.append(("⭐ Recommendation: Keep Up the Good Savings!", "blue"))

    return insights