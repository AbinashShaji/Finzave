import re
import os

files = [
    r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\transactions.html",
    r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\expenses.html"
]

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all <input type="date" ... > that don't already have max=
    # This regex looks for type="date" and inserts max="{{ today_date }}" just before it or after it.
    # A safer approach is to replace `type="date"` with `type="date" max="{{ today_date }}"` 
    # but only for specific inputs we care about or all if safe.
    # The requirement said to apply it to transaction related dates, which is all of them except goals (which are not in these files).
    
    # Simple replacement:
    content = content.replace('type="date"', 'type="date" max="{{ today_date }}"')
    # If there are duplicates like max="{{ today_date }}" max="{{ today_date }}", we can fix it:
    content = content.replace('max="{{ today_date }}" max="{{ today_date }}"', 'max="{{ today_date }}"')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Updated HTML files with max attribute")
