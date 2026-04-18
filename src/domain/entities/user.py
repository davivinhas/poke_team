class User:
    def __init__(self, id: int, name: str):
        if id <= 0:
            raise ValueError("Invalid id")

        if not name:
            raise ValueError("Name cannot be empty")

        self.id = id
        self.name = name
