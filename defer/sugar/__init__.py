import sys

from defer.defer import Defer
from defer.sugar._parse import _ParseDefer


def install():
    if not isinstance(sys.gettrace(), _ParseDefer):
        sys.settrace(_ParseDefer(sys.gettrace()))


defer = Defer()
install()
