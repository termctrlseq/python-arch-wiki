# python-arch-wiki

A terminal interface for browsing the [Arch Linux Wiki](https://wiki.archlinux.org/), with an interactive table of contents and article search.

## Installation

To install in the virtual environment in the directory `python_arch_wiki` and create a link with a name *wiki* (assuming `~/.local/bin` is in the **PATH**):
```bash
mkdir python_arch_wiki
cd python_arch_wiki
python3 -m venv venv
source venv/bin/activate
pip install -e 'python-arch-wiki @ git+https://github.com/termctrlseq/python-arch-wiki.git'
ln -s "$(realpath venv/bin/python-arch-wiki)" "$HOME/.local/bin/wiki"
```

To add `~/.local/bin` to **PATH** put this in your `~/.bashrc`
```bash
# add ~/.local/bin to PATH if not in it
[[ ":${PATH}:" != *:"${HOME}/.local/bin":* ]] \
    && export PATH="${HOME}/.local/bin:${PATH}"
```

Then the source code can be found in `~/python_arch_wiki/venv/src/`.

## Usage

```
wiki [-l] [-v] [article name]
```

## Options

```text
-l, --link-url    Show URLs in links
-v, --verbose     Enable debug logging
```

## Examples

Open the table of contents:

```bash
wiki
```

From there, press `/` to search the Arch Wiki. The search uses the Arch Wiki's own search engine, and the results are presented in a navigable menu. For convenience, this can be preferable to specifying a longer query on the command line:

```text
/install
```

For short, specific searches, giving the article name on the command line is often more convenient:

```bash
wiki zram
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

* *Left click* — select
* *Double left click* — open
* *Right click* — fold/unfold
* *Wheel* — navigate

Articles are rendered in the terminal and paged with `less`.

## Requirements

* Python 3.13+
* A terminal with `curses` support
* Internet connection
