import abc

from ..base import BaseMessage


class BaseHandler(abc.ABC):
    name: str
    type: str
    message: BaseMessage

    def __init__(self, *, message: BaseMessage) -> None:
        self.message = message

    @abc.abstractmethod
    async def handle(self, *args) -> None:
        pass
