import utils


class c_UIAppearance:
    def __init__(self):
        # ALWAYS USE "style.theme_use('clam')" FOR THE MOST SUPPORT!
        self.globalMainFontFamily = "Arial"

        self.mainBG = "#242424"  # "#1a1a1a"
        self.mainTextBoxBG = [self.mainBG, 10]
        self.mainBorderColor = "#424242"
        self.mainBorderWidth = 1


        self.mainTreeviewBG = self.mainTextBoxBG
        self.mainTreeviewFieldBG = self.mainTreeviewBG
        self.mainTreeviewSelectedBG = '#4a6984'
        self.mainTreeviewActiveBG = [self.mainTreeviewBG, self.mainTreeviewSelectedBG, 0.2] # When mouse hovers over
        self.mainTreeviewRowHeight = 24
        self.mainTreeviewTextColor = "white"
        self.mainTreeviewDisabledTextColor = "#888888"
        self.mainTreeviewFontFamily = self.globalMainFontFamily #"Segoe UI"
        self.mainTreeviewFontSize = 10
        self.mainTreeviewFontWeight = "normal"
        self.mainTreeviewFont = (self.mainTreeviewFontFamily, self.mainTreeviewFontSize, self.mainTreeviewFontWeight)

        self.mainTreeviewHeadingBG = [self.mainTreeviewBG, -10]
        self.mainTreeviewHeadingActiveBG = [self.mainTreeviewHeadingBG, +15] # When mouse hovers over
        self.mainTreeviewHeadingTextColor = self.mainTreeviewTextColor
        self.mainTreeviewHeadingFontFamily = self.globalMainFontFamily
        self.mainTreeviewHeadingFontSize = self.mainTreeviewFontSize
        self.mainTreeviewHeadingFontWeight = "bold"
        self.mainTreeviewHeadingFont = (self.mainTreeviewHeadingFontFamily, self.mainTreeviewHeadingFontSize, self.mainTreeviewHeadingFontWeight)
        


        self.mainTextColor = "#ECECEC"
        self.submainTextColor = [self.mainTextColor, -30]
        self.hiddenTextColor = [self.mainTextColor, -50]
        self.mainFontFamily = self.globalMainFontFamily   #"Sans Serif Collection"
        self.mainSymbolsFontFamily = self.globalMainFontFamily #"Noto Sans Symbols"
        self.mainSymbolsFontFamilySizeMult = 1
        self.mainFontSize = 18
        self.mainTitleFontSize = 20
        self.mainSubtextFontSize = 16
        self.mainFontWeight = "normal"


        self.mainButtonColor = "#343434"
        self.mainButtonColorDarker = [self.mainButtonColor, -5]
        self.mainOptionMenuButtonColor = [self.mainButtonColor, +5]
        self.mainButtonColorHover = [self.mainButtonColor, -10]
        self.mainButtonBorderColor = [self.mainButtonColor, -30]
        self.mainButtonBorderWidth = 1
        self.mainButtonTextColor = "#D2D2D2"

        self.test1 = "#929292"
        self.test2 = [self.test1, -89]
        self.test3 = [self.test2, "#7A086B", 0.5]
        self.test3 = [self.test3, "#9900FF", 0.5]


        # self.mainFontFunc = customtkinter.CTkFont(family=self.mainFontFamily, size=self.mainFontSize, weight=self.mainFontWeight)


uia = c_UIAppearance()
  

def resolve_actual_color(attribute, _debug_print=False, loopcount=0):
    #print(f"::: Attribute: {getattr(uia, attribute)}, type: {type(getattr(uia, attribute))}")

    """Resolve to the base color and accumulate all adjustments."""

    if loopcount > 10:
        raise ValueError(f"resolve_actual_color loopcount exceeded limit of 10!")
    
    adjustments = 0
    try:
        current = getattr(uia, attribute)
    except:
        current = attribute

    if _debug_print: print(f"org current: {current}")

    while isinstance(current, list): # and isinstance(current[1], (int, float)):
        if isinstance(current[1], (int, float)):
            adjustments += current[1]
            current = current[0]
        elif ((isinstance(current[0], list) or utils.is_valid_color(current[0]))
        and (isinstance(current[1], list) or utils.is_valid_color(current[1]))
        or isinstance(current[2], (int, float))):
            
            adjustments = 0
            if _debug_print: print(f"{utils.Fore.BLUE}BLENDED COLOR: {current}{utils.Fore.RESET}")

            current0name, current1name = "", ""
            if _debug_print: print(f"{utils.Fore.GREEN}Looking for;\ncurrent[0] = {current[0]}\ncurrent1 = {current[1]}{utils.Fore.RESET}")
            for attr in dir(uia):
                if not attr.startswith("__"):
                    if _debug_print: print(f"checking {attr}: {getattr(uia, attr)}")
                    if getattr(uia, attr) == current[0]:
                        current0name = attr
                        if _debug_print: print(f"{utils.Fore.GREEN}Found current0name: {current0name}{utils.Fore.RESET}")
                    
                    if getattr(uia, attr) == current[1]:
                        current1name = attr
                        if _debug_print: print(f"{utils.Fore.GREEN}Found current1name: {current1name}{utils.Fore.RESET}")

                    if current1name != "" and current0name != "":
                        break

            if current0name == "":
                current0name = current[0]
            if current1name == "":
                current1name = current[1]


            
            current = utils.blend_colors(resolve_actual_color(current0name, _debug_print=_debug_print, loopcount=loopcount+1), resolve_actual_color(current1name, _debug_print=_debug_print, loopcount=loopcount+1), current[2])
        else:
            if _debug_print: print(f"{utils.Fore.RED}Broke out of is instance loop! CURRENT: {current}{utils.Fore.RESET}")
            break
            

        

    if _debug_print: print(f"new current: {current}  new adjust: {adjustments}")
    #print(f"::: NEW Attribute: {current}, Adjustments: {(current)}")

    if not utils.get_color_type(current):
        #raise ValueError(f"Base color '{current}' is not a valid color")
        return False
    
    

    final_rgb = utils.adjust_color_for_contrast(fg=current, adjust=adjustments)
    return utils.rgb_to_hex(final_rgb)
    



for attr in dir(uia):
    if not attr.startswith("__"):
        if (isinstance(getattr(uia, attr), list) 
            and (isinstance(getattr(uia, attr)[1], (int, float)) or isinstance(getattr(uia, attr)[2], (int, float)))):
            # AKA: Match: ([_, int] or [_, _, int])

            #print(f"\n\nattribute {utils.Fore.YELLOW}{attr}{utils.Fore.RESET} is color")
            #print(f"Dive to actual color: {dive_to_actual_color(attr)}")
            newattr = resolve_actual_color(attr)
            print(f"::: {utils.Fore.YELLOW}{attr}{utils.Fore.RESET} {f"| {utils.Fore.CYAN}{utils.Style.BRIGHT}BLENDED{utils.Fore.RESET}{utils.Style.RESET_ALL} |" if len(getattr(uia, attr)) == 3 else ""} New Color: {newattr}  NEW RGB: {utils.hex_to_rgb(newattr)}  {utils.Fore_RGB(utils.hex_to_rgb(newattr))}██{utils.Fore.RESET}")
            setattr(uia, attr, newattr)
#resolve_actual_color("mainTreeviewActiveBG", _debug_print=True)