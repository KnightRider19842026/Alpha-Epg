import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

URL = "https://www.alphacyprus.com.cy/program"

def clean_title(title):
    # αφαιρεί παρενθέσεις, live now, WEBTV, copyright
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"live now", "", title, flags=re.IGNORECASE)
    title = re.sub(r"Δες όλα τα επεισόδια στο WEBTV", "", title, flags=re.IGNORECASE)
    title = re.sub(r"copyright.*", "", title, flags=re.IGNORECASE)
    # αφαιρεί φράσεις με μέρα + ώρα
    title = re.sub(
        r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ|ΔΕΥΤΕΡΑ|ΤΡΙΤΗ|ΤΕΤΑΡΤΗ|ΠΕΜΠΤΗ|ΠΑΡΑΣΚΕΥΗ|ΣΑΒΒΑΤΟ|ΚΥΡΙΑΚΗ)\s*ΣΤΙΣ\s*\d{1,2}:\d{2}",
        "", title, flags=re.IGNORECASE
    )
    title = re.sub(r"(ΚΑΘΗΜΕΡΙΝΑ|ΣΑΒΒΑΤΟΚΥΡΙΑΚΟ).*?\d{1,2}:\d{2}", "", title, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", title).strip()

def fetch_next_day_programmes():
    resp = requests.get(URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

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

    tomorrow = datetime.now() + timedelta(days=1)
    return programmes, tomorrow

def build_xml(programmes, target_date):
    if not programmes:
        print("❌ Κανένα πρόγραμμα βρέθηκε.")
        return

    base_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    xml += '<channel id="alpha.cy">\n  <display-name>Alpha Cyprus</display-name>\n</channel>\n'

    for i, (time_str, title) in enumerate(programmes):
        h, m = map(int, time_str.split(":"))
        start_dt = base_date + timedelta(hours=h, minutes=m)

        # Ακριβής ώρα λήξης
        if i < len(programmes) - 1:
            nh, nm = map(int, programmes[i + 1][0].split(":"))
            stop_dt = base_date + timedelta(hours=nh, minutes=nm)
        else:
            stop_dt = start_dt + timedelta(minutes=60)

        start = start_dt.strftime("%Y%m%d%H%M%S +0300")
        stop = stop_dt.strftime("%Y%m%d%H%M%S +0300")
        xml += f'<programme channel="alpha.cy" start="{start}" stop="{stop}">\n'
        xml += f"  <title>{title}</title>\n</programme>\n"

    xml += "</tv>"

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ epg.xml δημιουργήθηκε με {len(programmes)} προγράμματα για {target_date.strftime('%A, %d-%m-%Y')}.")

def main():
    programmes, target_date = fetch_next_day_programmes()
    build_xml(programmes, target_date)

if __name__ == "__main__":
    main()
