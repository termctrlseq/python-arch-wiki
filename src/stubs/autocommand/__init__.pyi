from collections.abc import Callable
from typing import Any, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


def autocommand(
    module: str,
    *,
    description: str | None = None,
    epilog: str | None = None,
    add_nos: bool = False,
    parser: Any | None = None,
    loop: Any | None = None,
    forever: bool = False,
    pass_loop: bool = False,
) -> Callable[[_F], _F]: ...
