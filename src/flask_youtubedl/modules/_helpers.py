from typing import List, Type, TypeVar

from injector import ClassProvider, Injector, ListOfProviders, Module, Provider

T = TypeVar("T")


class FytdlModule(Module):
    # marker module to make reflection easier
    pass


def _to_class_provider(cls):
    if not isinstance(cls, Provider):
        return ClassProvider(cls)
    return cls


class ClassProviderList(ListOfProviders[T]):
    def __init__(self, classes: List[Type[T]] = None):
        super().__init__()

        if classes:
            for cls in classes:
                self.append(ClassProvider(cls))

    def get(self, injector: Injector) -> List[T]:
        return [provider.get(injector) for provider in self._providers]
