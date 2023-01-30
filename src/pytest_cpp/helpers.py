from typing import Sequence


def make_cmdline(
    harness: Sequence[str], executable: str, arg: Sequence[str] = ()
) -> Sequence[str]:
    return [*harness, executable, *arg]
