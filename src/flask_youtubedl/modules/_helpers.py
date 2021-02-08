from injector import ClassProvider
from injector import ListOfProviders as _ListOfProviders
from injector import Module, Provider


class FytdlModule(Module):
    # marker module to make reflection easier
    pass


def _to_class_provider(cls):
    if not isinstance(cls, Provider):
        return ClassProvider(cls)
    return cls


class ListOfProviders(_ListOfProviders):
    def __init__(self, classes=()):
        super().__init__()
        for cls in classes:
            self.append(cls)


class ClassProviderList(ListOfProviders):
    def __init__(self, classes=()):
        super().__init__(_to_class_provider(c) for c in classes)
