
from typing import Sequence


def make_cmdline(harness: Sequence[str], executable: str, arg: Sequence[str] = ()) ->Sequence[str]:
    if not executable:
        return list()
    return [*harness, executable, *arg]
