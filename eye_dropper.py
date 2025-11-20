#!/usr/bin/env python3
"""
Simple screen eyedropper tool using only the standard library + Pillow.

Features:
- Live preview of color under the mouse cursor
- Magnifier showing a zoomed area around the cursor
- Copy Hex or RGB to clipboard

Notes:
- Designed for Windows (uses ctypes to read global cursor position). It should also work on other platforms
  where ImageGrab is supported by Pillow, but cursor position retrieval may require tweaks.
"""
from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import ttk
import math

try:
    from PIL import ImageGrab, ImageTk
except Exception as e:
    print("Pillow (PIL) is required. Install with: pip install pillow")
    raise


def get_cursor_pos(root):
    try:
        # Windows
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    except Exception:
        # Cross-platform fallback
        x = root.winfo_pointerx() + root.winfo_rootx()
        y = root.winfo_pointery() + root.winfo_rooty()
        return x, y


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return '#{:02X}{:02X}{:02X}'.format(*rgb)


# class EyeDropperApp:
#     def __init__(self, root: tk.Tk) -> None:


class EyeDropper(tk.Toplevel):
    def __init__(self, parent=None, title="Color Eyedrop Tool"):
        if parent is None:
            parent = tk.Tk()
            parent.withdraw()
            self._owns_root = True
        else:
            self._owns_root = False
            
        super().__init__(parent)
        self.zoom = 12
        self.update_ms = 60
        self.result = None
        
        self.window_size_height, self.window_size_width = 501,501   # The size of the clickable 'invisible' window
        self.preview_size_height, self.preview_size_width = 25,25   # (Odd for a center pixel) The size of the color preview / magnification box
        #self.preview_window_size_height, self.preview_window_size_width = 500,400   # The size of the preview window
        self.title(title)
        self.resizable(False, False)
        self.attributes('-topmost', True)

        #self.root.geometry(f"{self.preview_window_size_height}x{self.preview_window_size_width}+100+100")
        self.geometry(f"{self.preview_size_width * self.zoom}x{(self.preview_size_height * self.zoom) + 120}+100+100")

        self.root2 = tk.Toplevel()
        self.root2.title('Eye Dropper 2')
        self.root2.resizable(False, False)
        self.root2.attributes('-alpha', 0.002)  # Slightly transparent
        self.root2.configure(bg="#808080")
        
        self.root2.geometry(f"{self.window_size_width}x{self.window_size_height}+{self.winfo_x()+self.winfo_width()+10}+{self.winfo_y()}")
        self.root2.attributes('-topmost', True)
        self.lift(self.root2)

        self.additional_text = "\nClick to select color\nRight click to refresh\nESC to cancel"

        

        self.last_pos = (0, 0)
        self.update_color_needed = True
        self.update_image_needed = True
        self.current_grab_image = None
        self.current_grab_image_pos = (0, 0)
        self.initialize = True

        # UI
        main = ttk.Frame(self, padding=8)
        main.grid(row=0, column=0)


        # Dark theme colors
        bg_color = '#222222'
        fg_color = '#EEEEEE'
        accent_color = '#444444'

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)

        self.configure(bg=bg_color)
        main.configure(style='TFrame')

        self.canvas = tk.Canvas(main, width=self.preview_size_width * self.zoom, height=self.preview_size_height * self.zoom, bd=0, highlightthickness=0, bg=accent_color)
        self.canvas.grid(row=0, column=0, padx=(0, 16), pady=(0, 8))

        self.color_label = ttk.Label(main, text=f'Hex: #000000\nRGB: (0,0,0){self.additional_text}', font=('Consolas', 12, 'bold'), style='TLabel')
        self.color_label.grid(row=1, column=0, padx=(0, 0), pady=(0, 8), sticky='w')

        self._tk_image = None
        self.current_rgb = (0, 0, 0)

        self.bind('<Escape>', lambda e: self.destroy())
        self.root2.bind('<Escape>', lambda e: self.destroy())

        self.root2.bind('<ButtonRelease-1>', lambda e: self.return_color())

        self.root2.bind('<Button-2>', lambda e: self.refresh_color_window())

        # Start update loop
        #root.after(50, self._update_loop)
        self.after(20, self._follow_mouse)



    def _sample_region(self, x: int, y: int, sizex: int = 50, sizey: int = 50):
        left = x - (sizex // 2)
        top = y - (sizey // 2)
        right = x + (sizex // 2) + 1
        bottom = y + (sizey // 2) + 1
        self.current_grab_image_pos = (left, top)
        try:
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            return img
        except Exception:
            # In some environments ImageGrab may fail (permissions or unsupported platform)
            return None
        

        
    def _is_pos_within_window(self, posx, posy):
        x, y = posx, posy
        preview_width, preview_height = self.preview_size_width/2, self.preview_size_height/2
        win_x, win_y, win_width, win_height = self.root2.winfo_x(), self.root2.winfo_y(), self.window_size_width, self.window_size_height
        if (x >= win_x + math.ceil(preview_width/2) and x <= (win_x + win_width) - math.ceil(preview_width/2)) and (y >= win_y + math.ceil(preview_height/2) and y <= (win_y + win_height) - math.ceil(preview_height/2)):
            return True
        else:
            return False

        
    def _follow_mouse(self):
        x, y = get_cursor_pos(self)
        
        if (x, y) != self.last_pos:
            self.geometry(f"+{x + 50}+{y + 50}")

        if (x, y) != self.last_pos:
            if self._is_pos_within_window(x, y) is False or self.initialize is True:
                # mouse is outside the window, move the window to follow and update region
                self.root2.geometry(f"+{x - int(self.window_size_width / 2)}+{y - int(self.window_size_height / 2)}")
                self._update_current_grab_image(x, y)
                self._update_preview_image(x, y)
            else:
                self._update_preview_image(x, y)

        
        

        # if self.got_color is False:
        #     self._update_loop()
        #     self.got_color = True
            
        self.last_pos = (x, y)

        
        
        self.root2.configure(bg=rgb_to_hex(self.current_rgb))
        self.root2.focus_set()
        self.root2.after(50, self._follow_mouse)  # update every 20ms

        self.initialize = False


    def _update_current_grab_image(self, x, y) -> None:
        self.root2.attributes('-alpha', 0)  # Make visible when updating
        self.attributes('-alpha', 0)
        img = self._sample_region(x, y, self.window_size_width, self.window_size_height)
        self.root2.attributes('-alpha', 0.002)  # Make visible when updating # 0.002
        self.attributes('-alpha', 1)
        self.current_grab_image = img

    def _update_preview_image(self, x, y):
        if self.current_grab_image is not None:
            # print("updating image...")

            cx, cy = self.current_grab_image_pos
            cx, cy = x - cx, y - cy
            half_size_x, half_size_y = self.preview_size_width // 2, self.preview_size_height // 2


            # magnify
            mag = self.current_grab_image.copy()
            mag = mag.crop((cx - half_size_x, cy - half_size_y, cx + half_size_x, cy + half_size_y))
            mag = mag.resize((self.preview_size_width * self.zoom, self.preview_size_height * self.zoom), resample=ImageTk.Image.NEAREST)

            try:
                rgb = mag.getpixel((mag.width // 2, mag.height // 2))
            except Exception:
                rgb = (0, 0, 0)

            
            self.current_rgb = rgb
            hexc = rgb_to_hex(rgb)
            self.color_label.config(text=f'Hex: {hexc}\nRGB: {rgb}{self.additional_text}')

            self._tk_image = ImageTk.PhotoImage(mag)
            self.canvas.delete('all')
            self.canvas.create_image(0, 0, anchor='nw', image=self._tk_image)

            # draw center crosshair
            cx_pixel = (self.preview_size_width * self.zoom) // 2
            cy_pixel = (self.preview_size_height * self.zoom) // 2
            self.canvas.create_line(cx_pixel + 5 - 10, cy_pixel + 5, cx_pixel + 5 + 10, cy_pixel + 5, fill='white')
            self.canvas.create_line(cx_pixel + 5, cy_pixel + 5 - 10, cx_pixel + 5, cy_pixel + 5 + 10, fill='white')



    def return_color(self) -> tuple[int, int, int]:
        self.result = self.current_rgb
        self.destroy()
    
    def refresh_color_window(self):
        self.initialize = True
        self.last_pos = (0,0)

    def show(self):
        """Show dialog and wait for result"""
        self.wait_window(self)
        return self.result



if __name__ == '__main__':
    # Test the color picker
    eyedropper = EyeDropper()
    result = eyedropper.show()
    
    if result:
        print(f"Selected color: RGB{result}")
    else:
        print("Cancelled")
