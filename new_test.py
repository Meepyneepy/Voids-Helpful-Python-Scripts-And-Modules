import eye_dropper
import module_manager_redesign
import color_picker_redesign
import utils
import sys

# module_manager_redesign.ModuleCheckerGUI(module_name="eye_dropper_TEST.py").show()
# module_manager_redesign.ModuleCheckerGUI(module_name="eye_dropper_TEST.py").show()


new_color = color_picker_redesign.ColorPicker().show()

print(f"Returned ColorPicker Result: {new_color}")
print(f"Returned Color Type: {utils.get_color_type(new_color)}")

picker = eye_dropper.EyeDropper(initial=new_color)
color = picker.show()
if color:
    print(f"Selected Color: {color}")


color = eye_dropper.EyeDropper(initial=color).show()
if color:
    print(f"Selected Color: {color}")



# eye_dropper_manager = eye_dropper.EyeDropper(None)
# eye_dropper_manager.show()