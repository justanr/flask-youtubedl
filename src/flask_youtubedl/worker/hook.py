from collections import defaultdict
from uuid import uuid4


class YtdlHook:
    def __init__(self, post_dispatch):
        self.id = uuid4()
        self.events = defaultdict(list)
        self._dispatch_map = {}
        self._post_dispatch = post_dispatch
        self._info = None

    def dispatch(self, event):
        _m = self._dispatch_map.get(event["status"], self.unknown)
        result = _m(event)
        if result and self._post_dispatch:
            self._post_dispatch(result)

    def downloading(self, event):
        self.events["downloading"].append(event)

    def error(self, event):
        self.events["error"].append(event)

    def finished(self, event):
        self.events["finished"].append(event)

    def unknown(self, event):
        self.events["unknown"].append(event)

    def __call__(self, event):
        self.dispatch(event)

    def record_info(self, info):
        if self._info is not None:
            raise Exception("YtdlHook was reused after initialized")
        self._info = info
