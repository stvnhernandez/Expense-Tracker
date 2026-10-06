#!/usr/bin/env python3
"""Expense Tracker: a command-line tracker with monthly budgets.

Examples:
  python tracker.py add 12.50 Food "Lunch"
  python tracker.py list --month 2026-10
  python tracker.py budget set 1900
  python tracker.py budget set 420 --category Food
  python tracker.py report
  python tracker.py chart          (needs: pip install matplotlib)
  python tracker.py export expenses.csv
  python tracker.py sample
"""
import argparse
import calendar
import csv
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).with_name("expenses.json")
CATEGORIES = ["Housing", "Food", "Transport", "Utilities", "Health", "Leisure", "Other"]


def load():
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {"expenses": [], "budget": {"total": 0, "categories": {}}}


def save(db):
    DATA.write_text(json.dumps(db, indent=2))


def month_of(args):
    return getattr(args, "month", None) or date.today().strftime("%Y-%m")


def in_month(db, ym):
    return [e for e in db["expenses"] if e["date"].startswith(ym)]


def bar(ratio, width=24):
    filled = round(min(ratio, 1) * width)
    return "#" * filled + "-" * (width - filled)


def cmd_add(args):
    if args.amount <= 0:
        raise SystemExit("Amount must be greater than 0.")
    cat = next((c for c in CATEGORIES if c.lower() == args.category.lower()), None)
    if not cat:
        raise SystemExit("Category must be one of: " + ", ".join(CATEGORIES))
    db = load()
    db["expenses"].append({
        "id": max([e["id"] for e in db["expenses"]], default=0) + 1,
        "date": args.date or date.today().isoformat(),
        "category": cat,
        "description": args.description or "",
        "amount": round(args.amount, 2),
    })
    save(db)
    print(f"Added {args.amount:.2f} to {cat}.")


def cmd_list(args):
    db = load()
    rows = sorted(in_month(db, month_of(args)), key=lambda e: e["date"])
    if not rows:
        print("No expenses for this month.")
        return
    for e in rows:
        print(f"{e['id']:>4}  {e['date']}  {e['category']:<10} {e['amount']:>10.2f}  {e['description']}")


def cmd_delete(args):
    db = load()
    before = len(db["expenses"])
    db["expenses"] = [e for e in db["expenses"] if e["id"] != args.id]
    save(db)
    print("Deleted." if len(db["expenses"]) < before else "No expense with that id.")


def cmd_budget(args):
    db = load()
    if args.action == "set":
        if args.category:
            cat = next((c for c in CATEGORIES if c.lower() == args.category.lower()), None)
            if not cat:
                raise SystemExit("Category must be one of: " + ", ".join(CATEGORIES))
            db["budget"]["categories"][cat] = args.amount
        else:
            db["budget"]["total"] = args.amount
        save(db)
    b = db["budget"]
    print(f"Monthly budget: {b['total']:.2f}")
    for c, v in b["categories"].items():
        print(f"  {c:<10} {v:.2f}")


def cmd_report(args):
    db = load()
    ym = month_of(args)
    rows = in_month(db, ym)
    year, month = map(int, ym.split("-"))
    days = calendar.monthrange(year, month)[1]
    is_current = ym == date.today().strftime("%Y-%m")
    elapsed = date.today().day if is_current else days
    total = sum(e["amount"] for e in rows)
    budget = db["budget"]["total"]

    print(f"\n{calendar.month_name[month]} {year}")
    print("-" * 52)
    print(f"Spent       {total:>12.2f}")
    if budget:
        left = budget - total
        print(f"Budget      {budget:>12.2f}")
        print(f"Remaining   {left:>12.2f}")
        print(f"Used        [{bar(total / budget)}] {total / budget:.0%}")
        if rows:
            projected = total / elapsed * days
            print(f"Projected   {projected:>12.2f}" + ("  (over budget)" if projected > budget else ""))
    else:
        print("No budget set. Use: python tracker.py budget set 1900")

    print("\nBy category")
    by = {c: 0.0 for c in CATEGORIES}
    for e in rows:
        by[e["category"]] = by.get(e["category"], 0) + e["amount"]
    biggest = max(by.values()) or 1
    for c, v in by.items():
        cb = db["budget"]["categories"].get(c, 0)
        ratio = v / cb if cb else v / biggest
        extra = f" / {cb:.2f}" if cb else ""
        flag = "  over" if cb and v > cb else ""
        print(f"  {c:<10} [{bar(ratio, 16)}] {v:>9.2f}{extra}{flag}")
    print()


def cmd_chart(args):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit("Charts need matplotlib: pip install matplotlib")
    db = load()
    ym = month_of(args)
    rows = in_month(db, ym)
    year, month = map(int, ym.split("-"))
    days = calendar.monthrange(year, month)[1]
    daily = [0.0] * days
    for e in rows:
        daily[int(e["date"][8:]) - 1] += e["amount"]
    by = {c: 0.0 for c in CATEGORIES}
    for e in rows:
        by[e["category"]] += e["amount"]

    ink, slate, teal, red = "#13222D", "#5B7A99", "#0E6B62", "#B0413A"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1, 1.5]})
    names = list(by)[::-1]
    cb = db["budget"]["categories"]
    a1.barh(names, [by[n] for n in names], color=[red if cb.get(n) and by[n] > cb[n] else slate for n in names])
    for n in names:
        if cb.get(n):
            a1.plot([cb[n]] * 2, [names.index(n) - .4, names.index(n) + .4], color=teal, lw=2)
    a1.set_title("By category (green tick = budget)", loc="left", color=ink)
    limit = db["budget"]["total"] / days if db["budget"]["total"] else 0
    a2.bar(range(1, days + 1), daily, color=[red if limit and v > limit else slate for v in daily])
    if limit:
        a2.axhline(limit, color=teal, ls="--", lw=1)
    a2.set_title("Daily spending", loc="left", color=ink)
    for ax in (a1, a2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = Path(__file__).with_name("report.png")
    fig.savefig(out, dpi=160)
    print(f"Saved {out.name}")


def cmd_export(args):
    db = load()
    with open(args.file, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Category", "Description", "Amount"])
        for e in sorted(db["expenses"], key=lambda e: e["date"]):
            w.writerow([e["date"], e["category"], e["description"], e["amount"]])
    print(f"Exported to {args.file}")


def cmd_sample(args):
    ym = month_of(args)
    seed = [(1, "Housing", "Rent", 1100), (3, "Food", "Groceries", 86), (4, "Transport", "Fuel", 42),
            (5, "Utilities", "Electric and water", 94), (8, "Leisure", "Concert tickets", 75),
            (11, "Health", "Pharmacy", 27), (14, "Food", "Dinner out", 58), (18, "Food", "Groceries", 92),
            (21, "Other", "Gift", 50), (25, "Health", "Gym membership", 35)]
    db = load()
    start = max([e["id"] for e in db["expenses"]], default=0)
    for i, (d, c, desc, a) in enumerate(seed, 1):
        db["expenses"].append({"id": start + i, "date": f"{ym}-{d:02d}", "category": c,
                               "description": desc, "amount": a})
    db["budget"] = {"total": 1900, "categories": {"Housing": 1100, "Food": 420, "Transport": 140,
                                                  "Utilities": 150, "Health": 70, "Leisure": 110, "Other": 60}}
    save(db)
    print("Sample data added.")


def main():
    p = argparse.ArgumentParser(description="Expense tracker with monthly budgets")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add an expense")
    a.add_argument("amount", type=float)
    a.add_argument("category")
    a.add_argument("description", nargs="?", default="")
    a.add_argument("--date", help="YYYY-MM-DD (default: today)")
    a.set_defaults(fn=cmd_add)

    for name, fn, h in [("list", cmd_list, "list expenses"), ("report", cmd_report, "monthly budget report"),
                        ("chart", cmd_chart, "save report.png"), ("sample", cmd_sample, "add sample data")]:
        s = sub.add_parser(name, help=h)
        s.add_argument("--month", help="YYYY-MM (default: this month)")
        s.set_defaults(fn=fn)

    d = sub.add_parser("delete", help="delete an expense by id")
    d.add_argument("id", type=int)
    d.set_defaults(fn=cmd_delete)

    b = sub.add_parser("budget", help="show or set monthly budgets")
    b.add_argument("action", choices=["show", "set"], nargs="?", default="show")
    b.add_argument("amount", type=float, nargs="?", default=0)
    b.add_argument("--category")
    b.set_defaults(fn=cmd_budget)

    e = sub.add_parser("export", help="export all expenses to CSV")
    e.add_argument("file")
    e.set_defaults(fn=cmd_export)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
