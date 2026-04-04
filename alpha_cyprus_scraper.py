import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DAYS_TO_SCRAPE = 4                    # Πόσες ημέρες (από σήμερα)
OUTPUT_FILE = "alpha-cyprus-program.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_program_for_day(date_obj):
    """Προσομοίωση / scraping για μία ημέρα (προς το παρόν manual fallback)"""
    weekday_gr = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"][date_obj.weekday()]
    
    # Εδώ θα βάλουμε το πραγματικό scraping όταν η σελίδα επιτρέπει
    # Προς το παρόν δίνουμε παράδειγμα με δεδομένα από προηγούμενες ημέρες
    programs = []
    
    if weekday_gr == "Κυριακή":
        programs = [
            ("06:00", "MY GREECE", "ΨΥΧΑΓΩΓΙΑ", "", "Ταξιδιωτικό μαγκαζίνο", "Επανάληψη"),
            ("07:00", "ΜΗΝ ΑΡΧΙΖΕΙΣ ΤΗ ΜΟΥΡΜΟΥΡΑ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "", "", "Επανάληψη"),
            ("07:50", "ΟΙΚΟΓΕΝΕΙΑΚΕΣ ΙΣΤΟΡΙΕΣ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "", "", "Επανάληψη"),
            ("08:45", "KITCHEN LAB", "ΨΥΧΑΓΩΓΙΑ", "", "Μαγειρική", ""),
            ("09:45", "ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ ΜΕ ΤΟΝ ΜΑΝΕΣΗ", "ΕΝΗΜΕΡΩΣΗ", "", "", "Live"),
            ("13:00", "ΕΧΩ ΠΑΙΔΙΑ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "", "", "Επανάληψη"),
            ("18:05", "ALPHA NEWS", "ΕΝΗΜΕΡΩΣΗ", "", "Δελτίο Ειδήσεων", "Live"),
            ("20:00", "ALPHA NEWS", "ΕΝΗΜΕΡΩΣΗ", "", "Κεντρικό Δελτίο", "Live"),
            ("21:00", "ΠΑΡΑΔΟΣΙΑΚΗ ΒΡΑΔΙΑ", "ΨΥΧΑΓΩΓΙΑ", "", "", ""),
        ]
    elif weekday_gr in ["Δευτέρα", "Τρίτη", "Τετάρτη"]:
        programs = [
            ("06:00", "DEAL", "ΨΥΧΑΓΩΓΙΑ", "", "", "Επανάληψη"),
            ("06:45", "ALPHA ΚΑΛΗΜΕΡΑ", "ΕΝΗΜΕΡΩΣΗ", "", "Πρωινή εκπομπή", "Live"),
            ("18:10", "ΝΑ Μ' ΑΓΑΠΑΣ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "Επ. 88", "", ""),
            ("20:00", "ALPHA NEWS", "ΕΝΗΜΕΡΩΣΗ", "", "Κεντρικό Δελτίο", "Live"),
            ("21:00", "ΑΓΙΟΣ ΕΡΩΤΑΣ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "", "", ""),
            ("22:20", "Η ΓΗ ΤΗΣ ΕΛΙΑΣ", "ΕΛΛΗΝΙΚΕΣ ΣΕΙΡΕΣ", "5ος κύκλος", "", ""),
        ]
    
    return programs, weekday_gr


def create_xml():
    root = ET.Element("alpha_cyprus_program")
    ET.SubElement(root, "channel").text = "Alpha Cyprus"
    ET.SubElement(root, "generated_date").text = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    today = datetime.now().date()
    
    for i in range(DAYS_TO_SCRAPE):
        current_date = today + timedelta(days=i)
        programs, weekday = get_program_for_day(current_date)
        
        day_elem = ET.SubElement(root, "day")
        day_elem.set("date", current_date.strftime("%Y-%m-%d"))
        day_elem.set("weekday", weekday)
        
        for time, title, category, episode, description, prog_type in programs:
            prog = ET.SubElement(day_elem, "program")
            ET.SubElement(prog, "time").text = time
            ET.SubElement(prog, "title").text = title
            ET.SubElement(prog, "category").text = category
            ET.SubElement(prog, "episode").text = episode
            ET.SubElement(prog, "description").text = description
            ET.SubElement(prog, "type").text = prog_type
    
    # Αποθήκευση XML όμορφα
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)   # Python 3.9+
    
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ Το XML δημιουργήθηκε επιτυχώς: {OUTPUT_FILE}")
    print(f"   Περιλαμβάνει {DAYS_TO_SCRAPE} ημέρες (από {today.strftime('%d/%m/%Y')})")


if __name__ == "__main__":
    create_xml()
    
    # Προαιρετικά: Άνοιγμα του αρχείου αυτόματα
    # os.startfile(OUTPUT_FILE)   # Windows
    # os.system(f"open {OUTPUT_FILE}")  # macOS
