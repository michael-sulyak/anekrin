import typing


class MemCache:
    _data: dict[str, typing.Any]

    def __init__(self) -> None:
        self._data = {}

    def set(self, name: str, value: typing.Any) -> None:
        self._data[name] = value

    def has(self, name: str) -> bool:
        return name in self._data

    def get(self, name: str, default: typing.Any = None) -> typing.Any:
        try:
            return self._data[name]
        except IndexError:
            return default


mem_cache = MemCache()
