import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://tvepg.eu/en/cyprus/c/alpha-kuprou"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch():
    r = requests.get(URL, headers=HEADERS)
    return BeautifulSoup(r.text, "html.parser")


def parse_day(day_block):
    lines = day_block.get_text("\n").split("\n")

    programmes = []

    for line in lines:
        line = line.strip()

        if "|" in line:
            try:
                time_part, title = line.split("|", 1)
                time_part = time_part.strip()
                title = title.strip()

                if ":" in time_part:
                    programmes.append((time_part, title))
            except:
                continue

    return programmes


def get_2_days(soup):
    days = []

    blocks = soup.find_all("pre")

    for block in blocks[:2]:
        parsed = parse_day(block)
        if parsed:
            days.append(parsed)

    return days


def build_xml(days):
    now = datetime.now()

    xml = "<?xml version='1.0' encoding='utf-8'?>\n<tv>\n"
    xml += '<channel id="alpha.cy">\n'
    xml += '<display-name>Alpha Cyprus</display-name>\n'
    xml += "</channel>\n"

    for d, programmes in enumerate(days):
        base_date = now + timedelta(days=d)

        for i, (time_str, title) in enumerate(programmes):

            h, m = map(int, time_str.split(":"))

            start_dt = base_date.replace(hour=h, minute=m, second=0)

            if i < len(programmes) - 1:
                nh, nm = map(int, programmes[i + 1][0].split(":"))
                stop_dt = base_date.replace(hour=nh, minute=nm, second=0)

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
    soup = fetch()
    days = get_2_days(soup)
    build_xml(days)


if __name__ == "__main__":
    main()
