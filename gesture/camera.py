import cv2


class Camera:
    def __init__(self, index=0, width=1280, height=720):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(index)

        if not self.cap.isOpened():
            raise RuntimeError("Не удалось открыть камеру")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        ok, frame = self.cap.read()

        if not ok:
            return None

        frame = cv2.flip(frame, 1)

        return frame

    def release(self):
        self.cap.release()