from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, NoReturn, Union, Callable, List


class HashBaseStruct(ABC):

    @abstractmethod
    def __init__(self, hsh: Union[str, Callable[..., Union[bytes, bytearray]]] = 'sha256') -> None:
        pass

    @abstractmethod
    def clear(self) -> NoReturn:
        pass

    @abstractmethod
    def add_iter(self, keys, values) -> NoReturn:
        pass

    @abstractmethod
    def add_dict(self, dct: dict) -> NoReturn:
        pass

    @abstractmethod
    def size(self) -> int:
        pass

    @abstractmethod
    def root_hash(self) -> str:
        pass

    @abstractmethod
    def get_changeset(self, destination: HashBaseStruct) -> List[dict]:
        pass

    @abstractmethod
    def swap(self, other_tree: HashBaseStruct) -> NoReturn:
        pass

    @abstractmethod
    def _find_position(self, key: Any) -> int:
        pass

    @abstractmethod
    def get(self, key: Any, verified: bool = False) -> Any:
        pass

    @abstractmethod
    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    @abstractmethod
    def delete(self, key: Any) -> NoReturn:
        pass

    @abstractmethod
    def __delitem__(self, key: Any) -> NoReturn:
        pass

    @abstractmethod
    def set(self, key: Any, value: Any) -> NoReturn:
        pass

    @abstractmethod
    def __setitem__(self, key: Any, value: Any) -> NoReturn:
        pass

    @abstractmethod
    def get_by_order(self, order: int, as_json: bool = False) -> dict:
        pass

    @abstractmethod
    def __iter__(self, as_json: bool = False) -> iter:
        pass

    @abstractmethod
    def _get_hash(self, value: Any) -> bytearray:
        pass

    @abstractmethod
    def __contains__(self, key: Any) -> bool:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, o: object) -> bool:
        pass

    @abstractmethod
    def __ne__(self, o: object) -> bool:
        pass
