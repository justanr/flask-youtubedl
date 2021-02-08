from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any
from uuid import uuid4


class AbstractYtdlHook(ABC):
    def __init__(self):
        self._dispatch_map = {
            "downloading": self.downloading,
            "error": self.error,
            "finished": self.finished,
        }

    def dispatch(self, event) -> Any:
        _m = self._dispatch_map.get(event["status"], self.unknown)
        return _m(event)

    @abstractmethod
    def downloading(self, event) -> Any:
        NotImplemented

    @abstractmethod
    def error(self, event) -> Any:
        NotImplemented

    @abstractmethod
    def finished(self, event) -> Any:
        NotImplemented

    @abstractmethod
    def unknown(self, event) -> Any:
        NotImplemented

    def __call__(self, event):
        self.dispatch(event)


class YtdlHook(AbstractYtdlHook):
    def __init__(self, post_dispatch=None):
        super().__init__()
        self.id = uuid4()
        self.events = defaultdict(list)
        self._post_dispatch = post_dispatch
        self.info = None
        self.final_state = None

    def dispatch(self, event):
        result = super().dispatch(event)
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
