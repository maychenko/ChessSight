class GestureController:

    IDLE = "IDLE"
    SELECTING = "SELECTING"
    MOVING = "MOVING"

    def __init__(self):
        self.state = self.IDLE

        self.selected_square = None
        self.destination_square = None


    def update(
        self,
        gesture,
        palm_square=None,
        finger_square=None
    ):
        """
        Обрабатывает один стабильный жест.

        Возвращает словарь с текущим состоянием.
        """

        action = None
        move = None

    
        if self.state == self.IDLE:

            # ✊
            #
            # Начинаем выбирать фигуру.
            #
            if gesture == "FIST":

                if palm_square is not None:
                    self.selected_square = palm_square
                    self.destination_square = None

                    self.state = self.SELECTING

                    action = "SELECT"

      
        elif self.state == self.SELECTING:

            # ✊
            #
            # Пока кулак:
            # можно двигать руку и менять выбранную клетку.
            #
            if gesture == "FIST":

                if palm_square is not None:
                    self.selected_square = palm_square

            # ✌️
            #
            # Фиксируем выбранную клетку.
            #
            elif gesture == "TWO_FINGERS":

                self.state = self.MOVING

                if finger_square is not None:
                    self.destination_square = finger_square

                action = "START_MOVING"

            # 🖐️
            #
            # Просто отменяем выбор.
            #
            elif gesture == "OPEN_PALM":

                self.reset()

                action = "CANCEL"

        
        elif self.state == self.MOVING:

            # ✌️
            #
            # Двигаем destination.
            #
            if gesture == "TWO_FINGERS":

                if finger_square is not None:
                    self.destination_square = finger_square

            # ✊
            #
            # Отменяем текущее движение.
            # Теперь кулак снова выбирает новую клетку.
            #
            elif gesture == "FIST":

                self.state = self.SELECTING

                self.destination_square = None

                if palm_square is not None:
                    self.selected_square = palm_square

                action = "RESELECT"

            # 🖐️
            #
            # Подтверждаем ход.
            #
            elif gesture == "OPEN_PALM":

                if (
                    self.selected_square is not None
                    and self.destination_square is not None
                ):
                    move = (
                        self.selected_square,
                        self.destination_square
                    )

                    action = "COMMIT"

                self.reset()

        return {
            "state": self.state,
            "selected": self.selected_square,
            "destination": self.destination_square,
            "action": action,
            "move": move
        }

  
    def reset(self):

        self.state = self.IDLE

        self.selected_square = None
        self.destination_square = None

  
    def get_state(self):

        return {
            "state": self.state,
            "selected": self.selected_square,
            "destination": self.destination_square
        }