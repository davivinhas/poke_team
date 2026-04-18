class BaseStats:
    def __init__(
        self,
        hp: int,
        attack: int,
        defense: int,
        special_attack: int,
        special_defense: int,
        speed: int,
    ):

        for v in [hp, attack, defense, special_attack, special_defense, speed]:
            if v <= 0 or v > 255:
                raise ValueError("Base stats must be between 1 and 255")

        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.special_attack = special_attack
        self.special_defense = special_defense
        self.speed = speed

    def __eq__(self, value):
        return (
            self.hp == value.hp
            and self.attack == value.attack
            and self.defense == value.defense
            and self.special_attack == value.special_attack
            and self.special_defense == value.special_defense
            and self.speed == value.speed
        )
