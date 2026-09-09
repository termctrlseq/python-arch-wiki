# python-arch-wiki

A terminal interface for browsing the [Arch Linux Wiki](https://wiki.archlinux.org/), with an interactive table of contents and article search.

## Installation

The program can be run directly with uvx; install it in a virtual environment if you want access to the source code.

To install latest version from GitHub with source and create a link with a name *wiki* (assuming `~/.local/bin` is in the **PATH**):
```bash
mkdir python_arch_wiki
cd python_arch_wiki
python3 -m venv venv
venv/bin/python -m pip install \
    -e 'python-arch-wiki @ git+https://github.com/termctrlseq/python-arch-wiki.git'
ln -s "$PWD/venv/bin/python-arch-wiki" "$HOME/.local/bin/wiki"
```
Then the source code can be found in `~/python_arch_wiki/venv/src/`.

To add `~/.local/bin` to **PATH** put this in your `~/.bashrc`
```bash
# add ~/.local/bin to PATH if not in it
[[ ":${PATH}:" != *:"${HOME}/.local/bin":* ]] \
    && export PATH="${HOME}/.local/bin:${PATH}"
```

## Usage

Run:
```
uvx python-arch-wiki [-h | [-l] [-v] [article name]]
```

Or if installed:
```
wiki [-h | [-l] [-v] [article name]]
```

### Options

```text
-h, --help        Show a help message and exit
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
| Button              | Action      |
| ------------------- | ----------- |
| *Left click*        | select      |
| *Double left click* | open        |
| *Right click*       | fold/unfold |
| *Wheel*             | navigate    |

Articles are rendered in the terminal and paged with `less`.

## Requirements

* Python 3.13+
* A terminal with `curses` support
* Internet connection
