import json
import string
import sys
import textwrap
from argparse import ArgumentParser, FileType
from concurrent import futures
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import imdb

IA = imdb.IMDb()


BASE = Path(__file__).parent

TEMPLATES = BASE / "templates"
CARD_TEMPLATE = string.Template((TEMPLATES / "card.html").read_text())
BASE_TEMPLATE = string.Template((TEMPLATES / "base.html").read_text())

INDENT = " " * 4


@dataclass(order=True)
class Show:
    index: str = field(compare=False, repr=False)
    title: str = field(compare=False)
    rating: int = field(compare=True)
    rewatch: int = field(compare=True)
    image_url: Optional[int] = None

    to_json = asdict

    @classmethod
    def from_json(cls, json_object):
        return cls(**json_object)

    def annotate(self):
        if self.image_url:
            return None

        show = IA.get_movie(self.index[2:], ["main"])
        self.image_url = show.get("full-size cover url")

    def render(self):
        return CARD_TEMPLATE.safe_substitute(
            title=self.title,
            image=self.image_url,
            watches=self.rewatch,
            rating=self.rating,
        )


def annotate_shows(shows, dump_to=None):
    with futures.ThreadPoolExecutor(max_workers=16) as executor:
        tasks = [executor.submit(show.annotate) for show in shows]
        total = len(tasks)
        for current, future in enumerate(futures.as_completed(tasks)):
            future.result()
            print(f"{current}/{total}", end="\r")
    print(f"{total}/{total} show metadata fetched")


def render(shows, grid_size=4):
    for chunk_start in range(0, len(shows), grid_size):
        yield '<div class="mdl-grid centered">'
        for show in shows[chunk_start : chunk_start + grid_size]:
            yield textwrap.indent(show.render(), INDENT)
        yield "</div>"


def generate(input_file):
    with open(input_file) as stream:
        shows = json.load(stream, object_hook=Show.from_json)

    annotate_shows(shows, dump_to=input_file)
    with open(input_file, "w") as stream:
        json.dump([show.to_json() for show in shows], stream, indent=4)

    shows.sort(reverse=True)
    cards = "\n".join(render(shows))
    return BASE_TEMPLATE.safe_substitute(
        cards=textwrap.indent(cards, INDENT * 4)
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument(
        "output_file", type=FileType("w"), default=sys.stdout, nargs="?"
    )

    options = parser.parse_args()
    options.output_file.write(generate(options.input_file))


if __name__ == "__main__":
    main()
