import curses
import os
import signal
import sys


class CursesMenu:
    def __init__(self, toc) -> None:
        self._width, self._height = os.get_terminal_size()
        self.toc = toc
        self.contents = [
            [line] if isinstance(line, str) else line for line in self.toc
        ]
        self._selected = 0
        self._start_idx = 0
        self._stop_idx = self._start_idx + self._height
        self._saved_idx = None
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
            curses.init_pair(100, 1, -1)
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
        except Exception as e:
            os.system("reset")
            sys.exit(f"{e}")

    def _end_curses(self) -> None:
        self._stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
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

    def _fold(self) -> None:
        """(Un)fold submenu."""
        if hasattr(self.toc, "fold"):
            self.toc.fold(self.contents[self._selected][0])
            self.contents = [
                [line] if isinstance(line, str) else line for line in self.toc
            ]

    def _get_contents(self) -> None:
        """Get contents of menu item."""
        selected = self.contents[self._selected][0]
        if isinstance(selected, tuple):
            self._save_state()
            self._start_idx = 0
            self._stop_idx = self._height
            self._selected = 0
            self.contents = self.toc.get_submenu(selected)
        elif hasattr(self.toc, "display_contents"):
            self._end_curses()
            self.toc.display_contents(selected)
            self._start_curses()

    def handle_input(self) -> str | tuple | None:
        """Handle keyboard and mouse events."""
        key = self._stdscr.getch()
        # Up arrow, Ctrl-p, Shift-TAB
        if key in [curses.KEY_UP, 16, curses.KEY_BTAB]:
            self._previous()
        # Down arrow, Ctrl-n, TAB
        elif key in [curses.KEY_DOWN, 14, ord("\t")]:
            self._next()
        # Enter
        elif key == ord("\n"):
            self._get_contents()
        elif key == curses.KEY_BACKSPACE:
            self.contents = [
                [line] if isinstance(line, str) else line for line in self.toc
            ]
            self._restore_state()
        # Space
        elif key == ord(" "):
            self._fold()
        # Ctrl-d
        elif key == 4:
            sys.exit()
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
                    curses.color_pair(100),
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

    def _save_state(self):
        self._saved_idx = self._start_idx, self._stop_idx, self._selected

    def _restore_state(self):
        if self._saved_idx:
            self._start_idx, self._stop_idx, self._selected = self._saved_idx


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
