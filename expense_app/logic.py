"""
Core expense-tracking logic — ported from the original ass3.py.
Same behavior, same chatbot commands, just storage paths made mobile-safe.
"""
import json
import os
import re
import random
from datetime import datetime

CATEGORY_EMOJI = {
    "food": "🍔", "mess": "🍱", "lunch": "🥗", "dinner": "🍛", "breakfast": "🍳",
    "travel": "🚕", "uber": "🚖", "bus": "🚌", "train": "🚆", "fuel": "⛽",
    "shopping": "🛍️", "clothes": "👕", "shoes": "👟",
    "bills": "💡", "electricity": "🔌", "water": "💧", "internet": "🌐", "rent": "🏠",
    "movie": "🎬", "entertainment": "🎮", "game": "🎮",
    "medical": "💊", "doctor": "👨‍⚕️", "medicine": "💊",
    "education": "📚", "books": "📖", "fees": "🎓",
    "grocery": "🛒", "vegetables": "🥦", "fruits": "🍎",
    "general": "💰"
}


def get_emoji(category):
    for key in CATEGORY_EMOJI:
        if key in category.lower():
            return CATEGORY_EMOJI[key]
    return "💰"


class ExpenseStore:
    """Handles all file I/O. Takes a writable data_dir (mobile-safe app storage)."""

    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self.expenses_file = os.path.join(data_dir, "expenses.json")
        self.budget_file = os.path.join(data_dir, "budget.json")

    def load_expenses(self):
        try:
            with open(self.expenses_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save_expenses(self, expenses):
        with open(self.expenses_file, "w") as f:
            json.dump(expenses, f, indent=4)

    def load_budget(self):
        try:
            with open(self.budget_file, "r") as f:
                return json.load(f).get("budget", 0)
        except Exception:
            return 0

    def save_budget(self, amount):
        with open(self.budget_file, "w") as f:
            json.dump({"budget": amount}, f)


class ExpenseManager:
    def __init__(self, store: ExpenseStore):
        self.store = store

    # ---------- FEATURES ----------
    def add_expense(self, amount, category, currency="₹"):
        expenses = self.store.load_expenses()
        emoji = get_emoji(category)
        expenses.append({
            "amount": amount,
            "category": category,
            "emoji": emoji,
            "currency": currency,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.store.save_expenses(expenses)

        replies = [
            f"Got it! Added {currency}{amount} for {category} {emoji}",
            f"Noted! {currency}{amount} spent on {category} ✅ {emoji}",
            f"Okay, {currency}{amount} for {category} saved! 💾 {emoji}",
            f"Done! {emoji} {currency}{amount} added under {category}",
            f"Recorded ✍️ {currency}{amount} → {category} {emoji}"
        ]
        reply = random.choice(replies)

        budget = self.store.load_budget()
        if budget > 0:
            total = sum(e['amount'] for e in expenses)
            if total > budget:
                reply += f"\n⚠️ ALERT! You crossed your budget of ₹{budget}! Total spent: ₹{total}"
            elif total >= budget * 0.8:
                reply += f"\n⚠️ Warning! You've used 80% of your budget (₹{total}/₹{budget})"

        return reply

    def show_expenses(self):
        expenses = self.store.load_expenses()
        if not expenses:
            return "No expenses found. 📭"

        result = "📋 Your Expenses:\n"
        for i, e in enumerate(expenses, 1):
            emoji = e.get("emoji", "💰")
            currency = e.get("currency", "₹")
            result += f"{i}. {emoji} {currency}{e['amount']} - {e['category']} ({e['date']})\n"
        return result

    def delete_expense(self, index):
        expenses = self.store.load_expenses()
        if index is not None and 0 < index <= len(expenses):
            removed = expenses.pop(index - 1)
            self.store.save_expenses(expenses)
            currency = removed.get("currency", "₹")
            return f"🗑️ Deleted {currency}{removed['amount']} ({removed['category']})"
        return "❌ Invalid index!"

    def show_summary(self):
        expenses = self.store.load_expenses()
        if not expenses:
            return "No expenses yet! 📭"

        total = sum(e['amount'] for e in expenses)
        budget = self.store.load_budget()

        result = f"💰 Total spent: ₹{total}\n"
        if budget > 0:
            remaining = budget - total
            result += f"🎯 Budget: ₹{budget}\n"
            if remaining >= 0:
                result += f"✅ Remaining: ₹{remaining}\n"
            else:
                result += f"⚠️ Over budget by: ₹{abs(remaining)}\n"

        cat_totals = {}
        for e in expenses:
            cat_totals[e['category']] = cat_totals.get(e['category'], 0) + e['amount']

        if cat_totals:
            top_cat = max(cat_totals, key=cat_totals.get)
            emoji = get_emoji(top_cat)
            result += f"🏆 Top spending: {emoji} {top_cat} (₹{cat_totals[top_cat]})"

        return result

    def search_expense(self, category):
        expenses = self.store.load_expenses()
        results = [e for e in expenses if category.lower() in e['category'].lower()]

        if not results:
            return f"🔍 No matching expenses found for '{category}'."

        result = f"🔍 Results for '{category}':\n"
        for e in results:
            emoji = e.get("emoji", "💰")
            currency = e.get("currency", "₹")
            result += f"{emoji} {currency}{e['amount']} - {e['category']} ({e['date']})\n"
        return result

    def filter_by_date(self, period):
        expenses = self.store.load_expenses()
        today = datetime.now()
        filtered = []

        for e in expenses:
            try:
                exp_date = datetime.strptime(e['date'], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                continue

            if period == "today" and exp_date.date() == today.date():
                filtered.append(e)
            elif period == "month" and exp_date.month == today.month and exp_date.year == today.year:
                filtered.append(e)
            elif period == "week":
                diff = (today - exp_date).days
                if 0 <= diff <= 7:
                    filtered.append(e)

        if not filtered:
            return f"📅 No expenses found for {period}."

        total = sum(e['amount'] for e in filtered)
        currency = filtered[0].get("currency", "₹")
        result = f"📅 Expenses for {period.upper()}:\n"
        for e in filtered:
            emoji = e.get("emoji", "💰")
            cur = e.get("currency", "₹")
            result += f"{emoji} {cur}{e['amount']} - {e['category']} ({e['date']})\n"
        result += f"\n💰 Total: {currency}{total}"
        return result

    def edit_expense(self, index, new_amount):
        expenses = self.store.load_expenses()
        if index is not None and 0 < index <= len(expenses):
            old_amount = expenses[index - 1]['amount']
            currency = expenses[index - 1].get("currency", "₹")
            expenses[index - 1]['amount'] = new_amount
            self.store.save_expenses(expenses)
            return f"✏️ Updated expense #{index}: {currency}{old_amount} → {currency}{new_amount}"
        return "❌ Invalid expense number!"

    def clear_all(self):
        self.store.save_expenses([])
        return "🧹 All expenses cleared!"

    def category_totals(self):
        expenses = self.store.load_expenses()
        data = {}
        for e in expenses:
            data[e["category"]] = data.get(e["category"], 0) + e["amount"]
        return data

    def daily_reminder(self):
        expenses = self.store.load_expenses()
        today = datetime.now().date()
        today_expenses = []
        for e in expenses:
            try:
                exp_date = datetime.strptime(e['date'], "%Y-%m-%d %H:%M").date()
                if exp_date == today:
                    today_expenses.append(e)
            except (ValueError, KeyError):
                continue

        if not today_expenses:
            return "🔔 Reminder: You haven't tracked any expenses today!"
        total = sum(e['amount'] for e in today_expenses)
        return f"📊 You've spent ₹{total} today ({len(today_expenses)} items)"


# ---------- CHATBOT PARSING ----------
def extract_amount(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else None


def extract_currency(text):
    if "$" in text or "dollar" in text.lower():
        return "$"
    elif "€" in text or "euro" in text.lower():
        return "€"
    elif "£" in text or "pound" in text.lower():
        return "£"
    return "₹"


def extract_category(text):
    match = re.search(r'(?:on|for|in|at|to|from)\s+([a-zA-Z ]+)', text.lower())
    if match:
        return match.group(1).strip()

    words = re.findall(r'[a-zA-Z]+', text)
    skip = {
        "i", "spent", "spend", "add", "paid", "pay", "buy", "bought",
        "rs", "rupees", "dollar", "dollars", "euro", "pound", "for", "on",
        "at", "in", "to", "from", "with", "about", "of", "the", "and", "or",
        "my", "your", "our", "their", "me", "you", "us", "them"
    }
    words = [w for w in words if w.lower() not in skip]
    return words[-1] if words else "general"


class Chatbot:
    """Wraps ExpenseManager with the same text-command parsing as the original app."""

    def __init__(self, manager: ExpenseManager, on_confirm_clear=None):
        self.mgr = manager
        # on_confirm_clear: optional callback(confirm_yes_callback) used by the UI
        # to show a Yes/No popup instead of a blocking messagebox.
        self.on_confirm_clear = on_confirm_clear

    def respond(self, user_input):
        user_input = user_input.lower().strip()

        greetings = ["hi", "hii", "hello", "hey", "good morning", "good evening", "good afternoon"]
        if any(g == user_input or user_input.startswith(g + " ") for g in greetings):
            return random.choice([
                "Hey there! 👋 Ready to track your expenses?",
                "Hello! 😊 How can I help you today?",
                "Hi! 🌟 What did you spend on today?",
                "Hey! 💰 Let's manage your money smartly!",
                "Hello friend! 👋 Tell me about your expenses."
            ])

        if "thank" in user_input:
            return random.choice([
                "You're welcome! 💖", "Anytime! 😊", "Happy to help! 🌟", "My pleasure! 🤗"
            ])

        if any(word in user_input for word in ["bye", "goodbye", "see you"]):
            return random.choice([
                "Goodbye! Spend wisely! 👋", "See you later! 💰", "Bye bye! Take care! 🌟"
            ])

        if "how are you" in user_input:
            return "I'm great! 🤖 Ready to help you save money! How about you?"

        if "help" in user_input:
            return ("🆘 Here's what I can do:\n"
                    "💸 add 500 on food → Add expense\n"
                    "📋 show → Show all expenses\n"
                    "📅 today / this month / this week → Filter by date\n"
                    "🔍 search food → Search expenses\n"
                    "📊 summary → View totals + top category\n"
                    "✏️ edit 2 to 600 → Edit expense #2\n"
                    "🗑 delete 1 → Delete expense #1\n"
                    "🎯 set budget → Set monthly budget\n"
                    "👋 hi, bye, thanks → Chat with me!")

        if "today" in user_input:
            return self.mgr.filter_by_date("today")
        if "this month" in user_input or "month" in user_input:
            return self.mgr.filter_by_date("month")
        if "this week" in user_input or "week" in user_input:
            return self.mgr.filter_by_date("week")

        if "edit" in user_input or "change" in user_input or "update" in user_input:
            numbers = re.findall(r'\d+', user_input)
            if len(numbers) >= 2:
                return self.mgr.edit_expense(int(numbers[0]), int(numbers[1]))
            return "✏️ Format: edit 2 to 600 (edits expense #2 to ₹600)"

        if "budget" in user_input:
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                self.mgr.store.save_budget(int(numbers[0]))
                return f"🎯 Budget set to ₹{numbers[0]}! I'll alert you when you cross it."
            budget = self.mgr.store.load_budget()
            if budget > 0:
                return f"🎯 Your current budget: ₹{budget}"
            return "🎯 Say: 'set budget 5000' to set your monthly budget"

        if any(word in user_input for word in ["add", "spent", "spend", "pay", "paid", "buy", "bought"]):
            amount = extract_amount(user_input)
            category = extract_category(user_input)
            currency = extract_currency(user_input)
            if amount:
                return self.mgr.add_expense(amount, category, currency)
            return "💡 Please specify amount! Example: 'spent 500 on food'"

        if "show" in user_input or "list" in user_input:
            return self.mgr.show_expenses()

        if "delete" in user_input or "remove" in user_input:
            index = extract_amount(user_input)
            return self.mgr.delete_expense(index) if index else "🗑 Give expense number to delete."

        if "summary" in user_input or "total" in user_input:
            return self.mgr.show_summary()

        if "search" in user_input or "find" in user_input:
            parts = user_input.split()
            if len(parts) > 1:
                return self.mgr.search_expense(parts[-1])
            return "🔍 Please specify category to search."

        if "clear" in user_input:
            return "CONFIRM_CLEAR"  # UI layer shows a popup and calls mgr.clear_all()

        if "exit" in user_input or "quit" in user_input:
            return "EXIT"

        return "🤔 I didn't understand. Type 'help' to see what I can do!"
