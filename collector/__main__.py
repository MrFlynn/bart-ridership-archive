#!/usr/bin/env python3
#
# Parses ridership data tables on BART's (Bay Area Rapid Transit) website and
# saves them to a JSON file.

import json
import re
import requests

from bs4 import BeautifulSoup, element
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from typing import Iterator, List, Mapping, Tuple

RIDERSHIP_DATA_URL = "https://www.bart.gov/news/articles/2020/news20200225"


class Percentage(Enum):
    Invalid = auto()
    OfBaseline = auto()
    BelowBaseline = auto()

    @classmethod
    def from_string(cls, s: str) -> "Percentage":
        if re.match(r"% below baseline", s, re.IGNORECASE):
            return cls.BelowBaseline
        elif re.match(r"% of baseline", s, re.IGNORECASE) or re.match(
            r"% of pre-pandemic", s, re.IGNORECASE
        ):
            return cls.OfBaseline
        else:
            return cls.Invalid

    @classmethod
    def from_table_headers(cls, ti: Iterator[element.Tag]) -> "Percentage":
        try:
            _ = next(ti)  # Ignore first row
            header_row = next(ti)

            for column in header_row.children:
                if (t := cls.from_string(column.text)) != cls.Invalid:
                    return t
        except StopIteration:
            pass

        return cls.Invalid


@dataclass
class DayRidership:
    date: str = ""
    riders: str = ""
    percent_baseline: str = ""
    percent_type: Percentage = Percentage.OfBaseline

    _riders: int = 0
    _percent_baseline: int = 0
    _valid: bool = False

    def __post_init__(self):
        self._valid = all(
            [
                self._validate_date(),
                self._extract_ridership(),
                self._extract_baseline_percent(),
            ]
        )

    def _validate_date(self) -> bool:
        try:
            datetime.strptime(self.date, "%m/%d/%y")
            return True
        except ValueError:
            pass

        return False

    def _extract_ridership(self) -> bool:
        try:
            if (
                riders_matcher := re.match(r"((\d{1,3})?,?(\d{1,3}))", self.riders)
            ) != None:
                self._riders = int(re.sub(r",", "", riders_matcher.group(1)))

                return True
        except ValueError:
            pass

        return False

    def _extract_baseline_percent(self) -> bool:
        try:
            if (
                percent_matcher := re.match(r"-?(\d+)%?", self.percent_baseline)
            ) != None:
                value = int(percent_matcher.group(1))

                if self.percent_type == Percentage.BelowBaseline:
                    self._percent_baseline = 100 - value
                else:
                    self._percent_baseline = value

                return True
        except ValueError:
            pass

        return False

    @property
    def valid(self) -> bool:
        return self._valid

    def to_dict(self) -> Tuple[str, Mapping[str, int]]:
        return self.date, {
            "riders": self._riders,
            "percent_baseline": self._percent_baseline,
        }


def get_ridership_from_rows(
    rows: Iterator[element.Tag], percent_type: Percentage
) -> Iterator[DayRidership]:
    for row in rows:
        columns = list(row.children)

        if len(columns) % 3 != 0:
            continue

        for i in range(0, len(columns), 3):
            yield DayRidership(
                date=columns[i].text.strip(),
                riders=columns[i + 1].text.strip(),
                percent_baseline=columns[i + 2].text.strip(),
                percent_type=percent_type,
            )


def parse_tables(content: str) -> Iterator[DayRidership]:
    parser = BeautifulSoup(content, "html.parser")

    for table in parser.find_all("table"):
        table_body_list = list(filter(lambda e: e.name == "tbody", table.children))
        percentage_type = Percentage.Invalid
        data: Iterator[element.Tag] = iter(())

        if len(table_body_list) == 1:
            data = iter(table_body_list[0])
            percentage_type = Percentage.from_table_headers(data)
        elif len(table_body_list) == 2:
            headers, data = iter(table_body_list[0]), iter(table_body_list[1])
            percentage_type = Percentage.from_table_headers(headers)

        if percentage_type != Percentage.Invalid:
            yield from get_ridership_from_rows(data, percentage_type)


def main():
    content = requests.get(RIDERSHIP_DATA_URL)

    ridership = {}
    for day_ridership in parse_tables(content.text):
        if day_ridership.valid:
            ridership.setdefault(*day_ridership.to_dict())

    ridership = OrderedDict(sorted(ridership.items()))

    with open("ridership.json", "w+") as f:
        f.seek(0)
        json.dump(ridership, f)
        f.truncate()


if __name__ == "__main__":
    main()
