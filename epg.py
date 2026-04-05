import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BASE_URL = "https://www.alphacyprus.com.cy/program"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_page():
    r = requests.get(BASE_URL, headers=HEADERS)
    return BeautifulSoup(r.text, "html.parser")


def parse_days(soup):
    days_data = []

    # βρίσκουμε sections ημέρας
    sections = soup.find_all("section")

    for section in sections:
        items = section.find_all(["div", "li"])

        day_program = []
        current_time = None

        for item in items:
            text = item.get_text(strip=True)

            # ώρα
            if len(text) == 5 and ":" in text:
                current_time = text

            # τίτλος
            elif current_time and len(text) > 2:
                day_program.append((current_time, text))
                current_time = None

        if len(day_program) > 5:
            days_data.append(day_program)

    return days_data[:3]  # μόνο 3 μέρες


def build_xml(days):
    now = datetime.now()

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    for d, programmes in enumerate(days):
        base_date = now + timedelta(days=d)

        for i, (time_str, title) in enumerate(programmes):

            start_time = datetime.strptime(time_str, "%H:%M")
            start_dt = base_date.replace(
                hour=start_time.hour,
                minute=start_time.minute,
                second=0,
                microsecond=0
            )

            # stop time
            if i < len(programmes) - 1:
                next_time = datetime.strptime(programmes[i + 1][0], "%H:%M")
                stop_dt = base_date.replace(
                    hour=next_time.hour,
                    minute=next_time.minute,
                    second=0,
                    microsecond=0
                )

                # FIX για μετά τα μεσάνυχτα
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
    soup = fetch_page()
    days = parse_days(soup)
    build_xml(days)


if __name__ == "__main__":
    main()
