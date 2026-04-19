from src.domain.value_objects.types import Types


class Movement:
    def __init__(
        self,
        name: str,
        power: int,
        accuracy: int,
        description: str,
        pp: int,
        type: Types,
    ):
        self.name = name
        self.power = power
        self.accuracy = accuracy
        self.description = description
        self.pp = pp
        self.type = type
