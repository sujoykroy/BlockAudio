from gi.repository import Gtk, Gdk
from ..audio_boxes import *
from ..audio_blocks import *
from ..commons import Point, Beat

from gi.repository import GObject
GObject.threads_init()

class AudioSequencer(Gtk.Window):
    def __init__(self, width=800, height=600):
        Gtk.Window.__init__(self, title="Sequencer", resizable=True)
        self.set_size_request(width, height)
        self.connect("delete-event", self.quit)

        self.root_box = Gtk.VBox()
        self.add(self.root_box)


        self.play_control_box = Gtk.HBox()
        self.root_box.pack_start(self.play_control_box, expand=False, fill=False, padding=5)

        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

        self.play_control_box.pack_start(self.play_button, expand=False, fill=False, padding=5)
        self.play_control_box.pack_start(self.pause_button, expand=False, fill=False, padding=5)

        self.board_container = Gtk.Grid()
        self.root_box.pack_start(self.board_container, expand=True, fill=True, padding=5)

        self.board = Gtk.DrawingArea()
        self.board.set_size_request(400, 300)
        self.board_container.attach(self.board, left=0, top=0, width=1, height=1)
        self.board.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)

        self.board.connect("draw", self.on_board_draw)
        self.board.connect("configure-event", self.on_board_configure_event)
        self.board.connect("button-press-event", self.on_board_mouse_press)
        self.board.connect("button-release-event", self.on_board_mouse_release)
        self.board.connect("motion-notify-event", self.on_board_mouse_move)
        self.board.connect("scroll-event", self.on_board_mouse_scroll)

        self.board_vadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.board_vscrollbar = Gtk.VScrollbar(self.board_vadjust)
        self.board_container.attach(self.board_vscrollbar, left=1, top=0, width=1, height=1)

        self.board_hadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.board_hscrollbar = Gtk.HScrollbar(self.board_hadjust)
        self.board_container.attach(self.board_hscrollbar, left=0, top=1, width=2, height=1)

        self.audio_block = None
        self.block_box = None
        self.audio_server = None

        self.mouse_point = Point(0., 0.)
        self.mouse_init_point = Point(0., 0.)
        self.selected_box = None
        self.beat = Beat(bpm=120/8,
                         sample_rate=AudioBlock.SampleRate,
                         pixel_per_sample=AudioBlockBox.PIXEL_PER_SAMPLE)

        self.show_all()
        self.pause_button.hide()

    def play_button_clicked(self, wiget):
        if not self.audio_block:
            return
        if not self.audio_server:
            self.audio_server = AudioServer()
            self.audio_server.add_block(self.audio_block)
        self.audio_server.play()
        self.play_button.hide()
        self.pause_button.show()
        self.timer_id = GObject.timeout_add(100, self.on_playahead_movement)

    def pause_button_clicked(self, wiget):
        if not self.audio_block:
            return
        if not self.audio_server:
            return
        self.audio_server.pause()
        self.play_button.show()
        self.pause_button.hide()

    def on_playahead_movement(self):
        self.redraw()
        return self.audio_server and not self.audio_server.paused

    def load_block(self, audio_block):
        if self.audio_server and self.audio_block:
            self.audio_server.remove_block(self.audio_block)

        self.audio_block = audio_block
        if self.audio_block:
            if isinstance(self.audio_block, AudioTimedGroup):
                block_box = AudioTimedGroupBox(self.audio_block)
            else:
                block_box = AudioBlockBox(self.audio_block)
            self.block_box = block_box
            self.block_box.set_size(
                self.board.get_allocated_width(),
                self.board.get_allocated_height())
            if self.audio_server:
                self.audio_server.add_block(self.audio_block)
        else:
            self.block_box = None
        self.redraw()

    def redraw(self):
        self.board.queue_draw()

    def on_board_draw(self, widget, ctx):
        if not self.block_box:
            return
        self.block_box.show_div_marks(ctx, self.beat)
        self.block_box.draw(ctx)
        self.block_box.show_beat_marks(ctx, self.beat)
        self.block_box.show_current_position(ctx)
        self.block_box.show_border_line(ctx)

    def on_board_configure_event(self, widget, event):
        if self.block_box:
            self.block_box.set_size(
                self.board.get_allocated_width(), self.board.get_allocated_height())

    def on_board_mouse_press(self, widget, event):
        self.mouse_init_point.x = self.mouse_point.x
        self.mouse_init_point.y = self.mouse_point.y
        if self.block_box:
            self.selected_box = self.block_box.find_box_at(self.mouse_point)
            if self.selected_box:
                self.selected_box_init_position = self.selected_box.get_position()

    def on_board_mouse_release(self,widget, event):
        self.selected_box = None

    def on_board_mouse_move(self, widget, event):
        self.mouse_point.x = event.x
        self.mouse_point.y = event.y
        if self.selected_box:
            self.block_box.move_box(
                self.selected_box, self.selected_box_init_position,
                self.mouse_init_point, self.mouse_point,
                beat=self.beat)
            self.redraw()

    def on_board_mouse_scroll(self, widget, event):
        pass

    def quit(self, wiget, event):
        if self.audio_server:
            self.audio_server.close()
        Gtk.main_quit()

