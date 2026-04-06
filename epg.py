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
    return webdriver.Chrome(options=options)


import re

def clean_title(title):
    # αφαιρεί παρενθέσεις π.χ. (E), (R)
    title = re.sub(r"\(.*?\)", "", title)

    # αφαιρεί LIVE NOW (case-insensitive)
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)

    # αφαιρεί ημέρες + ώρα, π.χ. ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ ΣΤΙΣ 19:00 ή ΚΑΘΗΜΕΡΙΝΑ ΣΤΙΣ 21:30
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)

    # αφαιρεί γενικά υπολείμματα με μέρα + ώρα κολλημένα
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)

    # καθαρίζει περιττά κενά
    title = re.sub(r"\s+", " ", title).strip()

    return title

# παραδείγματα
titles = [
    "DEAL (E) LIVE NOW",
    "ΜΑΓΕΙΡΙΚΗ ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ ΣΤΙΣ 19:00",
    "ΤΑ ΕΠΕΙΣΟΔΙΑ (R) ΚΑΘΗΜΕΡΙΝΑ ΣΤΙΣ 21:30"
]

for t in titles:
    print(clean_title(t))


def fetch_day(driver):
    time.sleep(3)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    programmes = []
    current_time = None

    for tag in soup.find_all(["div", "span"]):
        text = tag.get_text(strip=True)

        if len(text) == 5 and ":" in text:
            current_time = text

        elif current_time and len(text) > 2:
            programmes.append((current_time, clean_title(text)))
            current_time = None

    return programmes


def click_next(driver):
    try:
        btn = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        return True
    except:
        return False


def build_xml(programmes):
    now = datetime.now()
    base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    events = []

    current_day = 0
    last_hour = -1

    # convert to datetime events
    for i, (time_str, title) in enumerate(programmes):

        h, m = map(int, time_str.split(":"))

        if h < last_hour:
            current_day += 1

        start_dt = base_date + timedelta(days=current_day, hours=h, minutes=m)

        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            next_day = current_day

            if nh < h:
                next_day += 1

            stop_dt = base_date + timedelta(days=next_day, hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        last_hour = h

        events.append((start_dt, stop_dt, title))

    # keep ONLY today 00:00–23:59

    xml_events = events

    # build XML
    for start_dt, stop_dt, title in xml_events:

        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")

        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"<title>{title}</title>\n"
        xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    driver = get_driver()
    driver.get(URL)

    all_programmes = []

    # πάρε 3 μέρες για σωστό parsing
    for _ in range(3):
        day_programmes = fetch_day(driver)
        all_programmes.extend(day_programmes)

        if not click_next(driver):
            break

    driver.quit()

    build_xml(all_programmes)


if __name__ == "__main__":
    main()
