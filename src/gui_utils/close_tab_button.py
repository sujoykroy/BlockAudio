from gi.repository import Gtk, Gdk
from ..commons import Color, draw_utils

class CloseTabButton(Gtk.DrawingArea):
    NormalColor = Color.parse("cccccc")
    HoverColor = Color.parse("ff0000")

    def __init__(self, callback, data, cross_size=10):
        super(CloseTabButton, self).__init__()
        self.mouse_release_callback = callback
        self.callback_data = data

        self.cross_size = cross_size
        self.set_size_request(cross_size, cross_size)
        self.set_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK| \
            Gdk.EventMask.BUTTON_PRESS_MASK| \
            Gdk.EventMask.BUTTON_RELEASE_MASK| \
            Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self.connect("draw", self.on_draw)
        self.connect("enter-notify-event", self.on_mouse_enter)
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("button-release-event", self.on_mouse_release)
        self.line_color = self.NormalColor
        self.override_background_color(Gtk.StateFlags.NORMAL,  Gdk.RGBA(1,0,0,0))
        self.override_background_color(Gtk.StateFlags.ACTIVE,  Gdk.RGBA(1,0,0,0))

    def on_draw(self, widget, ctx):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        ctx.translate((w-self.cross_size)*.5, (h-self.cross_size)*.5)
        ctx.new_path()
        ctx.move_to(0, 0)
        ctx.line_to(self.cross_size, self.cross_size)
        ctx.move_to(self.cross_size, 0)
        ctx.line_to(0, self.cross_size)
        draw_utils.draw_stroke(ctx, 1.5, self.line_color)

    def on_mouse_enter(self, widget, event):
        self.line_color = self.HoverColor
        self.queue_draw()

    def on_mouse_leave(self, widget, event):
        self.line_color = self.NormalColor
        self.queue_draw()

    def on_mouse_release(self, widget, event):
        self.mouse_release_callback(self, self.callback_data)

