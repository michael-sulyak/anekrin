from functools import lru_cache


class ClassPropertyAllMixin:
    @classmethod
    @property
    @lru_cache(maxsize=1)
    def ALL(cls) -> set[str]:
        return {
            value
            for key, value in vars(cls).items()
            if key != 'ALL'
            if not callable(getattr(cls, key))
            if not key.startswith('__')
        }
