import sys

from defer.defer import Defer
from defer.sugar._parse import _ParseDefer


def uninstall():
    if isinstance((trace := sys.gettrace()), _ParseDefer):
        sys.settrace(
            trace.tracefn if trace.tracefn is not _ParseDefer.IDENTITY else None
        )


defer = Defer()
uninstall()
