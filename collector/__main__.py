#!/usr/bin/env python3
#
# Parses ridership data tables on BART's (Bay Area Rapid Transit) website and
# saves them to a JSON file.

import json
import re
import requests

from bs4 import BeautifulSoup, element
from collections import OrderedDict
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


class ParseRowError(Exception):
    def __init__(
        self,
        message: str,
        field_name: str,
        row: List[element.PageElement],
    ) -> None:
        super().__init__(message)

        self.message = message
        self.field_name = field_name
        self.row = row

    def __str__(self) -> str:
        return (
            f"Error parsing field {self.field_name} in row {self.row}: {self.message}."
        )


class DayRidership:
    def __init__(
        self,
        row: List[element.PageElement],
        percent_type: Percentage = Percentage.Invalid,
    ) -> None:
        self.date = ""
        self.riders = 0
        self.percent_baseline = 0
        self.percent_type = percent_type

        # Extract fields from row.
        self._get_date(row)
        self._get_ridership(row)
        self._get_percent_baseline(row)

        if self.riders == 0:
            raise ParseRowError("field is zero", "riders", row)

        if self.percent_baseline == 0:
            raise ParseRowError("field is zero", "percent_baseline", row)

    def _get_date(self, row: List[element.PageElement]):
        try:
            self.date = row[0].text.strip()
            _ = datetime.strptime(self.date, "%m/%d/%y")
        except ValueError:
            raise ParseRowError("invalid date format", "date", row)

    def _get_ridership(self, row: List[element.PageElement]):
        try:
            riders_re = re.match(r"((\d{1,3})?,?(\d{1,3}))", row[1].text.strip())
            if riders_re:
                self.riders = int(re.sub(r",", "", riders_re.group(1)))
        except ValueError:
            raise ParseRowError("invalid numerical value for riders", "riders", row)

    def _get_percent_baseline(self, row: List[element.PageElement]):
        try:
            percentage_re = re.match(r"-?(\d+)%?", row[2].text.strip())
            if percentage_re:
                value = int(percentage_re.group(1))
                self.percent_baseline = (
                    100 - value
                    if self.percent_type == Percentage.BelowBaseline
                    else value
                )
        except ValueError:
            raise ParseRowError(
                "invalid numerical value for percentage",
                "percent_baseline",
                row,
            )

    def to_dict(self) -> Tuple[str, Mapping[str, int]]:
        return self.date, {
            "riders": self.riders,
            "percent_baseline": self.percent_baseline,
        }


def get_ridership_from_rows(
    rows: Iterator[element.Tag], percent_type: Percentage
) -> Iterator[DayRidership]:
    for row in rows:
        columns = list(row.children)

        if len(columns) % 3 != 0:
            continue

        for i in range(0, len(columns), 3):
            try:
                yield DayRidership(columns[i : i + 3], percent_type=percent_type)
            except ParseRowError as e:
                print(str(e) + " Skipping...")


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
        ridership.setdefault(*day_ridership.to_dict())

    ridership = OrderedDict(sorted(ridership.items()))

    with open("ridership.json", "w+") as f:
        f.seek(0)
        json.dump(ridership, f)
        f.truncate()


if __name__ == "__main__":
    main()
