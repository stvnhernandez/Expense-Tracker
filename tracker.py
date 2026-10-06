import os
from datetime import date

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

FILE = "expenses.csv"
COLUMNS = ["date", "category", "amount", "note"]


def load():
    if os.path.exists(FILE):
        return pd.read_csv(FILE, parse_dates=["date"])
    return pd.DataFrame(columns=COLUMNS)


def add_expense():
    category = input("Category (food, transport, school...): ").strip().lower()
    amount = float(input("Amount: "))
    note = input("Note (optional): ").strip()
    row = pd.DataFrame([[date.today(), category, amount, note]], columns=COLUMNS)
    df = pd.concat([load(), row], ignore_index=True)
    df.to_csv(FILE, index=False)
    print("Saved.")


def report():
    df = load()
    if df.empty:
        print("No expenses yet.")
        return

    df["month"] = df["date"].dt.to_period("M").astype(str)
    by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    by_month = df.groupby("month")["amount"].sum()
    by_day = df.groupby(df["date"].dt.date)["amount"].sum()

    print("\nTotal per category:")
    print(by_cat)
    print("\nTotal per month:")
    print(by_month)

    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2", "#9D755D"]
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(13, 8), layout="constrained")
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])

    # 1) Donut: spending by category
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.pie(
        by_cat,
        labels=by_cat.index,
        colors=colors[: len(by_cat)],
        autopct="%1.0f%%",
        pctdistance=0.8,
        startangle=90,
        wedgeprops={"width": 0.4, "edgecolor": "white"},
        textprops={"fontsize": 10},
    )
    ax1.set_title("Spending by category", fontsize=13, fontweight="bold")

    # 2) Bar: spending per month
    ax2 = fig.add_subplot(gs[0, 1])
    bars = ax2.bar(by_month.index, by_month.values, color="#4C78A8", width=0.5)
    ax2.bar_label(bars, fmt="%.0f", padding=3, fontsize=10)
    ax2.set_title("Spending per month", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Amount")
    ax2.margins(y=0.15)
    ax2.spines[["top", "right"]].set_visible(False)

    # 3) Line: daily spending
    ax3 = fig.add_subplot(gs[1, :])
    ax3.plot(list(by_day.index), by_day.values, marker="o", color="#E45756", linewidth=2)
    ax3.fill_between(list(by_day.index), by_day.values, alpha=0.15, color="#E45756")
    ax3.set_title("Daily spending", fontsize=13, fontweight="bold")
    ax3.set_ylabel("Amount")
    ax3.grid(axis="y", alpha=0.3)
    ax3.spines[["top", "right"]].set_visible(False)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax3.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=8))
    for label in ax3.get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")

    fig.suptitle(
        f"Expense Report  |  Total: {df['amount'].sum():,.2f}  |  {len(df)} entries",
        fontsize=16,
        fontweight="bold",
    )
    plt.savefig("report.png", dpi=200)
    print("\nChart saved as report.png")
    plt.show()


def main():
    while True:
        print("\n1) Add expense  2) Report  3) Quit")
        choice = input("Choose: ").strip()
        if choice == "1":
            add_expense()
        elif choice == "2":
            report()
        elif choice == "3":
            break


if __name__ == "__main__":
    main()
