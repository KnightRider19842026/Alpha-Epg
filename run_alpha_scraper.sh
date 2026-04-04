#!/bin/bash

# =============================================
# Alpha Cyprus TV Program Scraper - Bash Runner
# =============================================

echo "========================================"
echo "🚀 Ξεκινάει το Alpha Cyprus Scraper..."
echo "========================================"

# Πήγαινε στον φάκελο του project (άλλαξε το path αν χρειάζεται)
cd /path/to/your/github/repo/alpha-cyprus-program || {
    echo "❌ Δεν βρέθηκε ο φάκελος του repository!"
    exit 1
}

# Ενεργοποίηση virtual environment (προαιρετικό αλλά προτεινόμενο)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment ενεργοποιήθηκε"
fi

# Εκτέλεση του Python script
echo "📡 Τρέχει το Python scraper..."
python3 alpha_cyprus_scraper.py

if [ $? -eq 0 ]; then
    echo "✅ Το XML δημιουργήθηκε επιτυχώς!"
else
    echo "❌ Σφάλμα κατά την εκτέλεση του Python script"
    exit 1
fi

# Git operations
echo "📤 Γίνεται commit & push στο GitHub..."

git add alpha-cyprus-program.xml
git commit -m "Update Alpha Cyprus program - $(date '+%Y-%m-%d %H:%M:%S')" --quiet

if [ $? -eq 0 ]; then
    echo "✅ Commit δημιουργήθηκε"
    git push origin main          # άλλαξε "main" σε "master" αν χρησιμοποιείς master branch
    echo "🚀 Push έγινε επιτυχώς!"
else
    echo "ℹ️  Δεν υπάρχουν αλλαγές για commit"
fi

echo "========================================"
echo "🎉 Ολοκληρώθηκε στις $(date)"
echo "========================================"
