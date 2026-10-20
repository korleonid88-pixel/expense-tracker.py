# expense-tracker.py
# Запуск: python expense-tracker.py <команда> [аргументы]

import argparse
import csv
import json
import os
import sys
from datetime import datetime

DATA_FILE = "expenses.json"
CSV_FILE = "expenses.csv"

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

CATEGORIES = ["food", "transport", "entertainment", "bills", "other"]  # доп. фича


# ---------- Работа с файлом ----------

def load_expenses():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print("Error: could not read expenses file.")
        sys.exit(1)


def save_expenses(expenses):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2, ensure_ascii=False)


def next_id(expenses):
    return max((e["id"] for e in expenses), default=0) + 1


# ---------- Проверки ----------

def parse_amount(value):
    try:
        amount = float(value)
    except ValueError:
        sys.exit("Error: amount must be a number.")
    if amount <= 0:
        sys.exit("Error: amount must be a positive number.")
    return round(amount, 2)


def find_expense(expenses, expense_id):
    for e in expenses:
        if e["id"] == expense_id:
            return e
    sys.exit(f"Error: expense with ID {expense_id} not found.")


# ---------- Команды ----------

def cmd_add(args):
    expenses = load_expenses()
    category = args.category if args.category in CATEGORIES else "other"
    expense = {
        "id": next_id(expenses),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": args.description,
        "amount": parse_amount(args.amount),
        "category": category,          # доп. фича
    }
    expenses.append(expense)
    save_expenses(expenses)
    print(f"Expense added successfully (ID: {expense['id']})")


def cmd_update(args):
    expenses = load_expenses()
    expense = find_expense(expenses, args.id)
    if args.description:
        expense["description"] = args.description
    if args.amount is not None:
        expense["amount"] = parse_amount(args.amount)
    if args.category:
        if args.category not in CATEGORIES:
            sys.exit(f"Error: category must be one of: {', '.join(CATEGORIES)}")
        expense["category"] = args.category
    save_expenses(expenses)
    print("Expense updated successfully")


def cmd_delete(args):
    expenses = load_expenses()
    find_expense(expenses, args.id)  # проверка, что ID существует
    expenses = [e for e in expenses if e["id"] != args.id]
    save_expenses(expenses)
    print("Expense deleted successfully")


def cmd_list(args):
    expenses = load_expenses()
    if args.category:               # доп. фича: фильтр по категории
        expenses = [e for e in expenses if e.get("category") == args.category]
    if not expenses:
        print("No expenses found.")
        return
    print(f"{'ID':<4}{'Date':<12}{'Description':<25}{'Category':<15}{'Amount'}")
    for e in expenses:
        print(f"{e['id']:<4}{e['date']:<12}{e['description']:<25}"
              f"{e.get('category', '-'):<15}${e['amount']}")


def cmd_summary(args):
    expenses = load_expenses()

    if args.month:
        if not 1 <= args.month <= 12:
            sys.exit("Error: month must be between 1 and 12.")
        year = datetime.now().year
        filtered = [e for e in expenses
                    if e["date"].startswith(f"{year}-{args.month:02d}")]
        total = sum(e["amount"] for e in filtered)
        print(f"Total expenses for {MONTH_NAMES[args.month]}: ${total}")
        return

    total = sum(e["amount"] for e in expenses)
    print(f"Total expenses: ${total}")
    if args.month_budget:                            # доп. фича: бюджет
        year = datetime.now().year
        current = datetime.now().month
        month_total = sum(e["amount"] for e in expenses
                          if e["date"].startswith(f"{year}-{current:02d}"))
        if month_total > args.month_budget:
            print(f"Warning: you exceeded your monthly budget "
                  f"(${month_total} of ${args.month_budget})!")


def cmd_export(_args):                               # доп. фича: экспорт в CSV
    expenses = load_expenses()
    if not expenses:
        print("No expenses to export.")
        return
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Date", "Description", "Category", "Amount"])
        for e in expenses:
            writer.writerow([e["id"], e["date"], e["description"],
                             e.get("category", ""), e["amount"]])
    print(f"Expenses exported to {CSV_FILE}")


# ---------- Точка входа ----------

def main():
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="Simple CLI expense tracker.")

    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new expense")
    p_add.add_argument("--description", required=True, help="expense description")
    p_add.add_argument("--amount", required=True, help="expense amount")
    p_add.add_argument("--category", help=f"category: {', '.join(CATEGORIES)}")
    p_add.set_defaults(func=cmd_add)

    p_update = sub.add_parser("update", help="update an expense")
    p_update.add_argument("--id", type=int, required=True)
    p_update.add_argument("--description")
    p_update.add_argument("--amount")
    p_update.add_argument("--category")
    p_update.set_defaults(func=cmd_update)

    p_delete = sub.add_parser("delete", help="delete an expense")
    p_delete.add_argument("--id", type=int, required=True)
    p_delete.set_defaults(func=cmd_delete)

    p_list = sub.add_parser("list", help="list all expenses")
    p_list.add_argument("--category", help="filter by category")
    p_list.set_defaults(func=cmd_list)

    p_summary = sub.add_parser("summary", help="show total expenses")
    p_summary.add_argument("--month", type=int, help="month number (1-12)")
    p_summary.add_argument("--month-budget", type=float,
                           dest="month_budget", help="monthly budget check")
    p_summary.set_defaults(func=cmd_summary)

    sub.add_parser("export", help="export expenses to CSV").set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
