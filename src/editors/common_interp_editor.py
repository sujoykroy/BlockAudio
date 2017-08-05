from gi.repository import Gtk, Gdk
from ..audio_boxes import *
from ..audio_blocks import *
from ..commons import Point, Beat, Interpolator
from ..commons import KeyboardState
from interp_editor import InterpEditor

from gi.repository import GObject
GObject.threads_init()

class CommonInterpEditor(Gtk.Window):
    def __init__(self, width=800, height=600):
        Gtk.Window.__init__(self, title="Common InterPolator Editor", resizable=True)
        self.set_size_request(width, height)
        self.keyboard_state = KeyboardState()

        self.connect("delete-event", self.quit)
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        self.root_box = Gtk.VBox()
        self.add(self.root_box)

        self.interp_editor = InterpEditor(400, 300, self.keyboard_state)
        self.root_box.pack_start(self.interp_editor, expand=True, fill=True, padding=0)

        self.interpolator = Interpolator([
            Point(0, 0),
            Point(1, 1),
            Point(.25, .25),
            Point(.5, .5),
        ], kind="cubic")
        self.interp_editor.set_interpolator(self.interpolator)

        self.show_all()

    def on_key_press(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=True)
        return True

    def on_key_release(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=False)

    def quit(self, wiget, event):
        Gtk.main_quit()

