class GestureController:
    """
    Состояния:

    IDLE
        FIST -> выбрать клетку

    SELECTING
        FIST -> менять выбранную клетку
        TWO_FINGERS -> начать движение
        OPEN_PALM -> отмена

    MOVING
        TWO_FINGERS -> менять destination
        FIST -> отменить движение и выбрать другую клетку
        OPEN_PALM -> подтвердить ход
    """

    def __init__(self):
        self.state = "IDLE"
        self.selected_square = None
        self.destination_square = None

    def reset(self):
        self.state = "IDLE"
        self.selected_square = None
        self.destination_square = None

    def update(
        self,
        gesture,
        palm_square,
        finger_square
    ):
        """
        Возвращает:

            None
                если ход ещё не подтверждён

            (from_square, to_square)
                если пользователь подтвердил ход ладонью
        """

        committed_move = None

       
        if self.state == "IDLE":

            self.selected_square = None
            self.destination_square = None

            if gesture == "FIST":
                if palm_square is not None:
                    self.selected_square = palm_square
                    self.state = "SELECTING"

       
        elif self.state == "SELECTING":

            # ✊
            # Можно двигать кулак и выбирать другую клетку
            if gesture == "FIST":

                if palm_square is not None:
                    self.selected_square = palm_square

            # ✌️
            # Начинаем движение выбранной фигуры
            elif gesture == "TWO_FINGERS":

                if self.selected_square is not None:

                    self.destination_square = finger_square
                    self.state = "MOVING"

            # 🖐️
            # Отмена
            elif gesture == "OPEN_PALM":

                self.reset()

        
        elif self.state == "MOVING":

            # ✌️
            # Двигаем destination
            if gesture == "TWO_FINGERS":

                if finger_square is not None:
                    self.destination_square = finger_square

            # ✊
            # Отмена движения + выбор другой фигуры
            elif gesture == "FIST":

                self.destination_square = None

                if palm_square is not None:
                    self.selected_square = palm_square
                    self.state = "SELECTING"
                else:
                    self.state = "SELECTING"

            # 🖐️
            # Подтверждаем
            elif gesture == "OPEN_PALM":

                if (
                    self.selected_square is not None
                    and self.destination_square is not None
                ):
                    committed_move = (
                        self.selected_square,
                        self.destination_square
                    )

                self.reset()

        return committed_move