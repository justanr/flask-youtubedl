from typing import TypeVar, Generic, Dict, Any

T = TypeVar("T")


class SerializeResult(Generic[T]):
    def __init__(self, data: T=None, errors: Dict[str, Any] = None) -> None:
        self.data = data
        self.errors = errors

    @staticmethod
    def from_data(self, data: [T]) -> "SerializeResult[T]":
        return SerializeResult(data, None)

    @staticmethod
    def from_errors(self, errors: Dict[str, Any]) -> "SerializeResult[T]":
        return SerializeResult(None, errors)
