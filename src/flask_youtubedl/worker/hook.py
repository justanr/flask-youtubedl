from collections import defaultdict
from uuid import uuid4


class YtdlHook:
    def __init__(self, post_dispatch):
        self.id = uuid4()
        self.events = defaultdict(list)
        self._dispatch_map = {
            "downloading": self.downloading,
            "error": self.error,
            "finished": self.finished
        }
        self._post_dispatch = post_dispatch
        self.info = None
        self.final_state = None

    def dispatch(self, event):
        _m = self._dispatch_map.get(event["status"], self.unknown)
        result = _m(event)
        self.final_state = event["status"]
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

    def exception(self, error):
        self.events["download_error"].append(error)

    def __call__(self, event):
        self.dispatch(event)

    def recordinfo(self, info):
        if self.info is not None:
            raise Exception("YtdlHook was reused after initialized")
        self.info = info
