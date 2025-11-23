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
import tkinter.font as tkfont
from tkinter import ttk
import math
import utils

try:
    from PIL import ImageGrab, ImageTk, Image, ImageDraw
except Exception as e:
    print("Pillow (PIL) is required. Install with: pip install pillow")
    raise







# class EyeDropperApp:
#     def __init__(self, root: tk.Tk) -> None:


class EyeDropperAPP(tk.Toplevel):
    """
A Tkinter-based color picker eyedropper tool with live preview and magnification.

This class creates an interactive eyedropper interface that allows users to select colors
from anywhere on the screen with pixel-perfect precision. It displays a magnified preview
of the area around the cursor and shows color information in real-time.

Args:
    parent: Parent Tkinter window (optional). If None, creates its own root window.
    initial: Initial color as RGB/RGBA tuple (e.g., (255, 0, 0)) or HEX string (e.g., "#FF0000") to display as comparison (optional)
    title: Window title string (default: "Color Eyedrop Tool")

Returns:
    When show() is called, returns the selected color as an RGB tuple (r, g, b) where
    each component is 0-255, or None if cancelled.

Features:
    - Live magnified preview (12x zoom) of cursor area
    - Real-time hex and RGB color display
    - Pixel-precise selection with arrow key adjustment
    - Side-by-side comparison with initial color (if provided)
    - Multi-monitor support (requires 'mss' module)
    - Cross-platform cursor tracking with Windows optimization

Controls:
    - LEFT CLICK or ENTER: Select current color and close
    - RIGHT CLICK: Refresh window position
    - ESC: Cancel and close without selecting
    - ARROW KEYS: Fine-tune pixel selection by shifting cursor position

Usage:
    # Simple color selection
    picker = EyeDropper()
    color = picker.show()
    if color:
        print(f"Selected: RGB{color}")
    
    # Compare against existing color
    old_color = (255, 0, 0)
    picker = EyeDropper(initial=old_color, title="Change Background Color")
    new_color = picker.show()
    if new_color:
        print(f"Changed from {old_color} to {new_color}")
"""
    def __init__(self, parent=None, initial=None, title="Color Eyedrop Tool"):
        if parent is None:
            parent = tk.Tk()
            parent.withdraw()
            self._owns_root = True
        else:
            self._owns_root = False
            
        super().__init__(parent)

                # after other initialization...
        if utils.try_import("mss"):
            import mss
            self._sct = mss.mss()
        else:
            self._sct = None
            print("'mss' module not found! Multi monitor support may not be supported without it!")

        self.zoom = 12
        self.update_ms = 60
        self.result = None

        self.initial_color_type = utils.get_color_type(initial)
        print(f"Initial Color Type: {self.initial_color_type}")
        print(f"Initial Color: {initial}")
        if initial is not None and self.initial_color_type:
            if self.initial_color_type == 'hex':
                self.initial = utils.hex_to_rgb(initial)
            else:
                self.initial = initial
        else:
            self.initial = None
        
        self.window_size_height, self.window_size_width = 501,501   # The size of the clickable 'invisible' window
        self.preview_size_height, self.preview_size_width = 25,25   # (Odd for a center pixel) The size of the color preview / magnification box
        #self.preview_window_size_height, self.preview_window_size_width = 500,400   # The size of the preview window
        self.title(title)
        self.resizable(False, False)
        self.attributes('-topmost', True)

        #self.root.geometry(f"{self.preview_window_size_height}x{self.preview_window_size_width}+100+100")
        self.preview_window_size_width = (self.preview_size_height * self.zoom) + 16
        self.preview_window_size_height = (self.preview_size_width * self.zoom) + 95 + 8
        self.geometry(f"{self.preview_window_size_width}x{self.preview_window_size_height}+100+100")

        self.root2 = tk.Toplevel()
        self.root2.title('Eye Dropper 2')
        self.root2.resizable(False, False)
        self.root2.attributes('-alpha', 0.002)  # Slightly transparent
        self.root2.configure(bg="#808080")
        
        self.root2.geometry(f"{self.window_size_width}x{self.window_size_height}+{self.winfo_x()+self.winfo_width()+10}+{self.winfo_y()}")
        self.root2.attributes('-topmost', True)
        # self.lift(self.root2)

        

        

        self.last_pos = (0, 0)
        self.adjusted_mouse_pos = (0, 0)    # This is used to shift the selected pixel up, down, left, or right with the arrow keys.
        self.update_color_needed = True
        self.update_image_needed = True
        self.current_grab_image = None
        self.current_grab_image_pos = (0, 0)
        self.initialize = True
        self.just_shifted_mouse_pos = False
        self.window_is_focused = False

        # UI
        main = ttk.Frame(self, padding=8)
        main.grid(row=0, column=0)


        # Dark theme colors
        self.bg_color = '#222222'
        self.fg_color = '#EEEEEE'
        self.accent_color = '#444444'
        self.font = tkfont.Font(family='Consolas', size=12, weight='bold')
        self.line_height = self.font.metrics('linespace')
        


        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)

        self.configure(bg=self.bg_color)
        main.configure(style='TFrame')

        self.canvas = tk.Canvas(main, width=self.preview_size_width * self.zoom, height=self.preview_size_height * self.zoom, bd=0, highlightthickness=0, bg=self.accent_color)
        self.canvas.grid(row=0, column=0, padx=(0, 16), pady=(0, 8))

        self.text_label_line_1 = ttk.Label(main, text=f'', font=self.font, style='TLabel')
        self.text_label_line_1.grid(row=1, column=0, padx=(0, 0), pady=(0, 8), sticky='w')

        self.text_label_line_2 = ttk.Label(main, text=f'', font=self.font, style='TLabel')
        self.text_label_line_2.grid(row=2, column=0, padx=(0, 0), pady=(0, 8), sticky='w')

        self._tk_image = None
        self.current_rgb = (0, 0, 0)

        self.bind('<Escape>', lambda e: self.on_close())
        self.root2.bind('<Escape>', lambda e: self.on_close())

        self.root2.bind('<ButtonRelease-1>', lambda e: self.return_color())
        self.root2.bind('<Return>', lambda e: self.return_color())

        self.root2.bind('<Button-3>', lambda e: self.refresh_color_window())

        self.root2.bind('<Left>', lambda e: self.shift_mouse_pos_left())
        self.root2.bind('<Right>', lambda e: self.shift_mouse_pos_right())
        self.root2.bind('<Up>', lambda e: self.shift_mouse_pos_up())
        self.root2.bind('<Down>', lambda e: self.shift_mouse_pos_down())

        self.root2.bind('<FocusOut>', lambda e: setattr(self, 'window_is_focused', False))
        self.root2.bind('<FocusIn>', lambda e: setattr(self, 'window_is_focused', True))

        # Start update loop
        #root.after(50, self._update_loop)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root2.protocol("WM_DELETE_WINDOW", self.on_close)
        self.sched_follow_mouse = self.after(20, self._follow_mouse)

        self.focus_force()

    

    def _sample_region(self, x: int, y: int, sizex: int = 50, sizey: int = 50):
        left = x - (sizex // 2)
        top = y - (sizey // 2)
        right = x + (sizex // 2) + 1
        bottom = y + (sizey // 2) + 1
        self.current_grab_image_pos = (left, top)

        if getattr(self, "_sct", None) is not None:
            try:
                monitor = {"left": left, "top": top, "width": sizex + 1, "height": sizey + 1}
                sct_img = self._sct.grab(monitor)
                # sct_img.rgb provides RGB bytes; create a PIL Image from that.
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                return img
            except Exception:
                # fall through to Pillow fallback
                pass

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
        x, y = self.get_cursor_pos()
        
        if ((x, y) != self.last_pos and self.adjusted_mouse_pos == (0,0)) or self.just_shifted_mouse_pos is True:
            x_win_offset, y_win_offset = 50, 50
            if (x + x_win_offset + self.preview_window_size_width) > self.winfo_screenwidth():
                x_win_offset = -50 - self.preview_window_size_width

            if (y + y_win_offset + self.preview_window_size_height) > self.winfo_screenheight():
                y_win_offset = -50 - self.preview_window_size_height

            self.geometry(f"+{x + x_win_offset}+{y + y_win_offset}")

        if ((x, y) != self.last_pos and self.adjusted_mouse_pos == (0,0)) or self.just_shifted_mouse_pos is True:
            if self._is_pos_within_window(x, y) is False or self.initialize is True:
                # mouse is outside the window, move the window to follow and update region
                self.root2.geometry(f"+{x - int(self.window_size_width / 2)}+{y - int(self.window_size_height / 2)}")
                self._update_current_grab_image(x, y)
                self._update_preview_image(x, y)
            else:
                self._update_preview_image(x, y)

    
        if self.adjusted_mouse_pos == (0,0) and self.just_shifted_mouse_pos is False:
            self.last_pos = (x, y)

        
        self.initialize = False
        self.just_shifted_mouse_pos = False

        self.root2.configure(bg=self.rgb_to_hex(self.current_rgb))
        self.root2.focus_set()

        self.sched_follow_mouse = self.root2.after(50, self._follow_mouse)  # update every 20ms

        


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
            hexc = self.rgb_to_hex(rgb)
            
            if self.window_is_focused:
                self.text_label_line_1.config(text=f"LEFT CLICK or ENTER to select\nRIGHT CLICK to refresh\nESC to cancel\nARROW KEYS to shift selection", foreground="white")
                self.text_label_line_2.config(text=f"")
            else:
                self.text_label_line_1.config(text=f"WINDOW NOT FOCUSED!", foreground="red")
                self.text_label_line_2.config(text=f"RIGHT CLICK to focus!")


            self._tk_image = ImageTk.PhotoImage(mag)
            self.canvas.delete('all')
            self.canvas.create_image(0, 0, anchor='nw', image=self._tk_image)

            # draw center crosshair
            img_size_x, img_size_y = self.preview_size_width * self.zoom, self.preview_size_height * self.zoom
            cx_pixel = img_size_x // 2
            cy_pixel = img_size_y // 2
            self.canvas.create_line(cx_pixel + 5 - 10, cy_pixel + 5, cx_pixel + 5 + 10, cy_pixel + 5, fill=self.rgb_to_hex(utils.get_contrast_color(self.current_rgb)))
            self.canvas.create_line(cx_pixel + 5, cy_pixel + 5 - 10, cx_pixel + 5, cy_pixel + 5 + 10, fill=self.rgb_to_hex(utils.get_contrast_color(self.current_rgb)))

            # print(f"Contrast Color: {utils.get_contrast_color(self.current_rgb)}")
            # small cross marker at the center

            image_text = f"HEX: {hexc}\nRGB: {rgb}"
            try:
                padding = 5
                # rectangle height enough for two lines of text; adjust as needed
                rect_h = (self.font.metrics('linespace') * 2) + (padding * 2)
                # draw semi-transparent background for text
                overlay = Image.new('RGBA', (img_size_x, img_size_y), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                draw.rectangle((0, img_size_y - rect_h, img_size_x, img_size_y), fill=(0, 0, 0, 80))
                if self.initial is not None:
                    # If inital color is provided, display it next to the new color
                    rx1, ry1 = (img_size_x - (rect_h * 2)) + 10, (img_size_y - rect_h) + 5
                    rx2, ry2 = img_size_x - (rect_h), img_size_y - 5
                    draw.rectangle((rx1, ry1, rx2, ry2), fill=(self.initial[0], self.initial[1], self.initial[2], 255)) # Display new color
                    draw.text(((rx1 + rx2) // 2, ry2), "OLD", fill=utils.get_contrast_color((self.initial[0], self.initial[1], self.initial[2])), anchor= "md")

                rx1, ry1 = (img_size_x - rect_h) + 5, (img_size_y - rect_h) + 5
                rx2, ry2 = img_size_x - 5, img_size_y - 5
                
                draw.rectangle((rx1, ry1, rx2, ry2), fill=(rgb[0], rgb[1], rgb[2], 255)) # Display new color
                draw.text(((rx1 + rx2) // 2, ry2), "NEW", fill=utils.get_contrast_color((rgb[0], rgb[1], rgb[2])), anchor= "md")
                self._overlay_image = ImageTk.PhotoImage(overlay)
                self.canvas.create_image(0, 0, anchor='nw', image=self._overlay_image)

                # show the current hex color in the bottom-left of the preview on top of the overlay
                self.canvas.create_text(padding, img_size_y - padding, anchor='sw', text=image_text, fill='white', font=self.font)
            except Exception:
                # fallback label if hexc isn't available for some reason
                self.canvas.create_text(5, img_size_y - 5, anchor='sw', text=image_text, fill='white', font=self.font)


    def get_cursor_pos(self):
        # What needs to happen;
        # this is called every few ms to check if mouse has moved at all.
        # Needs to be able to detect if mouse was actually moved, then reset shifted offset, and return actual mouse pos.
        # If mouse hasn't actually been moved, then add shifted offset to actual mouse pos.
        try:
            # Windows
            import ctypes
            from ctypes import wintypes
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            if (pt.x, pt.y) != self.last_pos:
                # Mouse has actually moved, reset adjusted offset
                self.adjusted_mouse_pos = (0, 0)
                return pt.x, pt.y
            else:
                # Mouse hasn't moved, apply adjusted offset
                return pt.x + self.adjusted_mouse_pos[0], pt.y + self.adjusted_mouse_pos[1]
        except Exception:
            # Cross-platform fallback
            x = self.winfo_pointerx() + self.winfo_rootx()
            y = self.winfo_pointery() + self.winfo_rooty()
            if (x, y) != self.last_pos:
                # Mouse has actually moved, reset adjusted offset
                self.adjusted_mouse_pos = (0, 0)
                return x, y
            else:
                # Mouse hasn't moved, apply adjusted offset
                return x + self.adjusted_mouse_pos[0], y + self.adjusted_mouse_pos[1]
            return x, y



    def rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        return '#{:02X}{:02X}{:02X}'.format(*rgb)
    
    def shift_mouse_pos_left(self):
        self.adjusted_mouse_pos = (self.adjusted_mouse_pos[0] - 1, self.adjusted_mouse_pos[1])
        self.just_shifted_mouse_pos = True

    def shift_mouse_pos_right(self):
        self.adjusted_mouse_pos = (self.adjusted_mouse_pos[0] + 1, self.adjusted_mouse_pos[1])
        self.just_shifted_mouse_pos = True

    def shift_mouse_pos_up(self):
        self.adjusted_mouse_pos = (self.adjusted_mouse_pos[0], self.adjusted_mouse_pos[1] - 1)
        self.just_shifted_mouse_pos = True

    def shift_mouse_pos_down(self):
        self.adjusted_mouse_pos = (self.adjusted_mouse_pos[0], self.adjusted_mouse_pos[1] + 1)
        self.just_shifted_mouse_pos = True


    def return_color(self) -> tuple[int, int, int]:
        if self.initial_color_type == 'hex':
            print("returning hex")
            self.result = utils.rgb_to_hex(self.current_rgb)
        elif self.initial_color_type == 'rgba' and len(self.initial) == 4:
            print("returning rgba")
            self.result = (self.current_rgb[0], self.current_rgb[1], self.current_rgb[2], self.initial[3])
        else:
            print("returning rgb")
            self.result = self.current_rgb
        self.on_close()
    
    def refresh_color_window(self):
        print("refreshed")
        self.initialize = True
        self.last_pos = (0,0)

    def show(self):
        """Show dialog and wait for result"""
        self.wait_window(self)
        return self.result
    
    def on_close(self):
        """Handle window close event and stop the update loop"""
        print("eye_dropper: on_close called")

        self.after_cancel(self.sched_follow_mouse)
        
        # Clean up root2 window
        if hasattr(self, 'root2') and self.root2:
            try:
                self.root2.destroy()
            except:
                pass
        
        # Clean up mss if it exists
        if hasattr(self, '_sct') and self._sct:
            try:
                self._sct.close()
            except:
                pass
        
        # Destroy the main window
        self.destroy()
        
        # Clean up the root window if we own it
        if self._owns_root and self.master:
            try:
                self.master.destroy()
            except:
                pass



if __name__ == '__main__':
    # Test the color picker
    eyedropper = EyeDropperAPP(initial=(255,0,0))
    result = eyedropper.show()
    
    if result:
        print(f"Selected color: RGB{result}")
    else:
        print("Cancelled")
