#!/usr/bin/env python

import csv
import sys
import json
from argparse import ArgumentParser, FileType


def generate_shows(input_file):
    shows = []
    with open(input_file, "r", encoding="latin1") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            shows.append(
                {
                    "index": row["Const"],
                    "title": row["Title"],
                    "rating": int(row["Your Rating"]),
                }
            )

    shows.sort(key=lambda item: -item["rating"])
    return shows


def main():
    parser = ArgumentParser()
    parser.add_argument("input_file", help="Exported IMDB show ratings")
    parser.add_argument(
        "output_file", type=FileType("w"), default=sys.stdout, nargs="?"
    )

    options = parser.parse_args()
    json.dump(
        generate_shows(options.input_file), options.output_file, indent=4
    )


if __name__ == "__main__":
    main()
