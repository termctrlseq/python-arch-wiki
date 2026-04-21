import sys

from .menu import CursesMenu
from .toc import Toc


def main() -> None:
    toc = Toc()
    if len(sys.argv) > 1:
        article = "/title/" + "_".join(sys.argv[1:])
        toc.display_contents(article)
    else:
        with CursesMenu(toc) as menu:
            while True:
                menu.display_menu()
                menu.handle_input()

    toc.close()


if __name__ == "__main__":
    main()
