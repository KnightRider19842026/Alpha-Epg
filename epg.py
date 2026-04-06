from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    # αφαιρεί παρενθέσεις π.χ. (E), (R)
    title = re.sub(r"\(.*?\)", "", title)
    # αφαιρεί LIVE NOW
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    # αφαιρεί φράσεις μέρα + ώρα
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)
    # αφαιρεί τη φράση WEBTV
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    # καθαρίζει περιττά κενά
    return re.sub(r"\s+", " ", title).strip()

def fetch_day(driver):
    print("   Φόρτωση προγράμματος...")
    # περιμένουμε να εμφανιστεί κάποιο πρόγραμμα
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.programme-item"))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    programmes = []

    # παίρνουμε μόνο τα div με class programme-item (1η στήλη = ώρα, 2η = τίτλος)
    containers = soup.select("div.programme-item")
    
    for c in containers:
        # παίρνουμε ώρα και τίτλο
        time_el = c.select_one(".time")
        title_el = c.select_one(".title")
        if not time_el or not title_el:
            continue
        time_str = time_el.get_text(strip=True)
        title = clean_title(title_el.get_text(" ", strip=True))
        if time_str and title:
            programmes.append((time_str, title))
    return programmes

def build_xml(programmes):
    if not programmes:
        print("❌ Δεν βρέθηκαν προγράμματα.")
        return

    now = datetime.now()
    base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    last_hour = -1
    current_day = 0

    for i, (time_str, title) in enumerate(programmes):
        h, m = map(int, time_str.split(":"))
        if h < last_hour and i > 0:
            current_day += 1
        start_dt = base_date + timedelta(days=current_day, hours=h, minutes=m)

        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            next_day = current_day + (1 if nh < h else 0)
            stop_dt = base_date + timedelta(days=next_day, hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        last_hour = h

        # μόνο Δευτέρα-Πέμπτη
        if 0 <= start_dt.weekday() <= 3:
            start = start_dt.strftime("%Y%m%d%H%M%S +0300")
            stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
            xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
            xml += f"  <title>{title}</title>\n"
            xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ epg.xml δημιουργήθηκε με {len(programmes)} προγράμματα (Δευ–Πέμπτη).")

def main():
    driver = get_driver()
    driver.get(URL)
    programmes = fetch_day(driver)
    driver.quit()
    build_xml(programmes)

if __name__ == "__main__":
    main()
