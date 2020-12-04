import csv
import json
from datetime import date
import datetime
import urllib.request
from collections import defaultdict
from typing import List

from bs4 import BeautifulSoup

data_file = "data.csv"
daily_urls_file = "already_counted.json"

opener = urllib.request.build_opener()
opener.addheaders = [("User-agent", "Mozilla/5.0")]
urllib.request.install_opener(opener)


def http_get(url: str) -> bytes:
    return urllib.request.urlopen(url).read()


def get_page(d: int) -> bytes:
    return http_get(f"https://www.varesenews.it/necrologie/defunti/page/{d}/")


def get_urls(page: bytes) -> List[str]:
    soup = BeautifulSoup(page, "lxml")
    return [
        e["href"]
        for e in soup("a")
        if e["href"].startswith(
            "https://www.varesenews.it/necrologie/annuncio-famiglia/"
        )
    ]


def main():
    with open(data_file, "r") as csv_data:
        data = list(csv.DictReader(csv_data))
    try:
        with open(daily_urls_file, "r") as json_file:
            daily_urls = json.load(json_file)
            last_complete_day = max(daily_urls.values(), default=None)
    except (FileNotFoundError, IndexError, UnicodeDecodeError) as e:
        daily_urls = {}
        last_complete_day = None

    print(f"{last_complete_day=}")

    today = str(date.today())
    new_deaths = 0
    for page_num in range(1, 10):
        print(f"Parsing page {page_num}")
        page = get_page(page_num)
        new_urls = {url: today for url in get_urls(page) if url not in daily_urls}
        if not new_urls:
            break
        new_deaths += len(new_urls)
        daily_urls.update(new_urls)
    with open(daily_urls_file, "w") as of:
        json.dump(daily_urls, of)
    deaths_per_day = defaultdict(float)
    if last_complete_day == today and new_deaths:
        deaths_per_day[today] += new_deaths
    elif last_complete_day is not None and new_deaths:
        d1 = date.fromisoformat(last_complete_day)
        d2 = date.today()
        delta = (d2 - d1).days
        print(f"DAYS DELTA: {delta}")
        for d in range(1, delta + 1):
            day = d1 + datetime.timedelta(d)
            deaths_per_day[str(day)] = new_deaths / delta

    for d in data:
        year = d["year"]
        day = d["day"]
        obituaries = float(d["obituaries"])
        if obituaries == int(obituaries):
            obituaries = int(obituaries)
        date_str = f"{year}-{day}"
        deaths_per_day[date_str] = max(deaths_per_day.get(date_str, 0), obituaries)

    new_data = []
    for date_str, obituaries in deaths_per_day.items():
        year, day = date_str.split("-", 1)
        new_data.append({"year": year, "day": day, "obituaries": obituaries})

    new_data.sort(key=lambda d: f'{d["day"]}-{d["year"]}')

    with open(data_file, "w") as csvfile:
        fieldnames = ["year", "day", "obituaries"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_data)


if __name__ == "__main__":
    main()
