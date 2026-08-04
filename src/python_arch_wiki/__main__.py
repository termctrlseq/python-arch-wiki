import logging
import sys
from pathlib import Path

from .menu import CursesMenu
from .toc import Toc

logger = logging.getLogger(__name__)


def run() -> None:
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


def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "wiki.log"
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        encoding="utf-8",
        level=logging.WARNING,
    )


def main() -> None:
    setup_logging()
    run()


if __name__ == "__main__":
    main()
