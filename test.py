# from PIL import Image, ImageEnhance
# import tkinter as tk
# from PIL import ImageTk

# win = tk.Tk()
# win.title("Compose RGBA over RGB — hue shift + rotate")

# # === CONFIG: set paths for your background (RGB) and foreground (RGBA) images ===
# # Replace these with real file paths on your system. If a path fails to open, a
# # fallback solid background / placeholder will be used.
# BG_PATH = r"C:\Users\Meepyneepy\Pictures\background_rgb.png"  # example
# FG_PATH = r"C:\Users\Meepyneepy\Documents\GitHub\Voids-Helpful-Python-Scripts-And-Modules\debug_triangle.png"  # example RGBA with transparency

# try:
#     bg_image = Image.open(BG_PATH).convert("RGB")
# except Exception:
#     # fallback: solid gray background
#     bg_image = Image.new("RGB", (800, 600), (200, 200, 200))

# try:
#     fg_image = Image.open(FG_PATH).convert("RGBA")
# except Exception:
#     # fallback: use a small red square with alpha
#     fg_image = Image.new("RGBA", (200, 200), (255, 0, 0, 192))

# # Create canvas sized to background
# width, height = bg_image.size
# canvas = tk.Canvas(win, bg="white", width=width, height=height)
# canvas.pack()

# # Keep a reference to PhotoImage to avoid GC
# photo_ref = None
# image_id = canvas.create_image(0, 0, anchor=tk.NW)

# # Animation state for hue cycling
# iteration = 0
# max_iterations = 100


# def shift_hue_rgba(img_rgba: Image.Image, hue_shift: int) -> Image.Image:
#     """
#     Shift the hue of an RGBA image by hue_shift (0-255 range) and preserve alpha.
#     Returns a new RGBA image.
#     """
#     # Separate alpha
#     r, g, b, a = img_rgba.split()
#     rgb = Image.merge("RGB", (r, g, b))

#     # Convert RGB -> HSV, shift H channel, convert back
#     hsv = rgb.convert("HSV")
#     h, s, v = hsv.split()

#     # Add hue shift with wrap-around
#     h = h.point(lambda p: (p + hue_shift) % 256)

#     new_rgb = Image.merge("HSV", (h, s, v)).convert("RGB")
#     nr, ng, nb = new_rgb.split()

#     # Put alpha channel back and return
#     return Image.merge("RGBA", (nr, ng, nb, a))


# def update_frame():
#     global iteration, photo_ref

#     # Compute hue shift (map iteration -> 0..255)
#     hue_shift = int((iteration % max_iterations) * 255 / max_iterations)

#     # Apply hue shift to foreground while preserving its alpha
#     fg_shifted = shift_hue_rgba(fg_image, hue_shift)

#     # Rotate foreground by 20 degrees (static), keep alpha, expand to fit rotated bounds
#     rotated_fg = fg_shifted.rotate(20, resample=Image.BICUBIC, expand=True)

#     # Compose: paste rotated_fg onto a copy of bg_image using fg alpha as mask
#     composed = bg_image.copy()

#     # Center the rotated foreground on the background
#     bg_w, bg_h = composed.size
#     fg_w, fg_h = rotated_fg.size
#     pos = ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2)

#     composed.paste(rotated_fg, pos, rotated_fg)  # uses alpha channel of rotated_fg as mask

#     # Show in Tkinter
#     photo_ref = ImageTk.PhotoImage(composed)
#     canvas.itemconfig(image_id, image=photo_ref)

#     iteration += 1
#     # Update every 50ms (~20 FPS). Adjust as desired.
#     win.after(50, update_frame)


# # Start animation
# update_frame()

# win.mainloop()

# Windows-only: global mouse detect + optional suppress using ctypes hooks
# Run from a console. Press ESC to stop and restore normal mouse behavior.
import ctypes
from ctypes import wintypes
import threading
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_MOUSE_LL = 14
WH_KEYBOARD_LL = 13

WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207

WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B

# Structures
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

# Hook procedure types
LowLevelMouseProc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

suppress_mouse_clicks = True  # toggle: True to prevent clicks from reaching other apps

# Keep references so they aren't GC'd
_mouse_proc_ptr = None
_keyboard_proc_ptr = None
_mouse_hook = None
_keyboard_hook = None

exit_event = threading.Event()

def install_hooks():
    global _mouse_proc_ptr, _keyboard_proc_ptr, _mouse_hook, _keyboard_hook

    hInstance = kernel32.GetModuleHandleW(None)

    @_mouse_proc_ptr  # will be assigned below; decorator used as placeholder for signature
    def _mouse_proc(nCode, wParam, lParam):
        # nCode < 0 -> pass to next hook
        if nCode >= 0:
            if wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN):
                # lParam is pointer to MSLLHOOKSTRUCT
                ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                print(f"Mouse down at ({ms.pt.x}, {ms.pt.y}) msg={hex(wParam)}")
                if suppress_mouse_clicks:
                    # returning non-zero suppresses the event
                    return 1
        return user32.CallNextHookEx(_mouse_hook, nCode, wParam, lParam)

    @_keyboard_proc_ptr
    def _keyboard_proc(nCode, wParam, lParam):
        if nCode >= 0 and wParam == WM_KEYDOWN:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            # print('Key', kb.vkCode)
            if kb.vkCode == VK_ESCAPE:
                print("ESC pressed — exiting and unhooking.")
                exit_event.set()
        return user32.CallNextHookEx(_keyboard_hook, nCode, wParam, lParam)

    # Create real function pointers with correct signatures
    _mouse_proc_ptr = LowLevelMouseProc(_mouse_proc)
    _keyboard_proc_ptr = LowLevelKeyboardProc(_keyboard_proc)

    _mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, _mouse_proc_ptr, hInstance, 0)
    if not _mouse_hook:
        raise ctypes.WinError(ctypes.get_last_error())

    _keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _keyboard_proc_ptr, hInstance, 0)
    if not _keyboard_hook:
        # clean up mouse hook
        user32.UnhookWindowsHookEx(_mouse_hook)
        raise ctypes.WinError(ctypes.get_last_error())

    print("Hooks installed. Press ESC to stop.")

def uninstall_hooks():
    global _mouse_hook, _keyboard_hook
    if _mouse_hook:
        user32.UnhookWindowsHookEx(_mouse_hook)
        _mouse_hook = None
    if _keyboard_hook:
        user32.UnhookWindowsHookEx(_keyboard_hook)
        _keyboard_hook = None
    print("Hooks removed.")

def message_loop():
    msg = wintypes.MSG()
    while not exit_event.is_set():
        r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if r == 0:
            break
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

def main():
    try:
        install_hooks()
    except Exception as e:
        print("Failed to install hooks:", e)
        return

    try:
        message_loop()
    except KeyboardInterrupt:
        print("KeyboardInterrupt — exiting.")
    finally:
        uninstall_hooks()

if __name__ == "__main__":
    main()

#utils.cmyk_to_rgb(0, 100, 100, 0)  # Example usage