from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

URL = "https://www.alphacyprus.com.cy/program"

def get_driver():
    options = Options()
    # Ορίζουμε το binary που εγκαθιστά το GitHub Actions
    options.binary_location = "/opt/hostedtoolcache/setup-chrome/chromium/1610237/x64/chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def clean_title(title):
    # Αφαιρεί παρενθέσεις π.χ. (E), (R)
    title = re.sub(r"\(.*?\)", "", title)
    # Αφαιρεί LIVE NOW
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    # Αφαιρεί φράσεις με μέρα + ώρα
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)
    # Αφαιρεί τη φράση WEBTV
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    # Καθαρίζει περιττά κενά
    return re.sub(r"\s+", " ", title).strip()

def fetch_programmes(driver):
    print("Φόρτωση σελίδας...")
    driver.get(URL)
    time.sleep(5)  # δίνουμε λίγο χρόνο για να φορτωθεί το JS

    soup = BeautifulSoup(driver.page_source, "html.parser")
    lines = soup.get_text("\n").split("\n")
    programmes = []

    time_pattern = re.compile(r"^\s*(\d{1,2}:\d{2})\s*$")
    current_time = None
    for line in lines:
        line = line.strip()
        if time_pattern.match(line):
            current_time = line
            continue
        if current_time and line:
            title = clean_title(line)
            if title:
                programmes.append((current_time, title))
            current_time = None
    return programmes

def build_xml(programmes):
    if not programmes:
        print("❌ Κανένα πρόγραμμα βρέθηκε.")
        return

    now = datetime.now()
    base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    last_hour = -1
    current_day = 0
    events = []

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

        # Μόνο Δευτέρα-Πέμπτη
        if 0 <= start_dt.weekday() <= 3:
            start = start_dt.strftime("%Y%m%d%H%M%S +0300")
            stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
            xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
            xml += f"  <title>{title}</title>\n</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✅ epg.xml δημιουργήθηκε με {len(programmes)} προγράμματα (Δευ–Πέμπτη).")

def main():
    driver = get_driver()
    programmes = fetch_programmes(driver)
    driver.quit()
    build_xml(programmes)

if __name__ == "__main__":
    main()
