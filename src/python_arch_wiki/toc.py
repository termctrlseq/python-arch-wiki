import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from rich.console import Console
from rich.table import Table

# use Console() for paging, default text color 248
console = Console(style="color(248)")
# set less as pager
os.environ["MANPAGER"] = "less --raw-control-chars --mouse"


class Toc:
    """Arch wiki table of contents."""

    root_url = "https://wiki.archlinux.org"
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
            for i in range(3):
                try:
                    r = self.toc_session.get(
                        self._url_from_parts(
                            [self.root_url, "/title/Table_of_contents"]
                        ),
                        timeout=2,
                    )
                    r.raise_for_status()

                    soup = BeautifulSoup(r.text, "lxml")
                    rows = soup.select_one("#wiki-scripts-toc-table").select(  # type: ignore
                        "tr"
                    )
                    section = rows[0]
                    for row in rows[1:]:
                        self.add_subsection(row, folded=folded)

                    break

                except ConnectionResetError:
                    time.sleep(0.5 * (i + 1))
                    continue
                except requests.exceptions.RequestException as e:
                    self.toc_session.close()
                    sys.exit(f"{e}")

        if isinstance(section, tuple):
            self.section, self.title, self.href, self.num_articles = section
        elif isinstance(section, Tag):
            self.section, self.title, self.href, self.num_articles = (
                self.parse_tag(section)
            )

        self.folded = folded if self.section else False

    def close(self) -> None:
        """Close session."""
        self.toc_session.close()

    def add_subsection(self, tag, folded=False) -> None:
        """Add a subsection to table of contents."""
        subsection = self.parse_tag(tag)
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

    @staticmethod
    def _url_from_parts(parts: list) -> str:
        return "/".join(part.strip("/") for part in parts)

    def get_submenu(self, section: tuple[int, ...]) -> list:
        """Return list of articles."""
        subsection = self
        for i in section:
            subsection = subsection.subsections[i - 1]

        if not subsection.articles:
            try:
                with self.toc_session.get(
                    self._url_from_parts([self.root_url, subsection.href]),
                    timeout=2,
                ) as r:
                    r.raise_for_status()

                    soup = BeautifulSoup(r.text, "lxml")
                    categories = soup.select_one(".mw-category")
                    if categories:
                        for atag in categories.select("a"):
                            subsection.articles.append(
                                [atag["href"], atag["title"]]
                            )

            except requests.exceptions.RequestException as e:
                self.toc_session.close()
                sys.exit(f"{e}")

        return subsection.articles

    @staticmethod
    def _print_text(text: str) -> None:
        # Command
        text = re.sub(
            r"(^|:\s)([#\$])(\s\S+)",
            r"\1[bold][green]\2[/][bright_white]\3[/]",
            text,
            flags=re.MULTILINE,
        )
        # Option
        text = re.sub(
            r"(\s-[\w-]+\b)",
            r"[bold color(103)]\1[/]",
            text,
        )
        # Header
        text = re.sub(
            r"^([A-Z][\w\s-]+)(:)$",
            r"[color(74)]\1[/]\2",
            text,
            flags=re.MULTILINE,
        )
        console.print(text)

    @staticmethod
    def _display_section(section: Tag | None) -> None:
        """Print tag contents."""
        if section is None:
            return

        for tag in section.children:  # type: ignore
            tag: Tag
            if tag.name is None:
                continue
            for code in tag("code"):
                code.string = f"[bold white]{code.get_text()}[/]"
            if "mw-heading" in tag.get_attribute_list("class"):
                console.rule(f"[color(73)]{tag.get_text()}[/]")
            elif "archwiki-template-box" in tag.get_attribute_list("class"):
                text = tag.strong.string.extract()  # type: ignore
                color = "bold"
                if text == "Tip":
                    color += " green"
                elif text == "Note":
                    color += " blue"
                elif text == "Warning":
                    color += " yellow"
                Toc._print_text(f"[{color}]{text}:[/]{tag.get_text()}\n")
            elif "archwiki-template-message" in tag.get_attribute_list(
                "class"
            ):
                Toc._print_text(tag.get_text())
            elif tag.name == "div":
                Toc._display_section(tag)
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
                Toc._print_text(tag.get_text())

    @classmethod
    def display_contents(cls, href: str) -> None:
        """Display article."""
        try:
            with cls.toc_session.get(
                cls._url_from_parts([cls.root_url, href]),
                timeout=1,
            ) as r:
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "lxml")

        except requests.exceptions.RequestException as e:
            cls.toc_session.close()
            sys.exit(f"{e}")

        with console.pager(styles=True):
            cls._display_section(soup.select_one("#bodyContent"))

    def search(self, text: str) -> list:
        """Search arch wiki."""
        search_text = text.strip().replace(" ", "+")
        payload = {
            "search": search_text,
            "title": "Special%3ASearch",
            "profile": "default",
            "fulltext": "1",
        }
        try:
            with self.toc_session.get(
                self._url_from_parts([self.root_url, "index.php"]),
                params=payload,
                timeout=1,
            ) as r:
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "lxml")
        except requests.exceptions.RequestException as e:
            self.toc_session.close()
            sys.exit(f"{e}")

        results = []
        for tag in soup.select(".mw-search-result"):
            heading = tag.find(class_="mw-search-result-heading")
            results.append([heading.a["href"], heading.a["title"]])  # type: ignore

        return results


def main() -> None:
    toc = Toc(folded=False)

    print(toc.get_submenu((1, 1)))
    toc.close()


if __name__ == "__main__":
    main()
