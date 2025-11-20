import customtkinter as ctk
import utils
from tkinter import messagebox


class ButtonGeneratorApp:
    def __init__(self):
        # Initialize the main window
        self.root = ctk.CTk()
        self.root.title("Dynamic Button Generator")
        self.root.geometry("500x600")
        
        # Set theme and color
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        
        # Dictionary mapping button names to functions
        # Add your custom buttons and functions here
        self.button_dict = {
            "Show Info": self.show_info,
            "Test v_Color_Picker.py": self.test_color_picker,
            "Test color_picker_redesign.py": self.test_color_picker_redesign,
            "Test Button": self.test_button,
        }
        
        # Create the UI
        self.create_ui()
        self.last_saved_color = (255, 0, 0, 255)
    
    def create_ui(self):
        """Create the user interface with procedurally generated buttons"""
        # Title label
        title_label = ctk.CTkLabel(
            self.root,
            text="Dynamic Button Interface",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Description label
        desc_label = ctk.CTkLabel(
            self.root,
            text="Buttons are generated from the button_dict",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 20))
        
        # Create a scrollable frame for buttons
        self.button_frame = ctk.CTkScrollableFrame(
            self.root,
            width=400,
            height=400
        )
        self.button_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Procedurally generate buttons from the dictionary
        self.generate_buttons()
    
    def generate_buttons(self):
        """Procedurally generate buttons based on the button_dict"""
        for button_name, button_function in self.button_dict.items():
            button = ctk.CTkButton(
                self.button_frame,
                text=button_name,
                command=button_function,
                width=350,
                height=40,
                font=ctk.CTkFont(size=14)
            )
            button.pack(pady=10, padx=20)
    
    # Define your custom functions below
    # These are example functions - replace with your own!
    
    def show_info(self):
        """Example function 2"""
        info_text = f"Total buttons: {len(self.button_dict)}\n"
        info_text += f"Button names: {', '.join(self.button_dict.keys())}"
        messagebox.showinfo("Information", info_text)


    def test_color_picker(self):
        """Test v_Color_Picker"""
        initial_color = (25,25,255,255)
        import v_Color_Picker
        picker = v_Color_Picker.RGBAColorPicker(
            None,
            initial=(25, 25, 255, 255),
            rect_size=(250, 40),
            radius=6,
            title="Edit Color"
        )
        result = picker.show()
        new_r, new_g, new_b, new_a_255 = result
        messagebox.showinfo("", f"Initial Color: {str(initial_color)}\n\nReturned Color: {result}")

    def test_color_picker_redesign(self):
        """Test color_picker_redesign"""
        import color_picker_redesign
        picker = color_picker_redesign.PhotoshopColorPicker(
            self.root,
            initial=self.last_saved_color,
            title="Edit Color"
        )
        result = picker.show()
        self.last_saved_color = result if result else self.last_saved_color
        new_r, new_g, new_b, new_a_255 = result if result else self.last_saved_color
        print(f"\nRGB->CMYK = {utils.rgb_to_cmyk(new_r, new_g, new_b)}")
        new_c,new_m,new_y,new_k = utils.rgb_to_cmyk(new_r, new_g, new_b)
        print(f"CMYK->RGB = {utils.cmyk_to_rgb(new_c, new_m, new_y, new_k)}")
        #messagebox.showinfo("", f"Initial Color: {str(initial_color)}\n\nReturned Color: {result}")

    def test_button(self):
        """Test button for code snippets"""
        import test
        # r, g, b, a = (50,25,230,0)
        # print(f"Start RGBA: {r}, {g}, {b}, {a}")
        # def test_func(c,m,y,k):
        #     print(f"Inside test_func CMYK: {c}, {m}, {y}, {k}")
        #     return utils.cmyk_to_rgb(c, m, y, k)
        # print(f"Returned CMYK Convert: {utils.multithread_func(self, lambda: utils.rgb_to_cmyk((r, g, b)), True, True, lambda cmyk: test_func(*cmyk), True, 'rgba_to_hex')}")

    # def rgb_to_cmyk(self, r, g, b):
    #     """Convert RGB to CMYK"""
    #     print(f"{utils.Fore.RED}rgb_to_cmyk: {r}, {g}, {b}{utils.Style.RESET_ALL}")
    #     if r == 0 and g == 0 and b == 0:
    #         return 0, 0, 0, 100
        
    #     r, g, b = r / 255, g / 255, b / 255
    #     k = 1 - max(r, g, b)
    #     c = (1 - r - k) / (1 - k) if k != 1 else 0
    #     m = (1 - g - k) / (1 - k) if k != 1 else 0
    #     y = (1 - b - k) / (1 - k) if k != 1 else 0
        
    #     return int(c * 100), int(m * 100), int(y * 100), int(k * 100)
    
    # def cmyk_to_rgb(self, c, m, y, k):
    #     """Convert CMYK to RGB"""
    #     print(f"{utils.Fore.BLUE}cmyk_to_rgb: {c}, {m}, {y}, {k}{utils.Style.RESET_ALL}")
    #     c, m, y, k = c / 100, m / 100, y / 100, k / 100
    #     r = 255 * (1 - c) * (1 - k)
    #     g = 255 * (1 - m) * (1 - k)
    #     b = 255 * (1 - y) * (1 - k)
    #     return int(r), int(g), int(b)
    
    
    
    def run(self):
        """Start the application"""
        self.root.mainloop()



if __name__ == "__main__":
    # Create and run the application
    app = ButtonGeneratorApp()
    app.run()