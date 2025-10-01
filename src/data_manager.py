import json
import os
from PyQt6.QtCore import QDate

DATA_FILE = "data.json"

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def get_notes_for_date(date):
    data = load_data()
    return data.get(date.toString("yyyy-MM-dd"), {})

def save_notes_for_date(date, notes):
    data = load_data()
    data[date.toString("yyyy-MM-dd")] = notes
    save_data(data)