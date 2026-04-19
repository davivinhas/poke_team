import abc
from typing import Optional


class MovementGateway(abc.ABC):
    @abc.abstractmethod
    def get_by_name(self, id: int) -> Optional[str]:
        raise NotImplementedError
