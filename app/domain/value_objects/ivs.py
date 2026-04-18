class IVs:
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
            if v < 0 or v > 31:
                raise ValueError("IVs must be between 0 and 31")

        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.special_attack = special_attack
        self.special_defense = special_defense
        self.speed = speed
