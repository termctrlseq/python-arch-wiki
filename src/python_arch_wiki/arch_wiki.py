import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from rich.console import Console
from rich.table import Table

# use Console() for paging, style privides default text color
console = Console(style="color(248)")
# set less as pager
os.environ["MANPAGER"] = "less --raw-control-chars --mouse"


def print_text(text: str) -> None:
    text = re.sub(
        r"(^|:)(\s*[#\$])(\s*\S+)",
        r"\1[bold][green]\2[/][bright_white]\3[/][/]",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"(\s-[\w-]+\b)",
        r"[bold color(103)]\1[/]",
        text,
    )
    text = re.sub(
        r"^([A-Z][\w\s-]+)(:)$",
        r"[color(74)]\1[/]\2",
        text,
        flags=re.MULTILINE,
    )
    console.print(text)


def display_section(section: Tag | None) -> None:
    """Print tag contents."""
    for tag in section.children:  # type: ignore
        tag: Tag
        if not tag.name:
            continue
        elif tag.name == "div" and tag.has_attr("class"):
            if "archwiki-template-box" in tag.attrs["class"]:
                print_text(tag.get_text())
            elif "mw-heading" in tag.attrs["class"]:
                console.rule(
                    f"[bold color(73)]{tag.get_text()}[/]",
                    style="color(73)",
                )
            else:
                display_section(tag)
        elif tag.name == "table":
            caption = tag.find("caption")
            title = caption.get_text() if caption else None
            table = Table(title=title, highlight=True)
            rows = tag("tr")
            for heading in rows[0]("th"):  # type: ignore
                table.add_column(heading.get_text())
            for row in rows[1:]:
                entries = []
                for column in row("td"):  # type: ignore
                    entries.append(column.get_text())
                table.add_row(*entries)
            console.print(table)
        else:
            print_text(tag.get_text())


def main() -> None:
    url = ["https://wiki.archlinux.org", "title"]

    # check script arguments
    if len(sys.argv) > 1:
        # try to open specified article
        url.append("_".join(sys.argv[1:]))
    else:
        # open table of contents
        url.append("Installation_guide")

    try:
        # get rid of any extra slashes and get the webpage
        r = requests.get("/".join(part.strip("/") for part in url), timeout=1)
        # check the status of a response
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        sys.exit(f"{e}")

    # parse webpage with BeautifulSoup object
    soup = BeautifulSoup(r.text, "lxml")

    with console.pager(styles=True):
        display_section(soup.select_one("#bodyContent"))


if __name__ == "__main__":
    main()
