# python-arch-wiki

A terminal interface for browsing the [Arch Linux Wiki](https://wiki.archlinux.org/).

## Usage

Run the interactive table of contents:

```bash
uv run python-arch-wiki
```

Or open an article directly:

```bash
uv run python-arch-wiki linux kernel
```

Options:

```text
--link-url    Show URLs in links
--verbose     Enable debug logging
```

## Controls

| Key                                | Action              |
| ---------------------------------- | ------------------- |
| `↑` / `k` / `Ctrl-P` / `Shift-Tab` | Previous            |
| `↓` / `j` / `Ctrl-N` / `Tab`       | Next                |
| `H`                                | First visible item  |
| `M`                                | Middle visible item |
| `L`                                | Last visible item   |
| `Enter`                            | Open                |
| `Space` / `l`                      | Fold/unfold         |
| `h` / `u` / `Esc`                  | Go up               |
| `/` / `?`                          | Search              |
| `q` / `Ctrl-D`                     | Quit                |

Mouse input is also supported:

* Left click — select
* Double left click — open
* Right click — fold/unfold
* Wheel — navigate

Articles are rendered in the terminal and paged with `less`.

## Requirements

* Python 3.13+
* Internet connection
* A terminal with `curses` support
