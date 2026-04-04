#!/usr/bin/env python3
import datetime
import sys

print("=== EPG Update Ξεκίνησε ===")
print(f"Ημερομηνία: {datetime.datetime.now()}")

# Εδώ βάλε τον κώδικα σου για να κατεβάσεις EPG για 4 μέρες
# Παράδειγμα:
today = datetime.date.today()

for i in range(4):          # 0 = σήμερα, 1 = αύριο, ..., 3 = μεθαύριο +1
    target_date = today + datetime.timedelta(days=i)
    print(f"Λήψη EPG για: {target_date}")
    
    # Εδώ η λογική σου για download / generate EPG
    # π.χ. requests.get(...), xmltv κλπ.

print("=== EPG Update Ολοκληρώθηκε με επιτυχία! ===")
