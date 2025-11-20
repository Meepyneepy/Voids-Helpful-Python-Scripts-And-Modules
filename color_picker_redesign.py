import tkinter as tk
from tkinter import ttk
import math
import utils
from PIL import Image, ImageDraw, ImageTk, ImageFont


class PhotoshopColorPicker(tk.Toplevel):
    """
    A Photoshop-inspired RGBA color picker with:
    - HSV color wheel with triangle selector
    - Saved colors panel
    - HSV, RGB, and CMYK sliders
    - HEX input
    - Checkerboard preview with rounded rectangle
    """
    
    def __init__(self, parent=None, initial=(0, 255, 217, 210), title="Color Picker"):
        if parent is None:
            parent = tk.Tk()
            parent.withdraw()
            self._owns_root = True
        else:
            self._owns_root = False
            
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg='#3a3a3a')
        
        if not self._owns_root:
            self.transient(parent)
            self.grab_set()
        
        # State variables
        self.initial_color = initial
        r, g, b, a = initial
        self.r = r
        self.g = g
        self.b = b
        self.alpha = a
        self.h, self.s, self.v = self.rgb_to_hsv(r, g, b)
        self.c, self.m, self.y, self.k = utils.rgb_to_cmyk(r, g, b)
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_is_down = False
        self.mouse_is_down_and_was_in = "none"  # "wheel", "triangle"
        
        self.result = None
        self.saved_colors = []
        
        # UI elements references
        self.selected_checkerboard_theme = "dark"  # "light", "dark", "hight_contrast", "flat_light", "flat_dark"


        self.updating = False  # Track if we're updating from HSV to prevent hue drift
        self.ignore_rgb_updates = False  # Track if we're updating from HSV to prevent hue drift
        self.ignore_hsv_updates = False  # Track if we're updating from HSV to prevent hue drift
        self.ignore_cmyk_updates = False  # Track if we're updating from HSV to prevent hue drift
        self.ignore_alpha_updates = False  # Track if we're updating from HSV to prevent hue drift
        self.ignore_hex_updates = False  # Track if we're updating from HSV to prevent hue drift
        self.updating_finished = True  # Ensure we are done editing from color wheel.
        self.initial_draw = True
        self.color_wheel_canvas = None
        self.initial_wheel_image = None
        self.wheel_image = None
        self.initial_triangle_image = None
        self.triangle_points = []
        self.initial_checkerboard_image = None
        self.hue_marker = None
        self.sv_marker = None
        
        self.preview_canvas = None
        self.preview_image = None
        
        # Build UI
        self._build_ui()
        self._update_all()

    def set_ignore_flags(self, *ignore_flags):
        """
        Set all ignore update flags to False except the ones specified.
        
        Args:
            *ignore_flags: Variable number of strings specifying which flags to set to True.
                        Valid values: 'alpha', 'cmyk', 'rgb', "hsv"
        
        Example:
            self.set_ignore_flags('alpha', 'rgb')  # Only ignore alpha and rgb updates
            self.set_ignore_flags()  # All flags set to False (ignore nothing)
        """
        # Set all flags to False by default
        # self.ignore_alpha_updates = False
        # self.ignore_cmyk_updates = False
        # self.ignore_rgb_updates = False
        # self.ignore_hsv_updates = False
        
        # Set specified flags to True
        for flag in ignore_flags:
            if flag == 'alpha':
                self.ignore_alpha_updates = True
            elif flag == 'cmyk':
                self.ignore_cmyk_updates = True
            elif flag == 'rgb':
                self.ignore_rgb_updates = True
            elif flag == 'hsv':
                self.ignore_hsv_updates = True
            elif flag == 'hex':
                self.ignore_hex_updates = True
            else:
                raise ValueError(f"Invalid flag: {flag}. Valid options are: 'alpha', 'cmyk', 'rgb'")
    
    def reset_ignore_flags(self):
        # Set all flags to False by default
        self.ignore_alpha_updates = False
        self.ignore_cmyk_updates = False
        self.ignore_rgb_updates = False
        self.ignore_hsv_updates = False
        self.ignore_hex_updates = False

    def _build_ui(self):
        """Build the complete UI"""
        main_frame = tk.Frame(self, bg='#3a3a3a', padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Top section: Saved colors, color wheel, preview
        top_frame = tk.Frame(main_frame, bg='#3a3a3a')
        top_frame.pack(fill='x', pady=(0, 10))
        
        # Left: Saved colors
        self._build_saved_colors(top_frame)
        
        # Center: Color wheel and triangle
        self._build_color_wheel(top_frame)
        
        # Right: Preview
        self._build_preview(top_frame)
        
        # Middle section: Sliders
        slider_frame = tk.Frame(main_frame, bg='#3a3a3a')
        slider_frame.pack(fill='x', pady=(0, 10))
        
        # Left column: HSV and RGB sliders
        left_sliders = tk.Frame(slider_frame, bg='#3a3a3a')
        left_sliders.pack(side='left', fill='both', expand=True, padx=(0, 20))
        self._build_hsv_sliders(left_sliders)
        self._build_rgb_sliders(left_sliders)
        self._build_cmyk_sliders(left_sliders)
        
        # Right column: Color info and inputs
        right_info = tk.Frame(slider_frame, bg='#3a3a3a')
        right_info.pack(side='right', fill='y')
        self._build_color_info(right_info)
        
        # Bottom: Buttons
        self._build_buttons(main_frame)
        self.initial_draw = False
        
    def _build_saved_colors(self, parent):
        """Build saved colors panel"""
        frame = tk.Frame(parent, bg='#2a2a2a', relief='sunken', bd=1)
        frame.pack(side='left', padx=(0, 10))
        
        label = tk.Label(frame, text="Saved Colors", bg='#2a2a2a', fg='white', 
                        font=('Arial', 9))
        label.pack(pady=5)
        
        self.saved_colors_canvas = tk.Canvas(frame, width=240, height=440, 
                                             bg='#2a2a2a', highlightthickness=0)
        self.saved_colors_canvas.pack(padx=5, pady=(0, 5))
        
    def _build_color_wheel(self, parent):
        """Build HSV color wheel with triangle"""
        frame = tk.Frame(parent, bg='#3a3a3a')
        frame.pack(side='left', padx=(0, 10))
        
        self.color_wheel_canvas = tk.Canvas(frame, width=450, height=450, 
                                           bg='#4a4a4a', highlightthickness=0)
        self.color_wheel_canvas.pack()
        
        # Draw color wheel
        self._draw_color_wheel()
        
        
        # Bind mouse events
        self.color_wheel_canvas.bind('<Button-1>', self._on_wheel_click)
        self.color_wheel_canvas.bind('<B1-Motion>', self._on_wheel_drag)
        self.color_wheel_canvas.bind('<ButtonRelease-1>', self._on_wheel_release)
        
    def _build_preview(self, parent):
        """Build preview panel with checkerboard"""
        frame = tk.Frame(parent, bg='#2a2a2a', relief='sunken', bd=1)
        frame.pack(side='left')
        
        self.preview_canvas = tk.Canvas(frame, width=580, height=450, 
                                       bg='#2a2a2a', highlightthickness=0)
        self.preview_canvas.pack(padx=5, pady=5)
        
        # Draw checkerboard
        self._draw_checkerboard()
        
    def _build_hsv_sliders(self, parent):
        """Build HSV sliders"""
        hsv_frame = tk.Frame(parent, bg='#3a3a3a')
        hsv_frame.pack(fill='x', pady=(0, 10))
        
        self.h_slider = self._create_slider(hsv_frame, "H", "°", None, 0, 360, self.h, 
                                           self._on_hsv_change)
        self.s_slider = self._create_slider(hsv_frame, "S", "%", None, 0, 100, self.s * 100, 
                                           self._on_hsv_change)
        self.v_slider = self._create_slider(hsv_frame, "V", "%", None, 0, 100, self.v * 100, 
                                           self._on_hsv_change)
        
        self.h_slider.bind('<ButtonRelease-1>', self._on_hsv_slider_release)
        self.s_slider.bind('<ButtonRelease-1>', self._on_hsv_slider_release)
        self.v_slider.bind('<ButtonRelease-1>', self._on_hsv_slider_release)
        self.h_slider.bind('<Button-1>', self._on_hsv_slider_press)
        self.s_slider.bind('<Button-1>', self._on_hsv_slider_press)
        self.v_slider.bind('<Button-1>', self._on_hsv_slider_press)
        
    def _build_rgb_sliders(self, parent):
        """Build RGB sliders"""
        rgb_frame = tk.Frame(parent, bg='#3a3a3a')
        rgb_frame.pack(fill='x', pady=(0, 10))
        
        self.r_slider = self._create_slider(rgb_frame, "R", "", "#4C2A2A", 0, 255, self.r, 
                                           self._on_rgb_change)
        self.g_slider = self._create_slider(rgb_frame, "G", "", "#2F4C2A", 0, 255, self.g, 
                                           self._on_rgb_change)
        self.b_slider = self._create_slider(rgb_frame, "B", "", "#2A2B4C", 0, 255, self.b, 
                                           self._on_rgb_change)
        
        self.r_slider.bind('<ButtonRelease-1>', self._on_rgb_slider_release)
        self.g_slider.bind('<ButtonRelease-1>', self._on_rgb_slider_release)
        self.b_slider.bind('<ButtonRelease-1>', self._on_rgb_slider_release)
        self.r_slider.bind('<Button-1>', self._on_rgb_slider_press)
        self.g_slider.bind('<Button-1>', self._on_rgb_slider_press)
        self.b_slider.bind('<Button-1>', self._on_rgb_slider_press)
        
    def _build_cmyk_sliders(self, parent):
        """Build CMYK sliders"""
        cmyk_frame = tk.Frame(parent, bg='#3a3a3a')
        cmyk_frame.pack(fill='x')
        
        c, m, y, k = self.rgb_to_cmyk(self.r, self.g, self.b)
        
        self.c_slider = self._create_slider(cmyk_frame, "C", "%", "#2A4C4B", 0, 100, c, 
                                           self._on_cmyk_change)
        self.m_slider = self._create_slider(cmyk_frame, "M", "%", "#4A2A4C", 0, 100, m, 
                                           self._on_cmyk_change)
        self.y_slider = self._create_slider(cmyk_frame, "Y", "%", "#4C4C2A", 0, 100, y, 
                                           self._on_cmyk_change)
        self.k_slider = self._create_slider(cmyk_frame, "K", "%", "#4C4C4C", 0, 100, k, 
                                           self._on_cmyk_change)
        
        self.c_slider.bind('<ButtonRelease-1>', self._on_cmyk_slider_release)
        self.m_slider.bind('<ButtonRelease-1>', self._on_cmyk_slider_release)
        self.y_slider.bind('<ButtonRelease-1>', self._on_cmyk_slider_release)
        self.k_slider.bind('<ButtonRelease-1>', self._on_cmyk_slider_release)
        self.c_slider.bind('<Button-1>', self._on_cmyk_slider_press)
        self.m_slider.bind('<Button-1>', self._on_cmyk_slider_press)
        self.y_slider.bind('<Button-1>', self._on_cmyk_slider_press)
        self.k_slider.bind('<Button-1>', self._on_cmyk_slider_press)
        
    def _create_slider(self, parent, label, unit, color, from_, to, initial, command):
        """Create a slider row"""
        print(f"Creating slider: {label} with initial color {color} = {utils.is_valid_color(color)}")
        if utils.is_valid_color(color):
            print(f"Using custom color for {label} slider: {color}")
            bg_color = color
        else:
            print(f"Using default color for {label} slider")
            bg_color = '#2a2a2a'
        frame = tk.Frame(parent, bg='#3a3a3a')
        frame.pack(fill='x', pady=2)
        
        lbl = tk.Label(frame, text=label, bg='#3a3a3a', fg='white', 
                      font=('Arial', 9), width=2)
        lbl.pack(side='left', padx=(0, 5))
        
        slider = tk.Scale(frame, from_=from_, to=to, orient='horizontal',
                         bg='#4a4a4a', fg='white', troughcolor=bg_color,
                         highlightthickness=0, showvalue=0, length=600,
                         command=command)
        slider.set(initial)
        slider.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        value_label = tk.Label(frame, text=str(int(initial)), bg=bg_color, 
                              fg='white', font=('Arial', 9), width=5)
        value_label.pack(side='left', padx=(0, 5))
        
        unit = tk.Label(frame, text=unit, bg='#3a3a3a', fg='white', 
                       font=('Arial', 9), width=2)
        unit.pack(side='left')
        
        slider.value_label = value_label
        return slider
        
    def _build_color_info(self, parent):
        """Build color information display"""
        # Alpha slider
        alpha_frame = tk.Frame(parent, bg='#3a3a3a')
        alpha_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(alpha_frame, text="A", bg='#3a3a3a', fg='white', 
                font=('Arial', 9)).pack(side='left', padx=(0, 5))
        
        self.a_slider = tk.Scale(alpha_frame, from_=0, to=255, orient='horizontal',
                                bg='#4a4a4a', fg='white', troughcolor='#2a2a2a',
                                highlightthickness=0, showvalue=0, length=300,
                                command=self._on_alpha_change)
        self.a_slider.set(self.alpha)
        self.a_slider.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.a_value = tk.Label(alpha_frame, text=str(self.alpha), bg='#2a2a2a',
                               fg='white', font=('Arial', 9), width=5)
        self.a_value.pack(side='left', padx=(0, 5))
        
        tk.Label(alpha_frame, text="%", bg='#3a3a3a', fg='white',
                font=('Arial', 9)).pack(side='left')
        
        # HEX
        hex_frame = tk.Frame(parent, bg='#3a3a3a')
        hex_frame.pack(fill='x', pady=5)
        
        tk.Label(hex_frame, text="HEX:", bg='#3a3a3a', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        self.hex_var = tk.StringVar(value=self._rgb_to_hex(self.r, self.g, self.b))
        hex_entry = tk.Entry(hex_frame, textvariable=self.hex_var, bg='#2a2a2a',
                            fg='white', font=('Arial', 10), width=12,
                            insertbackground='white')
        hex_entry.pack(side='left')
        hex_entry.bind('<Return>', lambda e: self._on_hex_change())
        hex_entry.bind('<FocusOut>', lambda e: self._on_hex_change())
        
        # RGB
        rgb_frame = tk.Frame(parent, bg='#3a3a3a')
        rgb_frame.pack(fill='x', pady=5)
        
        tk.Label(rgb_frame, text="RGB:", bg='#3a3a3a', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        self.rgb_label = tk.Label(rgb_frame, text=f"{self.r},{self.g},{self.b}",
                                 bg='#2a2a2a', fg='white', font=('Arial', 10),
                                 width=12)
        self.rgb_label.pack(side='left')
        
        # HSV
        hsv_frame = tk.Frame(parent, bg='#3a3a3a')
        hsv_frame.pack(fill='x', pady=5)
        
        tk.Label(hsv_frame, text="HSV", bg='#3a3a3a', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        self.hsv_label = tk.Label(hsv_frame, 
                                 text=f"{int(self.h)},{int(self.s*100)},{int(self.v*100)}",
                                 bg='#2a2a2a', fg='white', font=('Arial', 10),
                                 width=12)
        self.hsv_label.pack(side='left')
        
        # CMYK
        cmyk_frame = tk.Frame(parent, bg='#3a3a3a')
        cmyk_frame.pack(fill='x', pady=5)
        
        tk.Label(cmyk_frame, text="CMYK:", bg='#3a3a3a', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        c, m, y, k = self.rgb_to_cmyk(self.r, self.g, self.b)
        self.cmyk_label = tk.Label(cmyk_frame, text=f"{int(c)},{int(m)},{int(y)},{int(k)}",
                                  bg='#2a2a2a', fg='white', font=('Arial', 10),
                                  width=12)
        self.cmyk_label.pack(side='left')
        
    def _build_buttons(self, parent):
        """Build bottom buttons"""
        btn_frame = tk.Frame(parent, bg='#3a3a3a')
        btn_frame.pack(side='bottom', pady=(10, 0))
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", bg='#4a4a4a', fg='white',
                              font=('Arial', 11), width=12, command=self._on_cancel,
                              relief='flat', bd=0, padx=20, pady=8)
        cancel_btn.pack(side='left', padx=(0, 20))
        
        save_btn = tk.Button(btn_frame, text="Save", bg='#4a4a4a', fg='white',
                            font=('Arial', 11), width=12, command=self._on_save,
                            relief='flat', bd=0, padx=20, pady=8)
        save_btn.pack(side='left')
        


    def _draw_color_wheel(self, svonly=False):
        """Draw HSV color wheel with triangle"""
        size = 450
        center = size // 2
        outer_radius = 220
        inner_radius = 165


        
        # Create image
        if self.initial_draw == True:
            # Draw color wheel (hue ring)
            img = Image.new('RGB', (size, size), "#4a4a4a00") #'#4a4a4a'
            draw = ImageDraw.Draw(img)
            for angle in range(360):
                rad = math.radians(angle)
                x1 = center + int(inner_radius * math.cos(rad))
                y1 = center + int(inner_radius * math.sin(rad))
                x2 = center + int(outer_radius * math.cos(rad))
                y2 = center + int(outer_radius * math.sin(rad))
                
                r, g, b = self.hsv_to_rgb(angle, 1.0, 1.0)
                color = f'#{r:02x}{g:02x}{b:02x}'
                
                # Draw thick line for each degree
                draw.line([(x1, y1), (x2, y2)], fill=color, width=6)

            self.initial_wheel_image = img.copy()
        else:
            img = self.initial_wheel_image.copy()
            draw = ImageDraw.Draw(img)

        # # Draw triangle for S/V selection
        # if svonly == False or self.initial_draw == True:
        #     # Create triangle image
        #     # tri_img = Image.new('RGBA', (size, size), "#7c7c7c00") #'#4a4a4a'
        #     # tri_draw = ImageDraw.Draw(tri_img)
        #     self._draw_sv_triangle(img, center, inner_radius)
        #     #img.save("debug_triangle.png")
            

        #     # Now edit the main image to add created triangle image
        #     #self._draw_sv_triangle(img, center, inner_radius)
        # else:
        #     img = self.initial_triangle_image.copy()
        #     draw = ImageDraw.Draw(img)

        self._draw_sv_triangle(img, center, inner_radius)
            
            
        # Convert to PhotoImage
        self.wheel_image = ImageTk.PhotoImage(img)
        self.color_wheel_canvas.create_image(0, 0, anchor='nw', image=self.wheel_image)
        
        # Draw markers
        self._draw_wheel_markers()
        


    def _draw_sv_triangle(self, img, center, radius):
        """Draw saturation/value triangle"""
        radius_offset = 30 # Padding from inner edge of wheel to triangle vertex
        # Calculate triangle points based on current hue
        if self.initial_draw == True:
            angle_offset = math.radians(0)  # Pointing up
        else:
            angle_offset = math.radians(self.h)
            
        points = []
        for i in range(3):
            angle = angle_offset + (i * 2 * math.pi / 3)
            x = center + int((radius - radius_offset) * math.cos(angle))
            y = center + int((radius - radius_offset) * math.sin(angle))
            points.append((x, y))
            #draw.point((x, y), fill="transparent")
        
        self.triangle_points = points

        if self.initial_draw == True:
            tri_img = Image.new('RGBA', (450, 450), "#7c7c7c00") #'#4a4a4a'
            tri_draw = ImageDraw.Draw(tri_img)
            # Create first triangle image
            
            # Fill triangle with gradient (simplified - just draw from corners)
            # Top vertex: white (S=0, V=1)
            # Bottom-left: black (S=any, V=0)
            # Bottom-right: pure hue (S=1, V=1)
            
            # Sample points within triangle and color them
            # steps = 50
            # dot_size = 7

            steps = 255
            dot_size = 1
            print(f"\n\n{self.h}\n\n")
            for i in range(steps):
                for j in range(steps - i):
                    # Barycentric coordinates
                    w = 1 - (i + j) / steps  # Weight for p0 (white)
                    u = i / steps             # Weight for p1 (black)
                    v = j / steps             # Weight for p2 (pure hue)
                    
                    if w < 0:
                        continue
                    
                    # Map to S/V
                    # sat = w / (w + v) if (w + v) > 0 else 0
                    sat = w / (w + v) if (w + v) > 0 else 0
                    val = w + v

                    #r, g, b = self.hsv_to_rgb(self.h, sat, val)
                    r, g, b = self.hsv_to_rgb(0.0, sat, val)
                    #color = f'#{r:02x}{g:02x}{b:02x}'
                    color = (r, g, b, 255)

                    
                    x = int(points[0][0] * w + points[1][0] * u + points[2][0] * v)
                    y = int(points[0][1] * w + points[1][1] * u + points[2][1] * v)
                    
                    # 
                    tri_draw.ellipse([(x-dot_size/2, y-dot_size/2), (x+dot_size/2, y+dot_size/2)], fill=color)

            tri_img.save("debug_triangle.png")

            self.initial_triangle_image = tri_img.copy() # Save base triangle image
        else:
            tri_img = self.initial_triangle_image.copy()
            tri_draw = ImageDraw.Draw(tri_img)

        #print(self.h)

        tri_img = utils.shift_image_hue_rgba(tri_img, (self.h/360)*255)
        tri_img = tri_img.rotate(-self.h, resample=Image.BICUBIC, center=(center, center), expand=False)

        # Center the rotated foreground on the background
        bg_w, bg_h = img.size
        fg_w, fg_h = tri_img.size
        pos = ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2)

        img.paste(tri_img, pos, tri_img)  # uses alpha channel of rotated_fg as mask

            
        

        
        

        
        # BACKUP
         # steps = 255
        # dot_size = 1
        # for i in range(steps):
        #     for j in range(steps - i):
        #         # Barycentric coordinates
        #         w = 1 - (i + j) / steps  # Weight for p0 (white)
        #         u = i / steps             # Weight for p1 (black)
        #         v = j / steps             # Weight for p2 (pure hue)
                
        #         if w < 0:
        #             continue
                
        #         # Map to S/V
        #         # sat = w / (w + v) if (w + v) > 0 else 0
        #         sat = w / (w + v) if (w + v) > 0 else 0
        #         val = w + v
                
        #         r, g, b = self.hsv_to_rgb(self.h, sat, val)
        #         color = f'#{r:02x}{g:02x}{b:02x}'
                
        #         x = int(points[0][0] * w + points[1][0] * u + points[2][0] * v)
        #         y = int(points[0][1] * w + points[1][1] * u + points[2][1] * v)
                
        #         # 
        #         draw.ellipse([(x-dot_size/2, y-dot_size/2), (x+dot_size/2, y+dot_size/2)], fill=color)


                
                
                
        
    def _draw_wheel_markers(self):
        """Draw hue and S/V markers on wheel"""
        center = 225
        
        # Hue marker on ring
        angle = math.radians(self.h - 0)
        radius = 192.5  # Middle of ring
        x = center + int(radius * math.cos(angle))
        y = center + int(radius * math.sin(angle))
        
        if self.hue_marker:
            self.color_wheel_canvas.delete(self.hue_marker)
        
        self.hue_marker = self.color_wheel_canvas.create_oval(
            x - 6, y - 6, x + 6, y + 6,
            outline='white', width=2, fill=''
        )
        
        # S/V marker in triangle
        if len(self.triangle_points) == 3:
            # Calculate position based on S and V
            p0, p1, p2 = self.triangle_points
        
            # Convert S/V to barycentric (inverse of the click calculation)
            w = self.v * self.s         # Weight for p0 (pure hue) - swapped
            v = self.v * (1 - self.s)   # Weight for p2 (white point) - swapped
            u = 1 - w - v               # Weight for p1 (black point)
            
            x = int(p0[0] * w + p1[0] * u + p2[0] * v)
            y = int(p0[1] * w + p1[1] * u + p2[1] * v)
            
            if self.sv_marker:
                self.color_wheel_canvas.delete(self.sv_marker)
            
            self.sv_marker = self.color_wheel_canvas.create_oval(
                x - 6, y - 6, x + 6, y + 6,
                outline='white', width=2, fill=''
            )
    
    def _draw_checkerboard(self):
        """Draw checkerboard background for preview"""
        width, height = 580, 450
        class color_pad:
            top = 55
            left = 30
            bottom = 20
            right = 30

        tile = 20

        checkerboard_themes = {
            "light": ("#cccccc", "#999999"),
            "dark": ("#0E0E0E", "#2B2B2B"),
            "high_contrast": ("#202020", "#C4C4C4"),
            "flat_light": ("#dddddd", "#dddddd"),
            "flat_dark": ("#1b1b1b", "#1b1b1b"),
        }




        rgba = (self.r, self.g, self.b, self.alpha)

        # Draw rounded rectangle with current color
        rect_width, rect_height = width - (color_pad.left + color_pad.right), (height / 2) - (color_pad.top + color_pad.bottom)
        rect_x = color_pad.left
        rect_y = color_pad.top

        if self.initial_draw == True:
        
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            for y in range(0, height, tile):
                for x in range(0, width, tile):
                    #color = '#cccccc' if (x // tile + y // tile) % 2 == 0 else '#999999'
                    color = checkerboard_themes[self.selected_checkerboard_theme][0] if (x // tile + y // tile) % 2 == 0 else checkerboard_themes[self.selected_checkerboard_theme][1]
                    draw.rectangle([x, y, x + tile, y + tile], fill=color)

            

            # Create overlay with alpha
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            font = ImageFont.truetype("arialbd.ttf", 35)
            
            overlay_draw.rectangle(
                [0, 0, width, height],
                fill=(0,0,0,0),
                outline="#242424",
                width=20,
            )
            overlay_draw.rectangle(
                [0, 0, width, 40],
                fill="#242424",
            )
            overlay_draw.rectangle(
                [0, height-40, width, height],
                fill="#242424",
            )

            # Center Line
            overlay_draw.rectangle(
                [0, (height/2)-5, width, (height/2)+5],
                fill="#242424"
            )
            overlay_draw.text((width/2, 7), "NEW COLOR", fill="#DBDBDB", font=font, anchor="mt")
            overlay_draw.text((width/2, height-7), "SAVED COLOR", fill="#DBDBDB", font=font, anchor="mb")
            

            i_rect_width, i_rect_height = width - (color_pad.left + color_pad.right), (height / 2) - (color_pad.bottom + color_pad.top)
            i_rect_x = color_pad.left
            i_rect_y = (height/2) + color_pad.bottom

            # Saved Color
            overlay_draw.rounded_rectangle(
                [i_rect_x, i_rect_y, i_rect_x + i_rect_width, i_rect_y + i_rect_height],
                radius=15,
                fill=self.initial_color
            )

            

            # Composite
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')

            self.initial_checkerboard_image = img.copy()
        else:
            img = self.initial_checkerboard_image.copy()
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)


        # New Color
        overlay_draw.rounded_rectangle(
            [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
            radius=15,
            fill=rgba
        )
        
        # Composite
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        self.preview_image = ImageTk.PhotoImage(img)
        self.preview_canvas.delete('all')
        self.preview_canvas.create_image(0, 0, anchor='nw', image=self.preview_image)
    
    def _on_wheel_click(self, event):
        """Handle clicks on color wheel"""
        self.set_ignore_flags("alpha","rgb","cmyk","hsv")
        self.mouse_is_down = True
        self.mouse_is_down_and_was_in = "none"
        self._on_wheel_drag(event)
    
    def _on_wheel_drag(self, event):
        """Handle dragging on color wheel"""
        if not self.mouse_is_down:
            return
        center_x, center_y = 225, 225
        # print(f"event.x={event.x}, event.y={event.y}")
        dx = event.x - center_x
        dy = event.y - center_y
        # print(f"dx={dx}, dy={dy}")
        distance = math.sqrt(dx * dx + dy * dy)
        

        # Check if in hue ring (165-220 pixels from center)
        if (165 <= distance <= 220 and self.mouse_is_down_and_was_in != "triangle") or self.mouse_is_down_and_was_in == "wheel":
            # Update hue
            self.mouse_is_down_and_was_in = "wheel"  # Keep true until mouse release
            angle = math.degrees(math.atan2(dy, dx))
            if angle < 0:
                angle += 360
            if self.mouse_is_down == True:
                self.h = angle % 360
            self.updating = True
            
            self.updating_finished = False
            self._update_from_hsv(svonly=False)
            # utils.multithread_func(self, lambda: self._update_from_hsv(svonly=False), True, False, None, True, "_update_from_hsv")
        # Check if in triangle (distance < 165)
        elif distance < (165) or self.mouse_is_down_and_was_in == "triangle":
            # Check if point is inside triangle
            if self.mouse_is_down_and_was_in != "wheel" or (self._point_in_triangle(event.x, event.y) and self.mouse_is_down_and_was_in != "wheel"):
                # Calculate S/V from position
                self.mouse_is_down_and_was_in = "triangle" # Keep true until mouse release

                self.updating = True
                self.updating_finished = False
                self._update_sv_from_point(event.x, event.y)  # doesn't touch self.h
                # Debug: Check if hue changed
                
                #print(f"Current Mouse X:{event.x}, Y:{event.y}")
                self._update_from_hsv(svonly=True)
                # utils.multithread_func(self, lambda: self._update_from_hsv(svonly=True), True, False, None, True, "_update_from_hsv")
        #print(f"{utils.Fore.YELLOW}HSV UPDATED! h={self.h}, s={self.s}, v={self.v}{utils.Style.RESET_ALL}")


    def _on_wheel_release(self, event):
        """Handle mouse button release on color wheel"""
        #print("Mouse button released!")
        # self.updating_from_hsv = False
        #self.reset_ignore_flags()
        #self.updating = False
        #print(f"{utils.Fore.RED}FINISHED Mouse X:{event.x}, Y:{event.y}{utils.Style.RESET_ALL}")
        #self._updating_finished()
        self.mouse_is_down = False
        #print(f"mouse_is_down = false")
        utils.cancel_thread(None, "slow_update_cmyk_rgb_sliders")
        #print(f"cancel_thread")
        
        self._updating_finished()
        #print(f"finished _updating_finished")
        #print(f"After release - H:{self.h}, S:{self.s}, V:{self.v}")
        #print(f"After release - R:{self.r}, G:{self.g}, B:{self.b}")
        
        #self._update_all()
        # You can add any cleanup or final actions here
        #pass

    def _on_hsv_slider_press(self, event=None):
        """Handle HSV slider button press"""
        #print("HSV slider pressed!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        # self.updating_from_hsv = True
        self.set_ignore_flags("alpha","rgb","cmyk","hex")
        #self.updating = True
        self.mouse_is_down = True
        self.updating_finished = False
        self._update_from_hsv()
        # utils.multithread_func(self, self._update_from_hsv, True, False, None, True, "_update_from_hsv")
        

    def _on_hsv_slider_release(self, event=None):
        """Handle HSV slider button release"""
        #print("HSV slider released!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        #self.reset_ignore_flags()
        self.mouse_is_down = False
        self._updating_finished()
        #print(f"After release - H:{self.h}, S:{self.s}, V:{self.v}")
        #print(f"After release - R:{self.r}, G:{self.g}, B:{self.b}")
        utils.cancel_thread(None, "slow_update_cmyk_rgb_sliders")
        
        
        #self._update_all()

    def _on_rgb_slider_press(self, event=None):
        """Handle RGB slider button press"""
        #print("RGB slider pressed!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        # self.updating_from_hsv = True
        self.set_ignore_flags("alpha","hsv","cmyk","hex")
        self.mouse_is_down = True
        self.updating_finished = False
        #self.updating = True
        self._update_from_rgb()

    def _on_rgb_slider_release(self, event=None):
        """Handle RGB slider button release"""
        #print("RGB slider released!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        #self.reset_ignore_flags()
        #self.updating = False
        self.mouse_is_down = False
        self._updating_finished()
        utils.cancel_thread(None, "slow_update_cmyk_hsv_sliders")
        #self._update_all()

    def _on_cmyk_slider_press(self, event=None):
        """Handle CMYK slider button press"""
        #print("CMYK slider pressed!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        # self.updating_from_hsv = True
        self.set_ignore_flags("alpha","rgb","hsv","hex")
        self.updating_finished = False
        self.mouse_is_down = True
        #self.updating = True
        self._update_from_cmyk()

    def _on_cmyk_slider_release(self, event=None):
        """Handle CMYK slider button release"""
        #print("CMYK slider released!")
        # You can add any cleanup or finalization here
        # For example, you might want to finalize the updating_from_hsv flag
        #self.reset_ignore_flags()
        self.mouse_is_down = False
        self._updating_finished()
        utils.cancel_thread(None, "slow_update_hsv_rgb_sliders")
        #self.updating = False
        #self._update_all()
    
    def _point_in_triangle(self, px, py):
        """Check if point is inside triangle"""
        if len(self.triangle_points) != 3:
            return False
        
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        
        p = (px, py)
        d1 = sign(p, self.triangle_points[0], self.triangle_points[1])
        d2 = sign(p, self.triangle_points[1], self.triangle_points[2])
        d3 = sign(p, self.triangle_points[2], self.triangle_points[0])
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def _update_sv_from_point(self, px, py):
        """Update saturation and value from triangle point"""
        if len(self.triangle_points) != 3:
            return
        
        p0, p1, p2 = self.triangle_points
        
        # Calculate barycentric coordinates
        v0x, v0y = p1[0] - p0[0], p1[1] - p0[1]
        v1x, v1y = p2[0] - p0[0], p2[1] - p0[1]
        v2x, v2y = px - p0[0], py - p0[1]
        
        dot00 = v0x * v0x + v0y * v0y
        dot01 = v0x * v1x + v0y * v1y
        dot02 = v0x * v2x + v0y * v2y
        dot11 = v1x * v1x + v1y * v1y
        dot12 = v1x * v2x + v1y * v2y
        
        denom = dot00 * dot11 - dot01 * dot01
        if abs(denom) < 1e-10:
            return
            
        inv_denom = 1 / denom
        u = (dot11 * dot02 - dot01 * dot12) * inv_denom  # Weight for p1
        v = (dot00 * dot12 - dot01 * dot02) * inv_denom  # Weight for p2
        w = 1 - u - v  # Weight for p0
        
        # Clamp to triangle
        w = max(0, min(1, w))
        u = max(0, min(1, u))
        v = max(0, min(1, v))
        
        # Normalize if outside
        total = w + u + v
        if total > 0:
            w /= total
            u /= total
            v /= total

        # print(f"Before release - H:{self.h}, S:{self.s}, V:{self.v}")
        # print(f"Before release - R:{self.r}, G:{self.g}, B:{self.b}")
        
        # Convert to S/V (same formula as drawing)
        self.s = w / (w + v) if (w + v) > 0 else 0
        self.v = w + v
    
    def _on_hsv_change(self, val=None):
        """Handle HSV slider changes"""
        if self.updating:
            return
        elif self.ignore_hsv_updates:
            return
        elif not self.mouse_is_down:
            return
        
        # if not self.winfo_containing(*self.winfo_pointerxy()):
        #     return
        
        #print(f"{utils.Fore.YELLOW}HSV UPDATED! h={self.h}, s={self.s}, v={self.v}{utils.Style.RESET_ALL}")
        self.h = int(self.h_slider.get())
        self.s = (self.s_slider.get() / 100)
        self.v = self.v_slider.get() / 100
        #print("""Handle HSV slider changes""")
        
        self._update_from_hsv()
        # utils.multithread_func(self, self._update_from_hsv, True, False, None, True, "_update_from_hsv")

    
    def _on_rgb_change(self, val=None):
        """Handle RGB slider changes"""
        if self.updating:
            return
        elif self.ignore_rgb_updates:
            return
        elif not self.mouse_is_down:
            return
        #print(f"{utils.Fore.RED}RGB UPDATED! r={self.r}, g={self.g}, b={self.b}{utils.Style.RESET_ALL}")
        self.r = int(self.r_slider.get())
        self.g = int(self.g_slider.get())
        self.b = int(self.b_slider.get())

        #print(f"RGB IS CHANING! YIKES!")
        
        self._update_from_rgb()
    
    def _on_cmyk_change(self, val=None):
        """Handle CMYK slider changes"""
        if self.updating:
            return
        elif self.ignore_cmyk_updates:
            return
        elif not self.mouse_is_down:
            return
        #print(f"{utils.Fore.BLUE}CMYK UPDATED! c={self.c}, m={self.m}, y={self.y}, k={self.k}{utils.Style.RESET_ALL}")
        self.c = self.c_slider.get()
        self.m = self.m_slider.get()
        self.y = self.y_slider.get()
        self.k = self.k_slider.get()
        
        # self.r, self.g, self.b = self.cmyk_to_rgb(c, m, y, k)
        #self.c, self.m, self.y, self.k = self.rgb_to_cmyk(c, m, y, k)
        
        self._update_from_cmyk()
    
    def _on_alpha_change(self, val=None):
        """Handle alpha slider change"""
        if self.ignore_alpha_updates:
            return
        
        self.alpha = int(self.a_slider.get())
        self.a_value.config(text=str(self.alpha))
        self._draw_checkerboard()
    
    def _on_hex_change(self):
        """Handle HEX input change"""
        if self.updating:
            return
        elif self.ignore_hex_updates:
            return
        hex_val = self.hex_var.get().strip().lstrip('#')
        try:
            if len(hex_val) == 6:
                self.r = int(hex_val[0:2], 16)
                self.g = int(hex_val[2:4], 16)
                self.b = int(hex_val[4:6], 16)
                
                self._update_from_rgb()
        except ValueError:
            pass

    
    def _update_from_hsv(self, svonly=False):
        """Update RGB from HSV"""
        self.r, self.g, self.b = self.hsv_to_rgb(self.h, self.s, self.v)
        self.c, self.m, self.y, self.k = utils.rgb_to_cmyk(self.r, self.g, self.b)
        if svonly:
            # Only update S and V sliders, not H
            self.s_slider.set(self.s * 100)
            self.v_slider.set(self.v * 100)
            self.s_slider.value_label.config(text=str(int(self.s * 100)))
            self.v_slider.value_label.config(text=str(int(self.v * 100)))
            self.hsv_label.config(text=f"{int(self.h)},{int(self.s*100)},{int(self.v*100)}")
            # self._update_hex_text()
            # self._draw_checkerboard()
        else:
            self._update_hsv_sliders()

        self._slow_update_other_sliders("rgb","cmyk")
        self._update_all(svonly=svonly)
        #utils.multithread_func(self, lambda: self._slow_update_other_sliders("rgb","cmyk"), True, False, None, True, "slow_update_cmyk_rgb_sliders")

    def _update_from_rgb(self):
        """Update HSV from RGB"""
        self.h, self.s, self.v = self.rgb_to_hsv(self.r, self.g, self.b)
        self.c, self.m, self.y, self.k = utils.rgb_to_cmyk(self.r, self.g, self.b)
        self._update_rgb_sliders()
        self._slow_update_other_sliders("hsv","cmyk","wheel","checkerboard")
        self._update_all()
        #utils.multithread_func(self, lambda: self._slow_update_other_sliders("hsv","cmyk","wheel","checkerboard"), True, False, None, True, "slow_update_cmyk_hsv_sliders")
        #self._update_all()

    def _update_from_cmyk(self):
        """Update HSV from CMYK"""
        # self.r, self.g, self.b = utils.cmyk_to_rgb(self.c, self.m, self.y, self.k)
        self.r, self.g, self.b = utils.cmyk_to_rgb(self.c, self.m, self.y, self.k)
        self.h, self.s, self.v = self.rgb_to_hsv(self.r, self.g, self.b)
        self._update_cmyk_sliders()
        self._slow_update_other_sliders("hsv","rgb","wheel","checkerboard")
        self._update_all()
        #utils.multithread_func(self, lambda: self._slow_update_other_sliders("rgb","hsv","wheel","checkerboard"), True, False, None, True, "slow_update_hsv_rgb_sliders")
        #self._update_all()




    def _update_cmyk_sliders(self):
        self.c_slider.set(self.c)
        self.m_slider.set(self.m)
        self.y_slider.set(self.y)
        self.k_slider.set(self.k)

        self.c_slider.value_label.config(text=str(int(self.c)))
        self.m_slider.value_label.config(text=str(int(self.m)))
        self.y_slider.value_label.config(text=str(int(self.y)))
        self.k_slider.value_label.config(text=str(int(self.k)))

        self.cmyk_label.config(text=f"{int(self.c)},{int(self.m)},{int(self.y)},{int(self.k)}")

    def _update_rgb_sliders(self):
        self.r_slider.set(self.r)
        self.g_slider.set(self.g)
        self.b_slider.set(self.b)

        self.r_slider.value_label.config(text=str(self.r))
        self.g_slider.value_label.config(text=str(self.g))
        self.b_slider.value_label.config(text=str(self.b))

        self.rgb_label.config(text=f"{self.r},{self.g},{self.b}")

    def _update_hsv_sliders(self):

        self.h_slider.config(command=lambda x: None)
        self.s_slider.config(command=lambda x: None)
        self.v_slider.config(command=lambda x: None)

        self.h_slider.set(self.h)
        self.s_slider.set(self.s * 100)
        self.v_slider.set(self.v * 100)

        self.h_slider.value_label.config(text=str(int(self.h)))
        self.s_slider.value_label.config(text=str(int(self.s * 100)))
        self.v_slider.value_label.config(text=str(int(self.v * 100)))

        self.hsv_label.config(text=f"{int(self.h)},{int(self.s*100)},{int(self.v*100)}")

        self.h_slider.config(command=self._on_hsv_change)
        self.s_slider.config(command=self._on_hsv_change)
        self.v_slider.config(command=self._on_hsv_change)
    
    def _update_hex_text(self):
        self.hex_var.set(self._rgb_to_hex(self.r, self.g, self.b))

    
    def _update_all(self, svonly=False):
        """Update all UI elements"""

        self._update_hex_text()

        self._draw_color_wheel(svonly)
        self._draw_checkerboard()


    def _updating_finished(self):

        utils.multithread_func(self, self.__delayed_updating_finished,True,True)
        
        if not self.updating_finished:
            self.updating_finished = True
            print("finished updating from hsv")

        self.reset_ignore_flags()
        self._update_cmyk_sliders()
        self._update_hsv_sliders()
        self._update_rgb_sliders()
        

        
        
    def __delayed_updating_finished(self):
        self.updating = False
        self.updating_finished = False



    def _slow_update_other_sliders(self, *sliders):
        """Available Sliders: "rgb", "hsv", "cmyk" """
        #utils.sleep(0.01)
        for slider in sliders:
            slider = str.lower(slider)
            if slider == "rgb":
                self._update_rgb_sliders()
            elif slider == "hsv":
                self._update_hsv_sliders()
            elif slider == "cmyk":
                self._update_cmyk_sliders()
        


        


        
    
    # Color conversion methods
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    
    def rgb_to_hsv(self, r, g, b):
        """Convert RGB to HSV"""
        r, g, b = r / 255, g / 255, b / 255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c
        
        if diff == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360
        
        s = 0 if max_c == 0 else diff / max_c
        v = max_c
        
        return h, s, v
    
    def rgb_to_cmyk(self, r, g, b):  #self.rgb_to_cmyk   #self.rgb_to_cmyk
        """PLACEBO!!! USE 'utils.rgb_to_cmyk' FOR ACCURATE Convert RGB to CMYK"""
        if r == 0 and g == 0 and b == 0:
            return 0, 0, 0, 100
        
        r, g, b = r / 255, g / 255, b / 255
        k = 1 - max(r, g, b)
        c = (1 - r - k) / (1 - k) if k != 1 else 0
        m = (1 - g - k) / (1 - k) if k != 1 else 0
        y = (1 - b - k) / (1 - k) if k != 1 else 0
        
        return int(c * 100), int(m * 100), int(y * 100), int(k * 100)
    
    def cmyk_to_rgb(self, c, m, y, k):  #self.cmyk_to_rgb  #self.cmyk_to_rgb
        """PLACEBO!!! USE 'utils.cmyk_to_rgb' FOR ACCURATE Convert CMYK to RGB"""
        c, m, y, k = c / 100, m / 100, y / 100, k / 100
        r = 255 * (1 - c) * (1 - k)
        g = 255 * (1 - m) * (1 - k)
        b = 255 * (1 - y) * (1 - k)
        return int(r), int(g), int(b)
    
    def _rgb_to_hex(self, r, g, b):
        """Convert RGB to hex string"""
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _on_save(self):
        """Save and close"""
        self.result = (self.r, self.g, self.b, self.alpha)
        self.destroy()
    
    def _on_cancel(self):
        """Cancel and close"""
        self.result = None
        self.destroy()
    
    def show(self):
        """Show dialog and wait for result"""
        self.wait_window(self)
        return self.result


if __name__ == '__main__':
    # Test the color picker
    picker = PhotoshopColorPicker(initial=(0, 255, 217, 210))
    result = picker.show()
    
    if result:
        print(f"Selected color: RGBA{result}")
    else:
        print("Cancelled")