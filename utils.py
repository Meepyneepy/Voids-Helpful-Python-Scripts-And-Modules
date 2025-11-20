###############################################
#   A script that contains useful functions   #
###############################################
import re
import math
import time
import os
import sys
import stat
import inspect
import importlib
import traceback
import types
from colorama import Fore, Back, Style

debugWatermark = " #!#!#!# "

def try_import(module_name: str, mute_success = True, mute_errors = False):
    """
    Attempts to import a module and returns a status string.
    Best if used to check if modules can be imported before actually defining it literally for IDE to interpret.
    Distinguishes between:
      - successful import
      - module not found
      - dependency missing inside module
      - other import-time errors

    Usage:
        if try_import("utils"):
            import utils
    """
    try:
        importlib.import_module(module_name)
        if not mute_success: print(f"{Fore.GREEN}Successfully imported '{module_name}'{Style.RESET_ALL}")
        return True

    except ModuleNotFoundError as e:
        if not mute_errors:
            print(Fore.RED)
            if e.name == module_name:
                print(f"Module '{module_name}' not found (not installed).")
            else:
                print(f"Module '{module_name}' failed to import because its dependency '{e.name}' is missing.")
            print(Style.RESET_ALL)
        return None

    except Exception as e:
        if not mute_errors:
            print(f"{Fore.RED}Module '{module_name}' failed to import due to an unexpected error:")
            traceback.print_exception(type(e), e, e.__traceback__)
            print(Style.RESET_ALL)
        return None
    
def is_module_imported(name):
    """
    Use to check if module is currently imported.
    """
    if isinstance(name, types.ModuleType):
        name = name.__name__

    if str(name) in sys.modules:
        return True
    else:
        return None
    

if try_import("utils_extra_color_conversions"):
    from utils_extra_color_conversions import rgb_to_cmyk, cmyk_to_rgb, shift_image_hue_rgba, local_cmyk_to_rgb
    #from utils_extra_color_conversions import selected_cmyk_profile, selected_rgb_profile, default_rgb_profile, default_cmyk_profile, cached_icc
else:
    print(f"{Fore.RED}Advanced color conversion functions will not work until error is correct!{Style.RESET_ALL}")


# perf_test_iterations = 25

# from PIL import Image, ImageCms
# def test_cmyk_to_rgb(
#     cmyk_string: str | int | float,
#     m: int | float | None = None,
#     y: int | float | None = None,
#     k: int | float | None = None,
#     *,
#     cmyk_profile: str = selected_cmyk_profile,
#     rgb_profile: str = selected_rgb_profile,
#     intent: int = ImageCms.Intent.RELATIVE_COLORIMETRIC,
#     black_point_compensation: bool = True,
#     out_format: str = "tuple"  # "tuple" or "str"
# ) -> str:
#     test_func = measure_performance(cmyk_to_rgb, cmyk_string, m, y, k, iterations=perf_test_iterations)
#     print(f"Parsing CMYK Average time: {test_func['avg_time']:.6f}s")
#     print(f"Parsing CMYK Total time: {test_func['total_time']:.6f}s")
#     print()

def sleep(duration=1.0):
    time.sleep(duration)
    return

# def multithread_func(self, lambdaFunc, daemon=True, wait=False, lambdaCallback=None):
#     """
#     Run a lambda or function in a background thread.
    
#     Args:
#         lambdaFunc: function or lambda to execute (must be callable, e.g. lambda: myfunc(args))
#         daemon: if True, thread exits with program
#         wait: if True, wait for thread to finish and return result
#         lambdaCallback: optional function to call with result (executed in the same thread!)

#     Returns:
#         If wait=True, returns result. If wait=False, returns thread.
#     """
#     import threading

#     result = {}
#     done = threading.Event()

#     def thread_func():
#         try:
#             result['value'] = lambdaFunc()
#         except Exception as e:
#             result['error'] = e
#         finally:
#             done.set()
#             if lambdaCallback:
#                 if get_required_arg_count(lambdaCallback) >= 1:
#                     lambdaCallback(result.get('value', None))
#                 else:
#                     lambdaCallback()

#     t = threading.Thread(target=thread_func, daemon=daemon)
#     t.start()

#     if wait:
#         t.join()
#         if 'error' in result:
#             raise result['error']
#         return result.get('value', None)
#     else:
#         return t




def multithread_func(self, lambdaFunc, daemon=True, wait=False, lambdaCallback=None, 
                     run_once=False, cancel_key=None):
    """
    Run a lambda or function in a background thread.
    
    Args:
        lambdaFunc: function or lambda to execute (must be callable, e.g. lambda: myfunc(args))
        daemon: if True, thread exits with program
        wait: if True, wait for thread to finish and return result
        lambdaCallback: optional function to call with result (executed in the same thread!)
        run_once: if True, don't start a new thread if one with the same cancel_key is running
        cancel_key: unique identifier for this thread (used with run_once and for cancellation)
    Returns:
        If wait=True, returns result. If wait=False, returns thread.
        If run_once=True and thread already running, returns None.
    """
    import threading
    
    # Initialize tracking dictionaries if they don't exist
    if not hasattr(self, '_running_threads'):
        self._running_threads = {}
        self._cancel_flags = {}
    
    # Check if we should skip starting a new thread
    if run_once and cancel_key:
        if cancel_key in self._running_threads and self._running_threads[cancel_key].is_alive():
            return None  # Thread already running
            print("Thread already running!")
    
    # Set up cancel flag for this thread
    if cancel_key:
        self._cancel_flags[cancel_key] = threading.Event()
    
    result = {}
    done = threading.Event()
    
    def thread_func():
        try:
            result['value'] = lambdaFunc()
        except Exception as e:
            result['error'] = e
        finally:
            done.set()
            # Clean up tracking
            if cancel_key:
                self._cancel_flags.pop(cancel_key, None)
                self._running_threads.pop(cancel_key, None)
            
            if lambdaCallback:
                if get_required_arg_count(lambdaCallback) >= 1:
                    lambdaCallback(result.get('value', None))
                else:
                    lambdaCallback()
    
    t = threading.Thread(target=thread_func, daemon=daemon)
    
    # Track this thread
    if cancel_key:
        self._running_threads[cancel_key] = t
    
    t.start()
    
    if wait:
        t.join()
        if 'error' in result:
            raise result['error']
        return result.get('value', None)
    else:
        return t

def cancel_thread(self, cancel_key):
    """
    Signal a thread to cancel. The thread function must check is_cancelled() periodically.
    
    Args:
        cancel_key: the key used when starting the thread
    Returns:
        True if cancel signal was sent, False if thread not found
    """
    if hasattr(self, '_cancel_flags') and cancel_key in self._cancel_flags:
        self._cancel_flags[cancel_key].set()
        return True
    return False

def is_cancelled(self, cancel_key):
    """
    Check if this thread has been cancelled. Call this periodically in your lambdaFunc.
    
    Args:
        cancel_key: the key used when starting the thread
    Returns:
        True if cancellation was requested
    """
    if hasattr(self, '_cancel_flags') and cancel_key in self._cancel_flags:
        return self._cancel_flags[cancel_key].is_set()
    return False





def Fore_RGB(rgb, g=None, b=None):
    """Console text foreground RGB. (May not be supported on all platforms.)"""
    if isinstance(rgb, (list,tuple)) and not isinstance(rgb, int) and len(rgb) == 3:
        r,g,b = rgb
    return f"\033[38;2;{r};{g};{b}m"

def Back_RGB(rgb, g=None, b=None):
    """Console text background RGB. (May not be supported on all platforms.)"""
    if isinstance(rgb, (list,tuple)) and not isinstance(rgb, int) and len(rgb) == 3:
        r,g,b = rgb
    return f"\033[48;2;{r};{g};{b}m"





def set_file_permissions(path: str, mode="777"):
    """
    Sets file permissions in a cross-platform way.

    Parameters:
    - path (str): Path to the file
    - mode (str or int) (opt): Permission bits (e.g., '644', 0o755) (DEFAULT: '777')

    On Windows: Only writable flag is managed.
    On POSIX: Full chmod behavior is supported.
    """
    # Convert string modes like '644' to octal int
    if isinstance(mode, str):
        if not mode.isdigit() or len(mode) not in (3, 4):
            raise ValueError(f"Invalid permission mode string: '{mode}'")
        mode = int(mode, 8)
    elif isinstance(mode, int):
        if mode < 0 or mode > 0o7777:
            raise ValueError(f"Invalid permission mode integer: {mode}")
    else:
        raise TypeError("Mode must be a string like '755' or an integer like 0o755")

    if sys.platform.startswith("win"):
        # Only set/unset the read-only attribute
        writable = bool(mode & 0o200)  # Owner write bit
        current_mode = os.stat(path).st_mode
        new_mode = current_mode | stat.S_IWRITE if writable else current_mode & ~stat.S_IWRITE
        os.chmod(path, new_mode)
        print(f"[Windows] Set writable={writable} for: {path}")
    else:
        # Full permission setting on POSIX
        os.chmod(path, mode)
        print(f"[POSIX] Set mode {oct(mode)} for: {path}")



def get_required_arg_count(func):
    sig = inspect.signature(func)
    return sum(
        1 for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty and
        p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    )



def convert_string_to_number(s):
    s = str(s)
    s = s.strip()  # Remove whitespace
    if not s:
        raise ValueError("Cannot convert empty string to a number.")
    
    try:
        if '.' in s:
            return float(s)
        else:
            return int(s)
    except ValueError as e:
        raise ValueError(f"Invalid number string: {s}") from e


def normalize_number_format(s):
    """
    Converts a string like '+007.2883' into a normal float or int.
    Removes '+' signs and leading zeros.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    s = s.strip()  # Remove surrounding whitespace
    if not s:
        print(f"{Fore.RED}Empty string cannot be converted{Fore.RESET}")
        return 0.0
        #raise ValueError("Empty string cannot be converted")

    try:
        # Try converting to integer first (if it's a whole number)
        if '.' not in s:
            return int(s.lstrip('+0') or '0')  # avoid empty string on '0000'
        else:
            return float(s.lstrip('+'))  # leading zeros are ignored by float()
    except ValueError as e:
        raise ValueError(f"Invalid number format: {s}") from e


def print_caller_info(stacknum=1):
    # Get the current stack frame and move one level back to the caller
    stack = inspect.stack()
    if len(stack) >= 2:
        caller_frame = stack[stacknum]
        filename = os.path.basename(caller_frame.filename)
        lineno = caller_frame.lineno
        print(
            visual_ljust(
                f"{Fore.CYAN}Called from: {filename}, line {lineno}   ", 135, "#"
            )
            + Fore.RESET
        )
    else:
        print("Unable to determine caller info.")


def debug_print_args(**kwargs):
    print("\n=== Debug: Variable Names and Values ===")
    for name, value in kwargs.items():
        print(f"{name} = {value}")
    print("========================================\n")


def pretty_print_nested(obj, indent=0, beforelinestr="", afterlinestr=""):
    """
    Recursively prints nested dicts/lists with indentation for debugging.

    Args:
            obj (dict, list, any): The object to print.
            indent (int): Current indentation level (used for recursion).
    """
    if indent == 0:
        print_caller_info(2)

    spacing = visual_ljust(f"{Fore.LIGHTBLACK_EX}·{Fore.RESET} ", 2) * indent

    if isinstance(obj, dict):
        print(f"{spacing}")
        for key, value in obj.items():
            print(f"{spacing}  {beforelinestr}{repr(key)}: ", end=afterlinestr)
            pretty_print_nested(
                value,
                indent + 1,
                beforelinestr=beforelinestr,
                afterlinestr=afterlinestr,
            )
        print(f"{spacing}")

    elif isinstance(obj, list):
        print(f"{spacing}[")
        for item in obj:
            pretty_print_nested(
                item, indent + 1, beforelinestr=beforelinestr, afterlinestr=afterlinestr
            )
        print(f"{spacing}]")

    else:
        print(f"{spacing}{beforelinestr}{repr(obj)}{afterlinestr}")


def is_valid_color(value, specific="nil", raiseError=False):
    """Checks if a color value is valid in one or more specified formats.

    Parameters:
    - value: The color to check. Can be a string (e.g., "#FF0000", "rgb(255,0,0)") or a tuple/list (e.g., (255, 0, 0)).
    - specific (str | list): Format(s) to check against: "rgb", "rgba", "hex", or "nil" (any). Accepts string with slashes or a list.
    - raiseError (bool): If True, raises a ValueError when validation fails.

    Returns:
    - bool: True if valid in the specified format(s), else False.

    Supported formats:
    - Hex strings: 3, 4, 6, or 8-digit formats (e.g., "#F00", "#FF0000", "#FF000080")
    - RGB strings: "rgb(r, g, b)"
    - RGBA strings: "rgba(r, g, b, a)"
    - Tuples/lists: (r, g, b) or (r, g, b, a)

    Example:
    >>> is_valid_color((255, 255, 255), specific="rgb")
    True
    """

    # print(f"debug is_valid_color: value={value}, specific={specific}, raiseError={raiseError}")

    if specific == None or (type(specific) != str and type(specific) != list):
        specific = "nil"
    elif type(specific) == list:
        tempSpecific = []
        for v in specific:
            if type(v) == str:
                if v.lower() in ("rgb", "rgba", "hex", "nil"):
                    tempSpecific.append(v.lower())

        if len(tempSpecific) == 0:
            tempSpecific = ["nil"]

        specific = tempSpecific

    if type(specific) == str:
        tempSpecific_1 = specific.split("/")
        tempSpecific_2 = []
        for v in tempSpecific_1:
            if v.lower() in ("rgb", "rgba", "hex", "nil"):
                tempSpecific_2.append(v.lower())

        if len(tempSpecific_2) == 0:
            tempSpecific_2.append("nil")

        specific = tempSpecific_2
    else:
        specific = specific.lower()

    if raiseError == None or type(raiseError) != bool:
        raiseError = False

    checkedFormatsStr = ""
    if "nil" in specific:
        checkedFormatsStr = "rgb/rgba/hex"
    else:
        checkedFormatsStr = "/".join(specific).lower()

    if isinstance(value, str):
        # HEX patterns
        hex_pattern = (
            r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
        )
        if re.fullmatch(hex_pattern, value) and "hex" in checkedFormatsStr:
            return True

        # rgb() and rgba() string patterns
        rgb_pattern = r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$"
        rgba_pattern = r"^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0|1|0?\.\d+)\s*\)$"

        if m := re.fullmatch(rgb_pattern, value) and "rgb" in checkedFormatsStr:
            r, g, b = map(int, m.groups())
            return all(0 <= x <= 255 for x in (r, g, b))

        if m := re.fullmatch(rgba_pattern, value) and "rgba" in checkedFormatsStr:
            r, g, b = map(int, m.groups()[:3])
            a = float(m.group(4))
            return all(0 <= x <= 255 for x in (r, g, b)) and 0.0 <= a <= 1.0

    # RGB or RGBA tuple/list
    if isinstance(value, (tuple, list)):
        if len(value) == 3 and "rgb" in checkedFormatsStr:
            return all(isinstance(x, int) and 0 <= x <= 255 for x in value)
        elif len(value) == 4 and "rgba" in checkedFormatsStr:
            r, g, b, a = value
            return all(isinstance(x, int) and 0 <= x <= 255 for x in (r, g, b)) and (
                isinstance(a, (float, int)) and 0.0 <= a <= 1.0
            )

    if raiseError:
        raise ValueError(f"'{value}' is not a valid {checkedFormatsStr} value!")
    return False


def get_color_type(value, raiseError=False):
    # print(f"{debugWatermark}")
    for v in ("rgb", "rgba", "hex"):
        if is_valid_color(value, specific=v):
            # print(f"ran code v={v}, returned val={is_valid_color(value, specific=v)}")
            return v

    # print(f"{debugWatermark}")
    if raiseError:
        raise ValueError(f"'{value}' is not a valid color format!")
    return False


def rgb_to_hex(rgb):
    if len(rgb) == 4:
        is_valid_color(rgb, specific="rgba", raiseError=True)
        r, g, b, a = rgb
        return f"#{r:02X}{g:02X}{b:02X}{(round(a * 255)):02X}".format(*rgb)
    else:
        is_valid_color(rgb, specific="rgb", raiseError=True)
        return "#{:02X}{:02X}{:02X}".format(*rgb)


def hex_to_rgb(hex_str, include_alpha=False):
    """
    Converts hex color code to RGB or RGBA tuple.

    Supports formats:
            #RGB
            #RRGGBB
            #RRGGBBAA
            #RGBA (if include_alpha=True)
    """
    is_valid_color(hex_str, specific="hex", raiseError=True)

    hex_str = hex_str.strip().lstrip("#")
    length = len(hex_str)

    # Expand short forms like #F00 → #FF0000
    if length == 3:
        r, g, b = [int(c * 2, 16) for c in hex_str]
        return (r, g, b)
    elif length == 4:# and include_alpha:
        r, g, b, a = [int(c * 2, 16) for c in hex_str]
        a = round(a / 255, 4)
        return (r, g, b, a)
    elif length == 6:
        r, g, b = [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]
        return (r, g, b)
    elif length == 8:# and include_alpha:
        r, g, b, a = [int(hex_str[i : i + 2], 16) for i in (0, 2, 4, 6)]
        a = round(a / 255, 4)
        return (r, g, b, a)
    else:
        raise ValueError(f"Invalid hex color format: {hex_str}")
    

def hex_to_decimal(hex_str, include_alpha=False):
    """
    Converts hex color code to RGB DECIMAL or RGBA DECIMAL tuple.

    Supports formats:
            #RGB
            #RRGGBB
            #RRGGBBAA
            #RGBA (if include_alpha=True)
    """
    is_valid_color(hex_str, specific="hex", raiseError=True)
    return tuple(round(c / 255, 4) for c in hex_to_rgb(hex_str=hex_str, include_alpha=include_alpha))


def rgb_to_decimal(rgb):
    """
    Converts RGB or RGBA (0–255) to a decimal tuple.
    
    - R, G, B are divided by 255 and rounded to 5 decimals.
    - A (if present) is left as-is (0–255 integer).
    
    Examples:
        (255, 128, 0)      → (1.0, 0.50196, 0.0)
        (255, 128, 0, 128) → (1.0, 0.50196, 0.0, 128)
    """
    if isinstance(rgb, (float, int)):
        return round(rgb / 255, 4)
    
    if len(rgb) == 4:
        # RGB normalized, A untouched
        r, g, b, a = rgb
        return (round(r / 255, 4), round(g / 255, 4), round(b / 255, 4), a)
    else:
        # Normal RGB
        return tuple(round(c / 255, 4) for c in rgb)

def decimal_to_rgb(decimal_rgb):
    if isinstance(decimal_rgb, (float, int)):
        return int(round(decimal_rgb * 255, 0))
    
    if len(decimal_rgb) == 4:
        # RGB normalized, A untouched
        r, g, b, a = decimal_rgb
        return (int(round(r * 255, 0)), int(round(g * 255, 0)), int(round(b * 255, 0)), a)
    else:
        # Normal RGB
        return tuple(int(round(c * 255, 0)) for c in decimal_rgb)


def decimal_to_hex(decimal_rgb):
    return rgb_to_hex(decimal_to_rgb(decimal_rgb=decimal_rgb))

def hsv_to_rgb(h, s, v):
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

def rgb_to_hsv(r, g, b):
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

# def rgb_to_cmyk(r, g, b):
#     """Convert RGB to CMYK"""
#     if r == 0 and g == 0 and b == 0:
#         return 0, 0, 0, 100
    
#     r, g, b = r / 255, g / 255, b / 255
#     k = 1 - max(r, g, b)
#     c = (1 - r - k) / (1 - k) if k != 1 else 0
#     m = (1 - g - k) / (1 - k) if k != 1 else 0
#     y = (1 - b - k) / (1 - k) if k != 1 else 0
    
#     return int(c * 100), int(m * 100), int(y * 100), int(k * 100)

# def cmyk_to_rgb(c, m, y, k):
#     """Convert CMYK to RGB"""
#     c, m, y, k = c / 100, m / 100, y / 100, k / 100
#     r = 255 * (1 - c) * (1 - k)
#     g = 255 * (1 - m) * (1 - k)
#     b = 255 * (1 - y) * (1 - k)
#     return int(r), int(g), int(b)



def blend_colors(fg, bg, alpha):
    """Blend two RGB colors using alpha compositing.

    Parameters:
    - fg (tuple[int, int, int]): The foreground color as an (R, G, B) tuple with values in the range 0–255.
    - bg (tuple[int, int, int]): The background color as an (R, G, B) tuple with values in the range 0–255.
    - alpha (float): The blending factor, where 0.0 means fully background, and 1.0 means fully foreground.

    Returns:
    - tuple[int, int, int]: The resulting blended color as an (R, G, B) tuple.

    Raises:
    - ValueError: If either `fg` or `bg` is not a valid RGB color (e.g., wrong type, out-of-range values), depending on `is_valid_color()` implementation.

    Example:
    >>> blend_colors((255, 0, 0), (0, 0, 255), 0.5)
    RETURNS: (128, 0, 128)

    Notes:
    - This uses linear interpolation: blended = alpha * fg + (1 - alpha) * bg
    - Color values are rounded to the nearest integer.
    """
    is_valid_color(fg, specific="rgb/hex", raiseError=True)
    is_valid_color(bg, specific="rgb/hex", raiseError=True)
    if get_color_type(fg) == "hex":
        fg = hex_to_rgb(fg)
    if get_color_type(bg) == "hex":
        bg = hex_to_rgb(bg)


    return tuple(round(alpha * fg[i] + (1 - alpha) * bg[i]) for i in range(3))


def adjust_color_for_contrast(fg, bg=None, adjust=-30):
    """
    Adjusts a color (fg) for contrast or darkness.

    Parameters:
            fg      = (R, G, B) foreground color, 0–255
            bg      = (R, G, B) background color, 0–255, or None
            adjust  = int:
                                    - If bg is None: adds this to each channel (can be negative)
                                    - If bg is provided: positive means lighten fg, negative means darken fg
                                                                    based on background brightness

    Returns:
            (R, G, B) tuple
    """

    is_valid_color(fg, specific="rgb/hex", raiseError=True)
    # print(fg)
    # print(bg)

    if is_valid_color(fg, specific="hex"):
        fg = hex_to_rgb(fg)

    # print(f"new fg={fg}")
    # print(f"new bg={bg}")

    def clamp(v, minimum=0, maximum=255):
        return max(minimum, min(maximum, v))

    def brightness(color):
        r, g, b = color
        return 0.299 * r + 0.587 * g + 0.114 * b

    if bg is None:
        # Direct lighten/darken

        # for c in fg:
        # 	print(f"c={c}, type(c)={type(c)}")
        # print(f"adjust={adjust}, type(adjust)={type(adjust)}")

        return tuple(clamp(c + adjust) for c in fg)
    else:
        # Auto-adjust for contrast
        bg_brightness = brightness(bg)
        fg_brightness = brightness(fg)
        delta = adjust if fg_brightness < bg_brightness else -adjust
        return tuple(clamp(c + delta) for c in fg)


def get_contrast_color(bg):
    r, g, b = bg
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if brightness > 186 else (255, 255, 255)


def convertNumToLetter(num):
    letterList = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    ]
    if num > 26:
        return letterList[math.floor((num / 26) - 1)] + letterList[(num % 26 - 1)]
    else:
        return letterList[(num % 26 - 1)]


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def visual_rjust(s, width, fillchar=" "):
    """Right-justify a string by visible width, preserving ANSI color codes."""
    visible_text = ANSI_ESCAPE.sub("", s)
    pad_len = max(0, width - len(visible_text))
    return (fillchar * pad_len) + s


def visual_center(s, width, fillchar=" "):
    """Center-justify a string by visible width, preserving ANSI color codes."""
    visible_text = ANSI_ESCAPE.sub("", s)
    pad_len = max(0, width - len(visible_text))
    left = pad_len // 2
    right = pad_len - left
    return (fillchar * left) + s + (fillchar * right)


def visual_ljust(s, width, fillchar=" "):
    """Left-justify a string by visible width, preserving ANSI color codes."""
    visible_text = ANSI_ESCAPE.sub("", s)
    pad_len = max(0, width - len(visible_text))
    return s + (fillchar * pad_len)


def measure_performance(func, *args, iterations=1, **kwargs):
    """
    Measures the execution time of a function.
    
    Args:
        func: The function to measure
        *args: Positional arguments to pass to the function
        iterations: Number of times to run the function (default: 1)
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        A dictionary containing:
            - 'result': The return value of the function
            - 'total_time': Total execution time in seconds
            - 'avg_time': Average execution time per iteration in seconds
            - 'min_time': Minimum execution time in seconds
            - 'max_time': Maximum execution time in seconds
            - 'iterations': Number of iterations performed
    
    Usage:
        def slow_function(x):
            time.sleep(x)
            return x * 2
        
        results = measure_performance(slow_function, 0.5, iterations=3)
        print(f"Average time: {results['avg_time']:.4f}s")
    """
    times = []
    result = None
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    
    total_time = sum(times)
    
    return {
        'result': result,
        'total_time': total_time,
        'avg_time': total_time / iterations,
        'min_time': min(times),
        'max_time': max(times),
        'iterations': iterations
    }
