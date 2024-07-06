"""
Utility functions for windows API calls
"""

from PySide6.QtWidgets import QWidget
import pygetwindow


def win32_set_as_wallpaper(widget: QWidget):
    import win32gui

    progman_window = win32gui.FindWindow("Progman", None)
    win32gui.SendMessageTimeout(progman_window, 0x052C, None, None, 0, 1000)
    workerw: int = None

    def enum_windows_foreach(hwnd: int, lParam: int):
        nonlocal workerw
        defview = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
        if defview:
            workerw = win32gui.FindWindowEx(None, hwnd, "WorkerW", None)
        return True

    win32gui.EnumWindows(enum_windows_foreach, None)
    win32gui.SetParent(widget.winId(), workerw)
    return workerw


def win32_get_current_wallpaper():
    import win32gui
    import win32con

    return win32gui.SystemParametersInfo(win32con.SPI_GETDESKWALLPAPER, 200, 0)


def win32_set_current_wallpaper(path: str):
    import win32gui
    import win32con

    win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, path, 3)


def win32_get_window_classname(hwnd: int):
    import win32gui

    return win32gui.GetClassName(hwnd)


def win32_is_clicking_wallpaper(x: int, y: int):
    win: list[pygetwindow.Win32Window] = pygetwindow.getWindowsAt(x, y)
    ret = True
    # the list only contains WorkerW, Progman and Windows.UI.Core.CoreWindow
    available_names = ["WorkerW", "Progman", "CoreWindow", "ApplicationFrameWindow"]
    active = False
    for w in win:
        classname = win32_get_window_classname(w._hWnd)
        # print(f"Classname: {classname}, id: {w._hWnd}, active: {w.isActive}")
        r = False
        if classname == "WorkerW" and w.isActive:
            active = True
        for name in available_names:
            if name in classname:
                r = True
        if not r:
            ret = False
    return ret and active
