import os
import json

DATA_PATH = "data"
EXPENSES_FILE = os.path.join(DATA_PATH, "expenses.json")
CATEGORIES_FILE = os.path.join(DATA_PATH, "categories.json")
INCOME_FILE = os.path.join(DATA_PATH, "income.json")
INCOME_CATEGORIES_FILE = os.path.join(DATA_PATH, "income_categories.json")
SETTINGS_FILE = "data/settings.json"


def ensure_files():
    os.makedirs(DATA_PATH, exist_ok=True)

    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(INCOME_FILE):
        with open(INCOME_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(INCOME_CATEGORIES_FILE):
        with open(INCOME_CATEGORIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

message_tracker = {}
