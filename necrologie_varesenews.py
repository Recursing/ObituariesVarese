import csv
import datetime
import urllib.request
from collections import Counter
from multiprocessing.pool import Pool
from typing import Tuple, List

from bs4 import BeautifulSoup

data_file = "/var/www/html/necrologi-varese/data.csv"

opener = urllib.request.build_opener()
opener.addheaders = [("User-agent", "Mozilla/5.0")]
urllib.request.install_opener(opener)


def http_get(url: str) -> bytes:
    return urllib.request.urlopen(url).read()


def get_page(d: int) -> bytes:
    return http_get(f"http://necrologie.varesenews.it/?page={d}")


def get_urls(page: bytes) -> List[str]:
    soup = BeautifulSoup(page, "lxml")
    return [
        e("a")[0]["href"]
        for e in soup("li")
        if e("a")
        and e("a")[0]["href"].startswith(
            "http://necrologie.varesenews.it/annuncio-famiglia/"
        )
    ]


def get_date(page: bytes) -> str:
    soup = BeautifulSoup(page, "lxml")
    date = soup(class_="city-date")[0].text.strip().split("\t")[-1]
    return date


def formatted_date(date_str: str) -> str:
    day, month, year = date_str.split()
    months = [
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    ]
    month_num = months.index(month) + 1
    date = datetime.date(int(year), month_num, int(day))
    return date.strftime("%Y-%m-%d")


def main():
    try:
        with open(data_file, "r") as csv_data:
            data = list(csv.DictReader(csv_data))
            cached_days = [d["day"] for d in data if d["year"] == "2020"]
            last_complete_day = f"2020-{sorted(cached_days)[-5]}"
    except (FileNotFoundError, IndexError, UnicodeDecodeError) as e:
        print(f"{e!r}")
        data = []
        last_complete_day = "2016-01-01"

    print(f"{last_complete_day=}")

    with Pool(20) as pool:
        saved_urls = set()
        deaths_per_day = Counter()
        for page_num in range(1, 665):
            print(f"Parsing page {page_num}")
            page = get_page(page_num)
            new_urls = {url for url in get_urls(page) if url not in saved_urls}
            saved_urls |= new_urls
            obituaries = pool.map(http_get, new_urls)
            dates = pool.map(get_date, obituaries)
            dates = [formatted_date(date) for date in dates]
            deaths_per_day += Counter(dates)
            print(deaths_per_day)
            if max(dates) < last_complete_day:
                break
            print(f"{max(dates)} > {last_complete_day}")

    for d in data:
        year = d["year"]
        day = d["day"]
        obituaries = int(d["obituaries"])
        date_str = f"{year}-{day}"
        deaths_per_day[date_str] = max(deaths_per_day[date_str], obituaries)

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
