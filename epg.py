from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

URL = "https://www.alphacyprus.com.cy/program"


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=options)


def fetch_html():
    driver = get_driver()
    driver.get(URL)
    time.sleep(5)  # αφήνουμε να φορτώσει JS

    html = driver.page_source
    driver.quit()

    return html


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


def build_xml(programmes):
    now = datetime.now()

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    for i, (time_str, title) in enumerate(programmes):

        h, m = map(int, time_str.split(":"))
        start_dt = now.replace(hour=h, minute=m, second=0)

        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            stop_dt = now.replace(hour=nh, minute=nm, second=0)

            if stop_dt <= start_dt:
                stop_dt += timedelta(days=1)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")

        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"<title>{title}</title>\n"
        xml += "</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    html = fetch_html()
    programmes = parse(html)
    build_xml(programmes)


if __name__ == "__main__":
    main()
