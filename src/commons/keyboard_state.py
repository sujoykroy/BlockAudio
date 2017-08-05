class KeyboardState(object):
    SHIFT_KEY_CODES = (65505, 65506)
    CTRL_KEY_CODES = (65507, 65508)

    def __init__(self):
        self.shift_key_pressed = False
        self.control_key_pressed = False

    def set_keypress(self, keyval, pressed):
        if keyval in self.SHIFT_KEY_CODES:
            self.shift_key_pressed = pressed
        elif keyval in self.CTRL_KEY_CODES:
            self.control_key_pressed = pressed

    def is_control_shift_pressed(self):
        return self.shift_key_pressed or self.control_key_pressed

