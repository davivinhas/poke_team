from src.domain.entities.movement import Movement


class MovementSlot:
    def __init__(self, movement: Movement, order: int):

        if order is None:
            raise ValueError("Order cannot be None")

        if movement is None:
            raise ValueError("Movement cannot be None")

        if not isinstance(movement, Movement):
            raise ValueError("Invalid movement")

        if not isinstance(order, int):
            raise ValueError("Invalid order")

        if order <= 0 or order > 4:
            raise ValueError("Order must in range 1 and 4")

        self.movement = movement
        self.order = order
