import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BASE_URL = "https://www.alphacyprus.com.cy/program"

def get_day_schedule():
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    programmes = []

    items = soup.find_all("div")

    times = soup.find_all(string=True)

    current_time = None

    for tag in soup.find_all(["div", "span"]):
        text = tag.get_text(strip=True)

        # ώρα μορφή 06:00
        if len(text) == 5 and ":" in text:
            current_time = text

        # τίτλος εκπομπής
        elif current_time and len(text) > 2:
            programmes.append((current_time, text))
            current_time = None

    return programmes


def build_xml():
    programmes = get_day_schedule()

    now = datetime.now()

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    for i, (time_str, title) in enumerate(programmes):
        start_dt = datetime.strptime(time_str, "%H:%M")
        start_dt = now.replace(hour=start_dt.hour, minute=start_dt.minute, second=0)

        if i < len(programmes) - 1:
            next_time = programmes[i + 1][0]
            stop_dt = datetime.strptime(next_time, "%H:%M")
            stop_dt = now.replace(hour=stop_dt.hour, minute=stop_dt.minute, second=0)
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


if __name__ == "__main__":
    build_xml()
