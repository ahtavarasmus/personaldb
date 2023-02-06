import json
import requests

with open('data/reminders.json', encoding='utf-8') as f:
    reminders = json.loads(f.read())

for reminder in reminders:
    r = requests.post("http://127.0.0.1:5000/reminder/new", json = reminder)
    print(f"Created reminder {reminder['message']} with ID {r.text}")
