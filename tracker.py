import os
from datetime import date

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
    print("\nTotal per category:")
    print(df.groupby("category")["amount"].sum().sort_values(ascending=False))
    print("\nTotal per month:")
    print(df.groupby("month")["amount"].sum())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    df.groupby("category")["amount"].sum().plot.pie(ax=ax1, autopct="%1.0f%%")
    ax1.set_ylabel("")
    ax1.set_title("Spending by category")
    df.groupby("month")["amount"].sum().plot.bar(ax=ax2)
    ax2.set_title("Spending per month")
    ax2.set_xlabel("")
    plt.tight_layout()
    plt.savefig("report.png")
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
