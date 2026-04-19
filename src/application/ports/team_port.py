from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.team import Team


class TeamRepositoryPort(ABC):
    @abstractmethod
    def save(self, team: Team) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Team]:
        pass

    @abstractmethod
    def get_all_by_user(self, user_id: int) -> List[Team]:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass
