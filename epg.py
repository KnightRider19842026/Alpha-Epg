from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

URL = "https://www.alphacyprus.com.cy/program"

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


import re

def clean_title(title):
    # αφαιρεί παρενθέσεις π.χ. (E), (R)
    title = re.sub(r"\(.*?\)", "", title)

    # αφαιρεί LIVE NOW (case-insensitive)
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)

    # αφαιρεί φράσεις με μέρα + ώρα
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )

    # αφαιρεί γενικά υπολείμματα με μέρα + ώρα κολλημένα
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)

    # αφαιρεί φράση "Δες όλα τα επεισόδια στο WEBTV"
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)

    # καθαρίζει περιττά κενά
    title = re.sub(r"\s+", " ", title).strip()

    return title

# παραδείγματα
titles = [
    "DEAL (E) LIVE NOW",
    "ΜΑΓΕΙΡΙΚΗ ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ ΣΤΙΣ 19:00",
    "ΤΑ ΕΠΕΙΣΟΔΙΑ (R) ΚΑΘΗΜΕΡΙΝΑ ΣΤΙΣ 21:30",
    "ΝΕΑ ΣΕΙΡΑ Δες όλα τα επεισόδια στο WEBTV"
]

for t in titles:
    print(clean_title(t))


def fetch_day(driver):
    print("   Φόρτωση προγράμματος...")
    time.sleep(6)  # δίνουμε χρόνο στο JavaScript να φορτώσει πλήρως
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    programmes = []
    
    time_pattern = re.compile(r'(\d{1,2}:\d{2})')
    
    # Βρίσκουμε όλα τα πιθανά containers που μπορεί να περιέχουν πρόγραμμα
    containers = soup.find_all(["div", "li", "article", "section", "a"], class_=True)
    
    for container in containers:
        full_text = container.get_text(" ", strip=True)
        
        # Βρίσκουμε την ώρα
        match = time_pattern.search(full_text)
        if not match:
            continue
            
        time_str = match.group(1)
        
        # Παίρνουμε τον τίτλο αφαιρώντας την ώρα
        raw_title = time_pattern.sub("", full_text, count=1).strip()
        title = clean_title(raw_title)
        
        # Φίλτρα για να αποφύγουμε σκουπίδια
        if (len(title) > 4 and 
            title.lower() not in ["live", "live:", ""] and 
            not title.startswith(("http", "Επόμενη", "Προηγούμενη", "Next")) and
            "MICROSITE" not in title.upper()):
            
            programmes.append((time_str, title))
    
    # Αφαίρεση διπλοτύπων
    seen = set()
    unique_programmes = []
    for t, title in programmes:
        key = (t, title[:100])
        if key not in seen:
            seen.add(key)
            unique_programmes.append((t, title))
    
    print(f"   → Βρέθηκαν {len(unique_programmes)} προγράμματα")
    if unique_programmes:
        print("   Πρώτα 5:", [title for _, title in unique_programmes[:5]])
    
    return unique_programmes


def click_next(driver):
    try:
        selectors = [
            "//button[contains(., 'Next') or contains(., 'Επόμενη') or contains(., '→')]",
            "//button[contains(@class, 'next')]",
            "//a[contains(@class, 'next')]",
            "//button[contains(@aria-label, 'Next')]"
        ]
        
        for selector in selectors:
            buttons = driver.find_elements(By.XPATH, selector)
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(1.5)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(6)
                    return True
        return False
    except Exception as e:
        print(f"   Click next error: {e}")
        return False


def build_xml(programmes):
    if not programmes:
        print("❌ Δεν βρέθηκαν προγράμματα. Το XML δεν δημιουργήθηκε.")
        return

    now = datetime.now()
    base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    events = []
    current_day = 0
    last_hour = -1

    for i, (time_str, title) in enumerate(programmes):
        h, m = map(int, time_str.split(":"))

        if h < last_hour and i > 0:
            current_day += 1

        start_dt = base_date + timedelta(days=current_day, hours=h, minutes=m)

        # Υπολογισμός stop time
        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            next_day = current_day + (1 if nh < h else 0)
            stop_dt = base_date + timedelta(days=next_day, hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        last_hour = h
        events.append((start_dt, stop_dt, title))

    # Δημιουργία XML
    for start_dt, stop_dt, title in events:
        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
        
        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"  <title>{title}</title>\n"
        xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✅ Επιτυχία! Το epg.xml δημιουργήθηκε με {len(events)} προγράμματα.")


def main():
    driver = get_driver()
    print("Άνοιγμα σελίδας Alpha Cyprus...")
    driver.get(URL)

    all_programmes = []

    for day in range(4):   # Δοκιμάζουμε μέχρι 4 μέρες
        print(f"\n📅 Ημέρα {day + 1}:")
        day_prog = fetch_day(driver)
        all_programmes.extend(day_prog)

        if not click_next(driver):
            print("   Δεν βρέθηκε κουμπί 'Επόμενη' ή τέλος διαθέσιμων ημερών.")
            break

    driver.quit()

    print(f"\nΣυνολικά συλλέχθηκαν {len(all_programmes)} εγγραφές προγράμματος.")
    build_xml(all_programmes)


if __name__ == "__main__":
    main()
