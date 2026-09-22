import ctypes
import threading
import time

import cv2
import numpy as np

import win32api
import win32con
import win32gui
import win32ui

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class HolographicOverlay:
    def __init__(self, region):
        self.region = region

        self.left = int(region["left"])
        self.top = int(region["top"])
        self.width = int(region["width"])
        self.height = int(region["height"])

        self.hwnd = None
        self.running = True
        self.visible = False

        self.current_square = None
        self.selected_square = None
        self.destination_square = None
        self.trajectory = []

        self._lock = threading.Lock()

        self._class_name = f"ChessSightOverlay_{id(self)}"

        self._create_window()

        self._watchdog = threading.Thread(
            target=self._topmost_watchdog,
            daemon=True
        )
        self._watchdog.start()

        print(
            f"[OVERLAY] Создан: "
            f"{self.left},{self.top} "
            f"{self.width}x{self.height}"
        )

   
    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_NCHITTEST:
            return win32con.HTTRANSPARENT

        if msg == win32con.WM_MOUSEACTIVATE:
            return win32con.MA_NOACTIVATE

        if msg == win32con.WM_ERASEBKGND:
            return 1

        if msg == win32con.WM_DESTROY:
            return 0

        return win32gui.DefWindowProc(
            hwnd,
            msg,
            wparam,
            lparam
        )

    def _create_window(self):
        hinstance = win32api.GetModuleHandle(None)

        wnd_class = win32gui.WNDCLASS()
        wnd_class.hInstance = hinstance
        wnd_class.lpszClassName = self._class_name
        wnd_class.lpfnWndProc = self._window_proc

        try:
            win32gui.RegisterClass(wnd_class)
        except win32gui.error as e:
            if getattr(e, "winerror", None) != 1410:
                raise

        ex_style = (
            win32con.WS_EX_LAYERED
            | win32con.WS_EX_TRANSPARENT
            | win32con.WS_EX_TOOLWINDOW
            | win32con.WS_EX_NOACTIVATE
        )

        self.hwnd = win32gui.CreateWindowEx(
            ex_style,
            self._class_name,
            "ChessSight Holographic Overlay",
            win32con.WS_POPUP,
            self.left,
            self.top,
            self.width,
            self.height,
            0,
            0,
            hinstance,
            None
        )

        if not self.hwnd:
            raise RuntimeError(
                "Не удалось создать Win32 overlay"
            )

        self._force_topmost()

        self._message_thread = threading.Thread(
            target=self._message_loop,
            daemon=True
        )
        self._message_thread.start()

    def _message_loop(self):
        while self.running:
            try:
                win32gui.PumpWaitingMessages()
            except Exception:
                break

            time.sleep(0.005)


    def _force_topmost(self):
        if not self.hwnd:
            return

        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,
            self.left,
            self.top,
            self.width,
            self.height,
            win32con.SWP_NOACTIVATE
            | win32con.SWP_SHOWWINDOW
        )

    def _topmost_watchdog(self):
        while self.running:
            try:
                if self.hwnd and self.visible:
                    self._force_topmost()
            except Exception:
                pass

            time.sleep(0.05)

    
    def show(self):
        self.visible = True

        if not self.hwnd:
            return

        win32gui.ShowWindow(
            self.hwnd,
            win32con.SW_SHOWNOACTIVATE
        )

        self._force_topmost()
        self._render()

    def hide(self):
        self.visible = False

        if not self.hwnd:
            return

        win32gui.ShowWindow(
            self.hwnd,
            win32con.SW_HIDE
        )

   
    def draw(
        self,
        current_square=None,
        selected_square=None,
        destination_square=None,
        trajectory=None,
        **kwargs
    ):
        """Метод-обертка для совместимости с main.py"""
        self.update(
            current_square=current_square,
            selected_square=selected_square,
            destination_square=destination_square,
            trajectory=trajectory
        )

    def update(
        self,
        current_square=None,
        selected_square=None,
        destination_square=None,
        trajectory=None
    ):
        with self._lock:
            self.current_square = current_square
            self.selected_square = selected_square
            self.destination_square = destination_square
            self.trajectory = (
                list(trajectory)
                if trajectory
                else []
            )

        if self.visible:
            self._render()

    
    def _square_center(self, square):
        if square is None:
            return None

        files = "abcdefgh"

        try:
            col = files.index(square[0])
            row = 8 - int(square[1])
        except (ValueError, IndexError):
            return None

        cell_w = self.width / 8
        cell_h = self.height / 8

        return (
            int(col * cell_w + cell_w / 2),
            int(row * cell_h + cell_h / 2)
        )

    def _square_rect(self, square):
        if square is None:
            return None

        files = "abcdefgh"

        try:
            col = files.index(square[0])
            row = 8 - int(square[1])
        except (ValueError, IndexError):
            return None

        cell_w = self.width / 8
        cell_h = self.height / 8

        return (
            int(col * cell_w),
            int(row * cell_h),
            int((col + 1) * cell_w),
            int((row + 1) * cell_h)
        )

    
    def _draw_square(
        self,
        frame,
        square,
        color,
        thickness=3
    ):
        rect = self._square_rect(square)

        if rect is None:
            return

        x1, y1, x2, y2 = rect

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            thickness
        )

    def _render(self):
        if not self.hwnd or not self.visible:
            return

        frame = np.zeros(
            (self.height, self.width, 4),
            dtype=np.uint8
        )

        with self._lock:
            current = self.current_square
            selected = self.selected_square
            destination = self.destination_square
            trajectory = list(self.trajectory)

       
        for i in range(9):
            x = int(i * self.width / 8)

            cv2.line(
                frame,
                (x, 0),
                (x, self.height),
                (120, 120, 120, 160),
                1
            )

        for i in range(9):
            y = int(i * self.height / 8)

            cv2.line(
                frame,
                (0, y),
                (self.width, y),
                (120, 120, 120, 160),
                1
            )

        
        self._draw_square(
            frame,
            current,
            (255, 180, 0, 220),
            3
        )

    
        self._draw_square(
            frame,
            selected,
            (0, 255, 255, 240),
            5
        )

        
        self._draw_square(
            frame,
            destination,
            (0, 255, 0, 240),
            5
        )

       
        if len(trajectory) >= 2:
            points = []

            for square in trajectory:
                point = self._square_center(square)

                if point is not None:
                    points.append(point)

            for i in range(len(points) - 1):
                cv2.arrowedLine(
                    frame,
                    points[i],
                    points[i + 1],
                    (255, 255, 0, 220),
                    3,
                    tipLength=0.2
                )

        self._update_layered_window(frame)

   
    def _update_layered_window(self, frame):
        if not self.hwnd:
            return

        height, width = frame.shape[:2]

        frame = np.ascontiguousarray(
            frame,
            dtype=np.uint8
        )

        screen_dc_handle = win32gui.GetDC(0)

        screen_dc = win32ui.CreateDCFromHandle(
            screen_dc_handle
        )

        memory_dc = screen_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()

        try:
            bitmap.CreateCompatibleBitmap(
                screen_dc,
                width,
                height
            )

            memory_dc.SelectObject(bitmap)

            gdi32 = ctypes.windll.gdi32

            class BITMAPINFOHEADER(
                ctypes.Structure
            ):
                _fields_ = [
                    ("biSize", ctypes.c_uint32),
                    ("biWidth", ctypes.c_int32),
                    ("biHeight", ctypes.c_int32),
                    ("biPlanes", ctypes.c_uint16),
                    ("biBitCount", ctypes.c_uint16),
                    ("biCompression", ctypes.c_uint32),
                    ("biSizeImage", ctypes.c_uint32),
                    ("biXPelsPerMeter", ctypes.c_int32),
                    ("biYPelsPerMeter", ctypes.c_int32),
                    ("biClrUsed", ctypes.c_uint32),
                    ("biClrImportant", ctypes.c_uint32),
                ]

            class BITMAPINFO(
                ctypes.Structure
            ):
                _fields_ = [
                    ("bmiHeader", BITMAPINFOHEADER),
                    ("bmiColors", ctypes.c_uint32 * 3),
                ]

            bmi = BITMAPINFO()

            bmi.bmiHeader.biSize = ctypes.sizeof(
                BITMAPINFOHEADER
            )

            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = win32con.BI_RGB
            bmi.bmiHeader.biSizeImage = (
                width * height * 4
            )

            raw = frame.tobytes()

            gdi32.SetDIBitsToDevice.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.POINTER(BITMAPINFO),
                ctypes.c_uint32,
            ]

            gdi32.SetDIBitsToDevice.restype = ctypes.c_int

            gdi32.SetDIBitsToDevice(
                memory_dc.GetSafeHdc(),
                0,
                0,
                width,
                height,
                0,
                0,
                0,
                height,
                raw,
                ctypes.byref(bmi),
                win32con.DIB_RGB_COLORS
            )

            
            blend = (
                win32con.AC_SRC_OVER,
                0,
                255,
                win32con.AC_SRC_ALPHA
            )

            win32gui.UpdateLayeredWindow(
                self.hwnd,
                screen_dc_handle,
                (self.left, self.top),
                (width, height),
                memory_dc.GetSafeHdc(),
                (0, 0),
                0,
                blend,
                win32con.ULW_ALPHA
            )

        finally:
            win32gui.DeleteObject(bitmap.GetHandle())
            memory_dc.DeleteDC()
            screen_dc.DeleteDC()

            win32gui.ReleaseDC(
                0,
                screen_dc_handle
            )

    
    def clear(self):
        with self._lock:
            self.current_square = None
            self.selected_square = None
            self.destination_square = None
            self.trajectory = []

        if not self.hwnd or not self.visible:
            return

        empty = np.zeros(
            (self.height, self.width, 4),
            dtype=np.uint8
        )

        self._update_layered_window(
            empty
        )

    
    def close(self):
        self.running = False
        self.visible = False

        hwnd = self.hwnd
        self.hwnd = None

        if hwnd:
            try:
                win32gui.DestroyWindow(hwnd)
            except Exception:
                pass