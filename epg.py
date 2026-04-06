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


def clean_title(title):
    import re

    # remove (E), (R), κλπ
    title = re.sub(r"\(.*?\)", "", title)

    # remove "Καθημερινά στις ..."
    title = re.sub(r"Καθημερινά\s+στις\s+\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)

    # remove extra spaces
    title = re.sub(r"\s+", " ", title)

    return title.strip()


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


def fill_24h(programmes):
    filled = []

    for i in range(len(programmes) - 1):
        filled.append(programmes[i])

        h1, m1 = map(int, programmes[i][0].split(":"))
        h2, m2 = map(int, programmes[i + 1][0].split(":"))

        t1 = h1 * 60 + m1
        t2 = h2 * 60 + m2

        # αν υπάρχει μεγάλο κενό → βάλε filler
        if t2 - t1 > 120:
            filled.append((f"{h1:02d}:{m1:02d}", "Unknown Program"))

    filled.append(programmes[-1])
    return filled


def build_xml(programmes):
    now = datetime.now()

    # 🔥 σωστή βάση ημέρας
    base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    current_day = 0
    last_hour = -1

    for i, (time_str, title) in enumerate(programmes):

        h, m = map(int, time_str.split(":"))

        # αν γυρίσει πίσω → νέα μέρα
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

    # 🔥 πάρε 3 μέρες για να είσαι safe (πιάνει πλήρη 48h πάντα)
    for _ in range(3):
    day_programmes = fetch_day(driver)

    # 👉 εδώ μπαίνει το fix για 24ωρο
    day_programmes = fill_24h(day_programmes)

    all_programmes.extend(day_programmes)

    if not click_next(driver):
        break

    driver.quit()

    build_xml(all_programmes)


if __name__ == "__main__":
    main()
