import logging
from pathlib import Path

from autocommand import autocommand
from platformdirs import user_log_dir

from .menu import CursesMenu
from .toc import Toc


def run(args, link_url) -> None:
    toc = Toc(link_url=link_url)
    if len(args) > 0:
        article = "/title/" + "_".join(args)
        toc.display_contents(article)
    else:
        with CursesMenu(toc) as menu:
            result = None
            while result is None:
                menu.display_menu()
                result = menu.handle_input()


def setup_logging(verbose=False) -> None:
    app_name = "python-arch-wiki"
    log_dir = Path(user_log_dir(app_name))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{app_name}.log"

    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        encoding="utf-8",
        level=logging.DEBUG if verbose else logging.WARNING,
        force=True,
    )


@autocommand(__name__)
def main(link_url=False, verbose=False, *article) -> None:
    setup_logging(verbose)
    run(article, link_url)


if __name__ == "__main__":
    main()
