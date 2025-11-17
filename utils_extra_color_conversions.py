import re
from pathlib import Path
from typing import Tuple
from PIL import Image, ImageCms


default_rgb_profile = r"sRGB"
default_cmyk_profile = r"Adobe_ICC_Profiles\CMYK\USWebCoatedSWOP.icc"

selected_rgb_profile = default_rgb_profile
selected_cmyk_profile = default_cmyk_profile

# ---------- Parsing & helpers ----------

def _clamp8(x: int) -> int:
    return 0 if x < 0 else 255 if x > 255 else x

def _to_255_from_pct(p: float) -> int:
    # p in 0..100
    return _clamp8(round(p * 255.0 / 100.0))

def _to_pct_from_255(v8: int) -> int:
    return max(0, min(100, round(v8 * 100.0 / 255.0)))

def _parse_cmyk_string(s: str) -> Tuple[int, int, int, int]:
    """
    Accepts: "10,65,85,5", "cmyk(10,65,85,5)", "10% 65% 85% 5%", "10 65 85 5", etc.
    If any value > 100, assumes device 0..255; else 0..100 (%).
    Returns CMYK 0..255 each.
    """
    if isinstance(s, tuple):
        # String is already a tuple
        toks = s
        saw_pct = True
        nums = toks
    else:
        s = s.strip().lower().replace("cmyk", "").replace("(", " ").replace(")", " ")
        toks = [t for t in re.split(r"[^0-9.%]+", s) if t]

        saw_pct = any(t.endswith("%") for t in toks)
        nums = [float(t[:-1]) if t.endswith("%") else float(t) for t in toks]

        

    if len(toks) != 4:
        raise ValueError(f"Could not parse CMYK values from: {s!r}")
    
    if saw_pct:
        vals = [_to_255_from_pct(v) if 0 <= v <= 100 else (_to_255_from_pct(max(0, min(100, v)))) for v in nums]
    else:
        if any(v > 100 for v in nums):
            vals = [_clamp8(int(round(v))) for v in nums]
        else:
            vals = [_to_255_from_pct(v) for v in nums]

    
    return tuple(vals)  # type: ignore[return-value]

def _parse_rgb_string(s: str) -> Tuple[int, int, int]:
    """
    Accepts: "rgb(12,34,56)", "12,34,56", "12 34 56", "#0C2238", "#0c2238",
    Returns RGB 0..255 each.
    """
    if isinstance(s, tuple):
        # String is already a tuple
        return s
    else:
        s = s.strip().lower()
        # hex
        m = re.match(r"#?([0-9a-f]{6})$", s)
        if m:
            h = m.group(1)
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        # rgb()
        s = s.replace("rgb", "").replace("(", " ").replace(")", " ")
        toks = [t for t in re.split(r"[^0-9]+", s) if t]
    if len(toks) != 3:
        raise ValueError(f"Could not parse RGB values from: {s!r}")
    return tuple(_clamp8(int(t)) for t in toks)  # type: ignore[return-value]


# ---------- Core conversion (ICC-managed) ----------

def _open_icc(path_or_keyword: str):
    # Allow built-in sRGB keyword without a file
    if path_or_keyword.strip().lower() == "srgb":
        return ImageCms.createProfile("sRGB")
    p = Path(path_or_keyword).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    if not p.is_file():
        raise FileNotFoundError(
            f"ICC profile not found: {path_or_keyword!r}\nResolved to: {str(p)}"
        )
    return ImageCms.getOpenProfile(str(p))

class FastCMYKtoRGB:
    def __init__(self, mode: str, xform):
        self._xform = xform
        self._src = Image.new(mode, (1, 1))  # reused
        self._mode = mode
    def convert_cmyk_to_rgb(self, c8, m8, y8, k8):
        self._src.putpixel((0, 0), (c8, m8, y8, k8))
        out = ImageCms.applyTransform(self._src, self._xform)
        return out.getpixel((0, 0))
    def convert_rgb_to_cmyk(self, r8, g8, b8):
        self._src.putpixel((0, 0), (r8, g8, b8))
        out = ImageCms.applyTransform(self._src, self._xform)
        return out.getpixel((0, 0))
    

def cmyk_to_rgb(
    cmyk_string: str | int | float,
    m: int | float | None = None,
    y: int | float | None = None,
    k: int | float | None = None,
    *,
    cmyk_profile: str = selected_cmyk_profile,
    rgb_profile: str = selected_rgb_profile,
    intent: int = ImageCms.Intent.RELATIVE_COLORIMETRIC,
    black_point_compensation: bool = True,
    out_format: str = "tuple"  # "tuple" or "str"
) -> str:
    """
    Convert a CMYK data string to an RGB string using ICC profiles.
    - cmyk_icc_path: path to the CMYK ICC profile used in Photoshop (e.g., USWebCoatedSWOP.icc)
    - rgb_profile: "sRGB" (built-in) or a path to the RGB working ICC (e.g., AdobeRGB1998.icc)
    """
    # 1) Parse
    cmyk_string = tuple(x for x in (cmyk_string, m, y, k) if x is not None) if (m is not None and y is not None and k is not None) else cmyk_string
    #print(f"received cmyk_string: {cmyk_string}")
    c8, m8, y8, k8 = _parse_cmyk_string(cmyk_string)

    # 2) Build the ICC transform: CMYK -> RGB
    prof_cmyk = _open_icc(cmyk_profile)
    prof_rgb  = _open_icc(rgb_profile)
    flags = ImageCms.Flags.BLACKPOINTCOMPENSATION if black_point_compensation else 0

    xform = ImageCms.buildTransformFromOpenProfiles(
        prof_cmyk, prof_rgb, "CMYK", "RGB",
        renderingIntent=intent, flags=flags
    )

    # 3) Apply transform to a 1×1 “image” swatch
    helper = FastCMYKtoRGB("RGB", xform)

    r, g, b = helper.convert_cmyk_to_rgb(c8, m8, y8, k8)

    # 4) Format output
    if out_format == "str":
        return f"rgb({r},{g},{b})"
    
    return r, g, b




def rgb_to_cmyk(
    rgb_string: str | int | float, # = to "r" if g and b are given.
    g: int | float | None = None,
    b: int | float | None = None,
    *,
    cmyk_profile: str = selected_cmyk_profile,
    rgb_profile: str = selected_rgb_profile,
    intent: int = ImageCms.Intent.RELATIVE_COLORIMETRIC,
    black_point_compensation: bool = True,
    out_format: str = "tuple"  # "tuple" or "str"
) -> str:
    

    # 1) Parse
    rgb_string = tuple(x for x in (rgb_string, g, b) if x is not None) if (g is not None and b is not None) else rgb_string
    #print(f"received rgb_string: {rgb_string}")

    r8, g8, b8 = _parse_rgb_string(rgb_string)

    # 2) Build the ICC transform: CMYK -> RGB
    prof_cmyk = _open_icc(cmyk_profile)
    prof_rgb  = _open_icc(rgb_profile)
    flags = ImageCms.Flags.BLACKPOINTCOMPENSATION if black_point_compensation else 0

    xform = ImageCms.buildTransformFromOpenProfiles(
        prof_rgb, prof_cmyk, "RGB", "CMYK",
        renderingIntent=intent, flags=flags
    )

    # 3) Apply transform to a 1×1 “image” swatch
    helper = FastCMYKtoRGB("CMYK", xform)

    c, m, y, k = helper.convert_rgb_to_cmyk(r8, g8, b8)

    # 4) Format output
    if out_format == "str":
        return f"cmyk({c},{m},{y},{k})"
    
    return _to_pct_from_255(c), _to_pct_from_255(m), _to_pct_from_255(y), _to_pct_from_255(k)


# # Windows example: point to an actual CMYK ICC on your system
# rgb = cmyk_to_rgb(90.5,100,0,0)
# print("working")
# print(rgb)  # -> e.g. "rgb(201,97,60)"

# # RGB -> CMYK (string to string)
# cmyk_out = rgb_to_cmyk(rgb)
# print(cmyk_out)  # e.g., "cmyk(10%,65%,85%,5%)"

# print("ending")
