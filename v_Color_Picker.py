import tkinter as tk
from tkinter import colorchooser, ttk

from PIL import Image, ImageDraw, ImageTk


# Global hidden root for standalone usage
_standalone_root = None


def _get_standalone_root():
    """Auto-detect existing Tk roots to avoid conflicts"""
    global _standalone_root
    
    # If there's already a Tk root (including from CTk), use it!
    if tk._default_root is not None:
        return tk._default_root
    
    # Only create new root if none exists
    if _standalone_root is None or not _standalone_root.winfo_exists():
        _standalone_root = tk.Tk()
        _standalone_root.withdraw()
    
    return _standalone_root


def make_rect_image(
    width: int,
    height: int,
    rgba=(255, 0, 0, 128),
    radius: int = 4,
    *,
    tile: int = 6,
    bg1=(220, 220, 220, 255),  # light square
    bg2=(180, 180, 180, 255)   # dark square
) -> ImageTk.PhotoImage:
    """
    Return an ImageTk.PhotoImage that shows a checkerboard (to visualize transparency)
    with a rounded rectangle of 'rgba' composited over it.
    """
    print(f"displaying color: {rgba}")
    img = Image.new("RGBA", (width, height), bg1)
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(0, height, tile):
        off = 0 if (y // tile) % 2 == 0 else tile
        for x in range(off, width, tile * 2):
            x2 = min(x + tile, width)
            y2 = min(y + tile, height)
            draw.rectangle((x, y, x2, y2), fill=bg2)

    if radius and radius > 0:
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=rgba)
    else:
        draw.rectangle((0, 0, width - 1, height - 1), fill=rgba)

    return ImageTk.PhotoImage(img)



class RGBAColorPicker(tk.Toplevel):
    """
This is an example of Google style.

Args:
    param1: This is the first param.
    param2: This is a second param.

Returns:
    This is a description of what is returned.

Raises:
    KeyError: Raises an exception.
"""
    def __init__(self, parent=None, initial=(50, 120, 255, 128), rect_size=(350, 250), radius=0, title="RGBA Color Picker"):
        if parent is None:
            parent = _get_standalone_root()
            self._owns_root = True
        else:
            self._owns_root = False
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)

        # Only make transient and grab if we have a visible parent
        if not self._owns_root:
            self.transient(parent)
            self.grab_set()

        # ---------- Position window at mouse cursor ----------
        # Get the current mouse position in screen coordinates
        x, y = self.winfo_pointerxy()  # <<< added
        # Apply small offset to prevent cursor covering the title bar
        self.geometry(f"+{x+10}+{y+10}")  # <<< added

        # State
        r, g, b, a = initial
        self.r, self.g, self.b, self.a = [tk.IntVar(value=int(x)) for x in (r, g, b, a)]
        self.hex_code = tk.StringVar(value=self.rgba_to_hex((r, g, b, a)))
        self.rect_w, self.rect_h, self.radius = *rect_size, radius
        self.result = None

        # Layout
        main = ttk.Frame(self, padding=10)
        main.grid(sticky="nsew")

        # Checkerboard preview
        self.bg = tk.Canvas(main, width=400, height=300, highlightthickness=0)
        self.bg.grid(row=0, column=0, columnspan=4)
        self._draw_checkerboard(self.bg, 400, 300, tile=20)
        self.photo = make_rect_image(self.rect_w, self.rect_h, rgba=(r, g, b, a), radius=self.radius)
        self.rect_img_id = self.bg.create_image(200, 150, image=self.photo)
        self.bg.image = self.photo

        # HEX entry
        ttk.Label(main, text="HEX:").grid(row=1, column=0, sticky="e", pady=(8, 0))
        self.hex_entry = ttk.Entry(main, width=12, textvariable=self.hex_code, justify="center")
        self.hex_entry.grid(row=1, column=1, sticky="w", pady=(8, 0))
        copy_btn = ttk.Button(main, text="Copy HEX", command=self._copy_hex)
        copy_btn.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(8, 0))

        # RGB fields
        rgb_frame = ttk.Frame(main)
        rgb_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        for i, (lbl, var) in enumerate(zip(("R", "G", "B"), (self.r, self.g, self.b))):
            ttk.Label(rgb_frame, text=f"{lbl}:").grid(row=0, column=i * 2, padx=(0, 2))
            ttk.Entry(rgb_frame, width=5, textvariable=var, justify="right").grid(row=0, column=i * 2 + 1, padx=(0, 10))

        # Alpha
        alpha_frame = ttk.Frame(main)
        alpha_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        ttk.Label(alpha_frame, text="Alpha (0–255):").grid(row=0, column=0, padx=(0, 6))
        self.alpha_slider = ttk.Scale(alpha_frame, from_=0, to=255, orient="horizontal", command=self._on_alpha_slide)
        self.alpha_slider.set(self.a.get())
        self.alpha_slider.grid(row=0, column=1, sticky="ew")
        ttk.Entry(alpha_frame, width=5, textvariable=self.a, justify="right").grid(row=0, column=2, padx=(6, 0))

        # Pick RGB button
        pick_btn = ttk.Button(main, text="Pick RGB…", command=self._pick_rgb)
        pick_btn.grid(row=4, column=0, columnspan=1, sticky="w", pady=(10, 0))

        # OK / Cancel
        btns = ttk.Frame(main)
        btns.grid(row=4, column=2, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="OK", command=self._on_ok).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="Cancel", command=self._on_cancel).grid(row=0, column=1)

        # Bind updates
        for var in (self.r, self.g, self.b, self.a):
            var.trace_add("write", self._update_from_vars)
        self.hex_code.trace_add("write", self._update_from_hex)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())

    # ---------- Conversion ----------
    def rgba_to_hex(self, rgba):
        r, g, b, a = rgba
        return f"#{r:02X}{g:02X}{b:02X}{a:02X}"

    def hex_to_rgba(self, hexcode):
        hexcode = hexcode.strip().lstrip("#")
        if len(hexcode) == 6:
            hexcode += "FF"
        if len(hexcode) != 8:
            raise ValueError("HEX must be 6 or 8 characters")
        r, g, b, a = [int(hexcode[i:i+2], 16) for i in range(0, 8, 2)]
        return (r, g, b, a)

    # ---------- Core logic ----------
    def _clamp(self, v):
        try:
            return max(0, min(255, int(float(v))))
        except ValueError:
            return 0

    def _draw_checkerboard(self, canvas, width, height, tile=20):
        for y in range(0, height, tile):
            for x in range(0, width, tile):
                color = "#ddd" if (x // tile + y // tile) % 2 == 0 else "#aaa"
                canvas.create_rectangle(x, y, x + tile, y + tile, fill=color, outline="")

    def _update_preview(self):
        rgba = (self.r.get(), self.g.get(), self.b.get(), self.a.get())
        img = make_rect_image(self.rect_w, self.rect_h, rgba=rgba, radius=self.radius)
        self.bg.image = img
        self.bg.itemconfigure(self.rect_img_id, image=img)

    def _update_from_vars(self, *args):
        rgba = tuple(self._clamp(v.get()) for v in (self.r, self.g, self.b, self.a))
        hex_new = self.rgba_to_hex(rgba)
        if self.hex_code.get().upper() != hex_new:
            self.hex_code.set(hex_new)
        self.alpha_slider.set(rgba[3])
        self._update_preview()

    def _update_from_hex(self, *args):
        try:
            rgba = self.hex_to_rgba(self.hex_code.get())
        except Exception:
            return
        for var, val in zip((self.r, self.g, self.b, self.a), rgba):
            if var.get() != val:
                var.set(val)

    def _pick_rgb(self):
        initial = (self.r.get(), self.g.get(), self.b.get())
        color_tuple, _ = colorchooser.askcolor(initial)
        if color_tuple:
            r, g, b = map(int, color_tuple)
            self.r.set(r)
            self.g.set(g)
            self.b.set(b)

    def _on_alpha_slide(self, val):
        self.a.set(self._clamp(val))

    def _copy_hex(self):
        self.clipboard_clear()
        self.clipboard_append(self.hex_code.get())
        self.update()

    def _on_ok(self):
        self.result = (self.r.get(), self.g.get(), self.b.get(), self.a.get())
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def show(self):
        self.wait_window(self)
        return self.result