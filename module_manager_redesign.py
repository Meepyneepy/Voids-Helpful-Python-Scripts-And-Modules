
import utils
# import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
import sys
import importlib.util
import ast
import os



module_translation = {
    "PIL": "pillow"
}


def extract_imports_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=filepath)
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                #print(f"{utils.Fore.LIGHTCYAN_EX}ast.Import: alias = {alias.name}{utils.Fore.RESET}")
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                #print(f"{utils.Fore.LIGHTGREEN_EX}ast.ImportFrom: node.module = {node.module}{utils.Fore.RESET}")
                imports.add(node.module.split('.')[0])
    return list(imports)


def check_missing_imports(module_list):
    missing = []
    for module in module_list:
        if module in sys.builtin_module_names:
            continue
        try:
            importlib.import_module(module)
        except ImportError:
            try:
                importlib.import_module(module_translation.get(module, module))
            except ImportError:
                missing.append(module_translation.get(module, module))
    return missing



class ModuleCheckerAPP(tk.Toplevel):
    def __init__(self, parent = None, module_name=""):
        if parent is None:
            parent = tk.Tk()
            parent.withdraw()
            self._owns_root = True
        else:
            self._owns_root = False
            
        super().__init__(parent)

        self.result = None

        main = ttk.Frame(self, padding=8)
        main.grid(row=0, column=0, sticky="nsew")
        # Allow the main frame to expand with the Toplevel window so child widgets
        # that use pack(fill="both", expand=True) can grow instead of being cut off.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

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
        # style.configure('TButton', background=self.bg_color, foreground=self.fg_color, highlightcolor=self.accent_color, highlightbackground=self.fg_color)
        style.map('TButton',
            background=[('active', "#3D3D3D"), ('!active', self.bg_color)],
            foreground=[('active', "#FFFFFF"), ('!active', self.fg_color)])
        self.configure(bg=self.bg_color)
        main.configure(style='TFrame')


        self.current_directory = os.getcwd()
        self.full_path = os.path.join(self.current_directory, module_name)
        if os.path.isfile(self.full_path) and self.full_path.endswith(".py"):
            self.file_name = os.path.splitext(self.full_path)[0]

            spec = importlib.util.spec_from_file_location(self.file_name, self.full_path)
            mod = importlib.util.module_from_spec(spec)

        self.imports = extract_imports_from_file(self.full_path)
        self.missing_imports = check_missing_imports(self.imports)

        self.title(f"Install missing modules for '{self.file_name}'")
        self.geometry("400x400")

        if not self._owns_root:
            self.transient(parent)
            self.grab_set()

        self.missing = self.missing_imports
        self.vars = {}

        ttk.Label(main, text="Missing Modules").pack(pady=(10, 5))

        # Create scrollable frame for modules
        container = tk.Frame(main, bg=self.bg_color, height=150)
        # container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        container.pack(fill="both", expand=True, pady=(0, 10))
        container.pack_propagate(False)  # Prevent container from shrinking to fit content

        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make scrollable_frame expand to canvas width
        def _configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.imports_label_list = []

        self.populate_module_list()

        

        # Button frame for Install All and Open Folder buttons
        button_frame = tk.Frame(main, bg=self.bg_color)
        button_frame.pack(pady=10)
        
        all_btn = ttk.Button(button_frame, text="Install All", command=self.install_all)
        all_btn.pack(side="left", padx=5)
        
        folder_btn = ttk.Button(button_frame, text="Open Modules Folder", command=self.open_modules_folder)
        folder_btn.pack(side="left", padx=5)

        self.output_text = tk.Text(main, height=10, bg="#2E2E2E", fg=self.fg_color)
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.shed_focus_force = self.after(100, lambda: self.focus_force())
        self.grab_set()

    

    def populate_module_list(self):
        for mod in self.missing:
            frame = tk.Frame(self.scrollable_frame)
            frame.configure(bg="#2E2E2E")
            frame.pack(fill="x", padx=10, pady=2)

            label = tk.Label(frame, text=mod, bg="#2E2E2E", fg=self.fg_color)
            label.pack(side="left", padx=(5, 0))

            # Use a reasonable fixed width (characters) so the button doesn't
            # force the dialog to overflow horizontally. Let layout manage size.
            btn = ttk.Button(frame, text="Install", width=12,
                                command=lambda m=mod: self.install_package(m))
            btn.pack(side="right", padx=(0, 0))

            self.imports_label_list.append(frame)

        for mod in self.imports:
            if mod not in self.missing:
                frame = tk.Frame(self.scrollable_frame)
                frame.configure(bg="#2E2E2E")
                frame.pack(fill="x", padx=10, pady=2)

                label = tk.Label(frame, text=mod, bg="#2E2E2E", fg=self.fg_color)
                label.pack(side="left", padx=(5, 0))

                # Use a reasonable fixed width (characters) so the button doesn't
                # force the dialog to overflow horizontally. Let layout manage size.
                # btn = ttk.Button(frame, text="Install", width=12,
                #                     command=lambda m=mod: self.install_package(m))
                installed_label = tk.Label(frame, text="Installed", bg="#2E2E2E", fg=self.fg_color)
                installed_label.pack(side="right", padx=(0, 0))
                # btn.pack(side="right", padx=(0, 0))

                self.imports_label_list.append(frame)

    def clear_module_list(self):
        for widget in self.imports_label_list:
            widget.destroy()
        self.imports_label_list.clear()

    def refresh_module_list(self):
        self.clear_module_list()
        self.missing = check_missing_imports(self.imports)
        self.populate_module_list()
        

    def install_package(self, module):
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "install", module],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.output_text.insert(tk.END, f"\n[{module}] Installation Output:\n{result.stdout}\n{result.stderr}\n")
            self.output_text.see(tk.END)
        except Exception as e:
            self.output_text.insert(tk.END, f"Failed to install {module}: {e}\n")

        self.refresh_module_list()

    def install_all(self):
        for mod in self.missing:
            self.install_package(mod)

    def open_modules_folder(self):
        """Open file explorer to the site-packages folder where modules are installed"""
        import subprocess
        import site
        import platform
        
        # Get the site-packages directory
        site_packages = site.getsitepackages()
        
        if site_packages:
            # Use the first site-packages directory (usually the main one)
            folder_path = site_packages[0]
            
            # Open folder based on platform
            try:
                system = platform.system()
                if system == 'Windows':
                    subprocess.Popen(['explorer', folder_path])
                elif system == 'Darwin':  # macOS
                    subprocess.Popen(['open', folder_path])
                elif system == 'Linux':
                    subprocess.Popen(['xdg-open', folder_path])
                else:
                    self.output_text.insert(tk.END, f"Unsupported platform: {system}\nFolder path: {folder_path}\n")
                    self.output_text.see(tk.END)
                    return
                
                self.output_text.insert(tk.END, f"Opening folder: {folder_path}\n")
                self.output_text.see(tk.END)
            except Exception as e:
                self.output_text.insert(tk.END, f"Failed to open folder: {e}\n")
                self.output_text.see(tk.END)

    def show(self):
        """Show dialog and wait for result"""
        self.wait_window(self)
        return self.result
    
    def on_close(self):
        print("ModuleCheckerGUI: on_close called")
        #self.after_cancel(self.shed_focus_force)
        self.destroy()
        # Clean up the root window if we own it
        if self._owns_root and self.master:
            try:
                self.master.destroy()
            except:
                pass

if __name__ == '__main__':
    # Test the color picker
    py_module_manager = ModuleCheckerAPP(module_name="utils.py")
    result = py_module_manager.show()
    
    if result:
        print(f"Result: {result}")
    else:
        print("Cancelled")