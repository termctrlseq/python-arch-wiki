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


class Toc:
    """Arch wiki table of contents."""

    home_url = "https://wiki.archlinux.org"
    toc_session = requests.Session()

    section: tuple | None
    title: str
    href: str
    articles: list
    num_articles: int
    subsections: list["Toc"]
    folded: bool

    def __init__(
        self,
        section: Tag
        | tuple[tuple[int, ...] | None, str, str, int]
        | None = None,
        folded=True,
    ) -> None:
        """Initialize Toc section."""
        self.subsections = []
        self.articles = []

        if not section:
            try:
                r = Toc.toc_session.get(
                    self._url_from_parts("/title/Table_of_contents"),
                    timeout=2,
                )
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                sys.exit(f"{e}")

            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.select_one("#wiki-scripts-toc-table").select("tr")  # type: ignore
            section = rows[0]
            for row in rows[1:]:
                self.add_subsection(row, folded=folded)

        self.section, self.title, self.href, self.num_articles = (
            self.parse_tag(section) if isinstance(section, Tag) else section
        )
        self.folded = folded if self.section else False

    def add_subsection(self, tag, folded=False) -> None:
        """Add a subsection to table of contents."""
        subsection = self.parse_tag(tag)
        # if not subsection[0]:
        #     raise AttributeError("Can not add subsection without section")
        assert subsection[0], "Can not add subsection without section"

        # create a nested structure using section as a tuple of indices
        parent = self
        for i in subsection[0][:-1]:
            parent = parent.subsections[i - 1]
        parent.subsections.append(Toc(subsection, folded=folded))

    def parse_tag(
        self, trtag: Tag
    ) -> tuple[tuple[int, ...] | None, str, str, int]:
        """Extract section info from tr tag into a tuple."""
        assert trtag
        atag = trtag.find("a") if trtag else None
        if atag is None:
            raise ValueError("'a' tag not found")

        title = atag.string
        href = str(atag["href"])
        try:
            section = tuple(
                int(x)
                for x in atag.find_previous_sibling("small")
                .get_text()  # type: ignore
                .strip(".")
                .split(".")
            )
        except (AttributeError, ValueError):
            section = None
        try:
            num_articles = int(
                atag.find_next_sibling("small")
                .get_text()  # type: ignore
                .strip("()")
            )
        except (AttributeError, ValueError):
            num_articles = 0

        if not title or not href:
            raise ValueError(f"Failed to parse tag: {atag}")
        else:
            return section, title, href, num_articles

    def get_entries(
        self,
        section: "Toc | None" = None,
        toc_list: list[tuple[tuple, str]] | None = None,
    ) -> list[tuple[tuple, str]]:
        """Return a list of section/title tuples."""
        if section is None:
            section = self
        if toc_list is None:
            toc_list = []

        if section.section:
            section_str = (
                f"{' ' * 4 * (len(section.section) - 1)}"
                f"{section.section[-1]:>2}. "
            )

            if section.num_articles:
                num_art_str = f" ({section.num_articles})"
            else:
                num_art_str = ""

            if section.folded and section.subsections:
                subsect_str = f" *{len(section.subsections)}"
            else:
                subsect_str = ""

            toc_list.append(
                (
                    section.section,
                    f"{section_str}{section.title}{num_art_str}{subsect_str}",
                )
            )

        if section.subsections and not section.folded:
            for subsection in section.subsections:
                self.get_entries(subsection, toc_list)

        return toc_list

    def __iter__(self):
        """Return Toc generator."""
        yield from self.get_entries()

    def fold(self, section: tuple[int] | str) -> None:
        """Toggle displaying subsections."""

        if isinstance(section, tuple):
            subsection = self
            for i in section:
                subsection = subsection.subsections[i - 1]
            subsection.folded = not subsection.folded

    def _url_from_parts(self, href: list | str) -> str:
        url_list = [Toc.home_url]
        if isinstance(href, list):
            url_list.extend(href)
        else:
            url_list.append(href)
        return "/".join(part.strip("/") for part in url_list)

    def get_submenu(self, section: tuple[int, ...]):
        subsection = self
        for i in section:
            subsection = subsection.subsections[i - 1]

        if not subsection.articles:
            try:
                r = Toc.toc_session.get(
                    self._url_from_parts(subsection.href), timeout=2
                )
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                sys.exit(f"{e}")

            soup = BeautifulSoup(r.text, "lxml")
            categories = soup.select_one(".mw-category")
            if categories:
                for atag in categories.select("a"):
                    subsection.articles.append([atag["href"], atag["title"]])

        return subsection.articles

    def _print_text(self, text: str) -> None:
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

    def _display_section(self, section: Tag | None) -> None:
        """Print tag contents."""
        for tag in section.children:  # type: ignore
            tag: Tag
            if tag.name is None:
                continue
            elif re.match(r"^h\d+", tag.name):
                console.rule(f"[color(73)]{tag.get_text()}[/]")
            elif tag.name == "div" and tag.has_attr("class"):
                if "archwiki-template-box" in tag.attrs["class"]:
                    self._print_text(tag.get_text())
                else:
                    self._display_section(tag)
            elif tag.name == "div":
                self._display_section(tag)
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
                self._print_text(tag.get_text())

    def display_contents(self, href: str) -> None:
        try:
            r = Toc.toc_session.get(
                self._url_from_parts(href),
                timeout=1,
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            sys.exit(f"{e}")

        soup = BeautifulSoup(r.text, "lxml")

        with console.pager(styles=True):
            self._display_section(soup.select_one("#bodyContent"))


def main() -> None:
    toc = Toc(folded=False)

    # for _, line in toc:
    #     print(line)
    print(toc.get_submenu((1, 1)))


if __name__ == "__main__":
    main()
