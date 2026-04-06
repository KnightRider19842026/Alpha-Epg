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

def clean_title(title):
    title = re.sub(r"\(.*?\)", "", title)                    # (E), (R) κλπ.
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    title = re.sub(r"ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ\s*ΣΤΙΣ\s*\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def fetch_day(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(4)   # δώσε χρόνο στο JS να φορτώσει το πρόγραμμα
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    programmes = []
    
    # Κύρια προσπάθεια: Βρες όλα τα στοιχεία που έχουν ώρα XX:XX
    time_tags = soup.find_all(string=re.compile(r'^\s*\d{1,2}:\d{2}\s*$'))
    
    for time_tag in time_tags:
        time_str = time_tag.strip()
        
        # Πάρε το parent container και ψάξε για τον τίτλο κοντά του
        parent = time_tag.parent
        container = parent.find_parent(["div", "li", "a", "tr"]) or parent
        
        # Βρες τίτλο (συνήθως link ή h tag ή μεγάλο text)
        title_tag = container.find("a") or container.find(["h3", "h4", "strong"]) or container
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        
        # Αφαίρεσε την ώρα από τον τίτλο
        title = re.sub(r'^\s*\d{1,2}:\d{2}\s*', '', title_text)
        title = clean_title(title)
        
        if title and len(title) > 3:
            programmes.append((time_str, title))
    
    # Αφαίρεσε διπλότυπα
    seen = set()
    unique = []
    for t, title in programmes:
        if (t, title) not in seen:
            seen.add((t, title))
            unique.append((t, title))
    
    print(f"   → Βρέθηκαν {len(unique)} προγράμματα")
    return unique

def click_next(driver):
    try:
        # Δοκιμάζουμε πολλαπλούς selectors
        selectors = [
            "//button[contains(., 'Next') or contains(., 'Επόμενη') or contains(., '→')]",
            "//button[contains(@class, 'next')]",
            "//a[contains(@class, 'next')]",
        ]
        for sel in selectors:
            btns = driver.find_elements(By.XPATH, sel)
            for btn in btns:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(5)
                    return True
        return False
    except:
        return False

def build_xml(programmes):
    if not programmes:
        print("Δεν βρέθηκαν προγράμματα! Το XML δεν θα δημιουργηθεί.")
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

        if h < last_hour and i > 0:          # πέρασε μεσάνυχτα
            current_day += 1

        start_dt = base_date + timedelta(days=current_day, hours=h, minutes=m)

        # Υπολογισμός stop time
        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            next_day = current_day + (1 if nh < h else 0)
            stop_dt = base_date + timedelta(days=next_day, hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(hours=1)

        last_hour = h
        events.append((start_dt, stop_dt, title))

    # Γράψιμο XML
    for start_dt, stop_dt, title in events:
        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"  <title>{title}</title>\n"
        xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    
    print(f"✅ Το epg.xml δημιουργήθηκε με {len(events)} προγράμματα.")

def main():
    driver = get_driver()
    driver.get(URL)
    print("Φόρτωση σελίδας...")

    all_programmes = []

    for day in range(4):        # δοκίμασε μέχρι 4 μέρες
        print(f"\nΗμέρα {day+1}:")
        day_prog = fetch_day(driver)
        all_programmes.extend(day_prog)
        
        if not click_next(driver):
            print("Δεν βρέθηκε κουμπί Next ή τέλος σελίδας.")
            break

    driver.quit()

    print(f"\nΣυνολικά συλλέχθηκαν {len(all_programmes)} εγγραφές.")
    build_xml(all_programmes)

if __name__ == "__main__":
    main()
