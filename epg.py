from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def fetch_day(driver):
    print("   Φόρτωση προγράμματος...")
    time.sleep(6)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    programmes = []
    
    time_pattern = re.compile(r'(\d{1,2}:\d{2})')
    containers = soup.find_all(["div", "li", "article", "section", "a"], class_=True)
    
    for container in containers:
        full_text = container.get_text(" ", strip=True)
        match = time_pattern.search(full_text)
        if not match:
            continue
            
        time_str = match.group(1)
        raw_title = time_pattern.sub("", full_text, count=1).strip()
        title = clean_title(raw_title)
        
        if (len(title) > 4 and 
            title.lower() not in ["live", "live:", ""] and 
            not title.startswith(("http", "Επόμενη", "Προηγούμενη", "Next")) and
            "MICROSITE" not in title.upper()):
            
            programmes.append((time_str, title))
    
    seen = set()
    unique_programmes = []
    for t, title in programmes:
        key = (t, title[:100])
        if key not in seen:
            seen.add(key)
            unique_programmes.append((t, title))
    
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

        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            next_day = current_day + (1 if nh < h else 0)
            stop_dt = base_date + timedelta(days=next_day, hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        last_hour = h

        # φιλτράρουμε μόνο Δευτέρα(0) έως Πέμπτη(3)
        if 0 <= start_dt.weekday() <= 3:
            events.append((start_dt, stop_dt, title))

    for start_dt, stop_dt, title in events:
        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"  <title>{title}</title>\n"
        xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✅ Το epg.xml δημιουργήθηκε με {len(events)} προγράμματα (Δευτέρα-Πέμπτη).")

def main():
    while True:
        driver = get_driver()
        print("Άνοιγμα σελίδας Alpha Cyprus...")
        driver.get(URL)

        all_programmes = []
        for day in range(4):
            day_prog = fetch_day(driver)
            all_programmes.extend(day_prog)
            if not click_next(driver):
                break

        driver.quit()
        build_xml(all_programmes)

        print("\n⏳ Αναμονή 2 ημερών για αυτόματη ανανέωση...")
        time.sleep(2 * 24 * 60 * 60)  # 2 ημέρες σε δευτερόλεπτα

if __name__ == "__main__":
    main()
