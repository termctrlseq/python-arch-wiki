import curses
import logging
import os
import signal
import sys
from curses.textpad import Textbox, rectangle
from subprocess import run

logger = logging.getLogger(__name__)


class EditError(Exception):
    pass


class CursesMenu:
    def __init__(self, menu) -> None:
        self._width, self._height = os.get_terminal_size()
        self.menu = menu
        self.contents = [
            [line] if isinstance(line, str) else line for line in self.menu
        ]
        self._selected = 0
        self._start_idx = 0
        self._stop_idx = self._start_idx + self._height
        self._saved_state = None
        self._start_curses()
        signal.signal(signal.SIGWINCH, self._signal_win_resize)

    def _start_curses(self) -> None:
        try:
            self._stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self._stdscr.keypad(True)
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(10, 1, -1)
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
            curses.set_escdelay(50)

        except Exception as e:
            run("reset")
            sys.exit(f"{e}")

    def _end_curses(self) -> None:
        self._stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_curses()
        return False

    def display_menu(self) -> None:
        """Display menu."""
        for i, item in enumerate(
            self.contents[self._start_idx : self._stop_idx],
            start=self._start_idx,
        ):
            if i == self._selected:
                self._stdscr.addstr(
                    i - self._start_idx, 0, f"> {item[-1]}", curses.A_BOLD
                )
            else:
                self._stdscr.addstr(i - self._start_idx, 0, f"  {item[-1]}")
            self._stdscr.clrtoeol()

        self._stdscr.clrtobot()
        self._stdscr.refresh()

    def _previous(self) -> None:
        if self._selected > 0:
            self._selected -= 1

            if self._selected < self._start_idx:
                self._start_idx -= 1
                self._stop_idx -= 1

    def _next(self) -> None:
        if self._selected < len(self.contents) - 1:
            self._selected += 1

            if self._selected > self._stop_idx - 1 and self._stop_idx < len(
                self.contents
            ):
                self._start_idx += 1
                self._stop_idx += 1

    def _fold(self, up_level: bool = False) -> None:
        """(Un)fold submenu."""
        if hasattr(self.menu, "fold"):
            section = self.contents[self._selected][0]
            logger.debug("Fold: selected = %s", self._selected)

            if up_level:
                if len(section) > 1:
                    self.menu.fold(section[:-1])

                    for i, sect in enumerate(self.contents):
                        if sect[0] == section[:-1]:
                            self._selected = i

            else:
                self.menu.fold(section)

            old_contents_len = len(self.contents)

            self.contents = [
                [line] if isinstance(line, str) else line
                for line in self.menu
            ]

            self._restore_state()

            contents_len = len(self.contents)
            if self._selected > contents_len - 1:
                self._selected = contents_len - 1

            if contents_len > old_contents_len:
                self._stop_idx += max(
                    0,
                    contents_len
                    - old_contents_len
                    - self._stop_idx
                    + self._selected
                    + 1,
                )
                self._start_idx = max(0, self._stop_idx - self._height)

            if contents_len <= self._height:
                self._start_idx = 0
                self._stop_idx = self._height
            elif self._height > (contents_len - self._start_idx):
                self._start_idx = contents_len - self._height
                self._stop_idx = contents_len

            if self._selected < self._start_idx:
                self._start_idx = self._selected
                self._stop_idx = self._start_idx + self._height

            if self._selected > self._stop_idx:
                self._stop_idx = self._selected
                self._start_idx = max(0, self._stop_idx - self._height)

    def _get_contents(self) -> None:
        """Get contents of menu item."""
        selected = self.contents[self._selected][0]

        if isinstance(selected, tuple):
            self._save_state()
            self.contents = self.menu.get_submenu(selected)

        elif hasattr(self.menu, "display_contents"):
            self._end_curses()
            self.menu.display_contents(selected)
            self._start_curses()

    def handle_input(self) -> str | tuple | None:
        """Handle keyboard and mouse events."""
        key = self._stdscr.getch()

        # Up arrow, Ctrl-p, Shift-TAB
        if key in [curses.KEY_UP, 16, curses.KEY_BTAB, ord("k")]:
            self._previous()

        # Down arrow, Ctrl-n, TAB
        elif key in [curses.KEY_DOWN, 14, ord("\t"), ord("j")]:
            self._next()

        elif key == ord("H"):
            self._selected = self._start_idx

        elif key == ord("M"):
            stop = min(self._stop_idx, len(self.contents))
            self._selected = self._start_idx + (stop - self._start_idx) // 2

        elif key == ord("L"):
            self._selected = min(self._stop_idx, len(self.contents)) - 1

        # Enter
        elif key == ord("\n"):
            self._get_contents()

        # Space or l
        elif key in [ord(" "), ord("l")]:
            self._fold()

        # u, h, Escape
        elif key in [ord("u"), ord("h"), 27]:
            self._fold(up_level=True)

        # Ctrl-d, q
        elif key in [4, ord("q")]:
            sys.exit()

        # slash
        elif key == ord("/"):
            self._search()

        elif key == curses.KEY_MOUSE:
            try:
                _, _, y, _, bstate = curses.getmouse()
                # Left click
                if (
                    bstate & curses.BUTTON1_CLICKED
                    and y + self._start_idx < len(self.contents)
                ):
                    self._selected = y + self._start_idx

                # Double click
                elif (
                    bstate & curses.BUTTON1_DOUBLE_CLICKED
                    and y + self._start_idx < len(self.contents)
                ):
                    self._selected = y + self._start_idx
                    self._get_contents()

                # Right click
                elif (
                    bstate & curses.BUTTON3_CLICKED
                    and y + self._start_idx < len(self.contents)
                ):
                    self._selected = y + self._start_idx
                    self._fold()

                # Mouse wheel up
                elif bstate & curses.BUTTON4_PRESSED:
                    self._previous()

                # Mouse wheel down
                elif bstate & curses.BUTTON5_PRESSED:
                    self._next()

            except curses.error:
                # Display msg in the middle of the screen
                msg = "  Error handling mouse event.  "
                border = " " * len(msg)
                line = self._height // 2
                column = (self._width - len(msg)) // 2
                self._stdscr.addstr(line - 1, column, border)
                self._stdscr.addstr(
                    line,
                    column,
                    msg,
                    curses.color_pair(10),
                )
                self._stdscr.addstr(line + 1, column, border)

    def _signal_win_resize(self, signum, stack_frame) -> None:  # noqa: ARG002
        """Handle SIGWINCH signal (resize window)."""
        self._width, self._height = os.get_terminal_size()

        if self._start_idx > self._selected:
            self._start_idx = self._selected + 1

        self._stop_idx = self._start_idx + self._height

        if self._stop_idx < self._selected + 1:
            self._stop_idx = self._selected + 1
            self._start_idx = max(0, self._stop_idx - self._height)

        self._stdscr.clear()
        self._stdscr.refresh()
        self.display_menu()

    def _save_state(self):
        self._saved_state = self._start_idx, self._stop_idx, self._selected
        self._start_idx = 0
        self._stop_idx = self._height
        self._selected = 0

    def _restore_state(self):
        if self._saved_state:
            self._start_idx, self._stop_idx, self._selected = (
                self._saved_state
            )
            self._saved_state = None

    @staticmethod
    def validator(ch):
        if ch == 27:
            raise EditError

        return ch

    def _search(self):
        max_y, max_x = self._stdscr.getmaxyx()
        uly, ulx = max_y // 2, max_x // 4
        height, width = 1, curses.COLS // 2
        prompt = " Search: "
        plen = len(prompt)
        self._stdscr.addstr(uly, ulx, prompt)

        search_win = curses.newwin(height, width - plen, uly, ulx + plen)
        rectangle(
            self._stdscr, uly - 1, ulx - 1, uly + height, ulx + width + 1
        )
        search_win.clear()
        self._stdscr.refresh()

        box = Textbox(search_win)
        curses.curs_set(1)

        try:
            box.edit(self.validator)
        except EditError:
            return
        finally:
            curses.curs_set(0)

        search_term = box.gather()
        result = self.menu.search(search_term)
        logger.debug("search: %s\n%s", search_term, result)

        if result:
            self.contents = result
            self._save_state()


def main() -> None:
    menu_items = []
    for i in range(50):
        menu_items.append(f"Option_{i}")

    result = None
    with CursesMenu(menu_items) as menu:
        while not result:
            menu.display_menu()
            result = menu.handle_input()

    print(result)


if __name__ == "__main__":
    main()
