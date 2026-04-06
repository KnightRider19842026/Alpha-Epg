from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

URL = "https://www.alphacyprus.com.cy/program"


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def fetch_day_html(driver):
    time.sleep(3)
    return driver.page_source


def click_next_day(driver):
    try:
        next_btn = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(3)
        return True
    except:
        return False


def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    programmes = []
    current_time = None

    for tag in soup.find_all(["div", "span"]):
        text = tag.get_text(strip=True)

        if len(text) == 5 and ":" in text:
            current_time = text

        elif current_time and len(text) > 2:
            programmes.append((current_time, text))
            current_time = None

    return programmes


def build_xml(all_programmes):
    now = datetime.now()

    # FIX broadcast day (Alpha αλλάζει στις 06:00)
    if now.hour < 6:
        base_date = now - timedelta(days=1)
    else:
        base_date = now

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    current_day = 0
    last_hour = 0

    for i, (time_str, title) in enumerate(all_programmes):

        h, m = map(int, time_str.split(":"))

        # Αν η ώρα πάει πίσω → επόμενη μέρα
        if h < last_hour:
            current_day += 1

        start_dt = base_date.replace(hour=h, minute=m, second=0) + timedelta(days=current_day)

        if i < len(all_programmes) - 1:
            nh, nm = map(int, all_programmes[i + 1][0].split(":"))
            next_day = current_day

            if nh < h:
                next_day += 1

            stop_dt = base_date.replace(hour=nh, minute=nm, second=0) + timedelta(days=next_day)
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

    # 👉 πάρε 2 μέρες
    for _ in range(2):
        html = fetch_day_html(driver)
        programmes = parse(html)
        all_programmes.extend(programmes)

        if not click_next_day(driver):
            break

    driver.quit()

    build_xml(all_programmes)


if __name__ == "__main__":
    main()
