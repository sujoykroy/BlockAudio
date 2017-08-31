from gi.repository import Gtk, GObject
from ..gui_utils.file_op import FileSelect
from ..commons import draw_utils, Color
import moviepy.editor
import numpy
import cairo
from ..audio_blocks import AudioServer
from ..audio_boxes import AudioBlockBox
import time
from samples_block_viewer import SamplesBlockViewer
from piano_keypad import PianoKeypad

class FileInstruPage(object):
    CurveColor = Color.parse("FFF422")

    def __init__(self, owner, instru):
        self.owner = owner
        self.instru = instru
        self.audio_server = None
        self.audio_block = self.instru.create_note_block()
        self.audio_block.set_no_loop()

        self.image_surface = None
        self.tab_name_label = Gtk.Label()

        self.name_label = Gtk.Label("Name")
        self.name_entry = Gtk.Entry()
        self.name_save_button = Gtk.Button("Rename")
        self.name_save_button.connect("clicked", self.name_save_button_clicked)

        self.source_label = Gtk.Label("Source")
        self.filename_select = FileSelect("audio")
        self.filename_select.connect("file-selected", self.audio_file_selected)

        self.duration_heading_label = Gtk.Label("Duration")
        self.duration_value_entry = Gtk.Entry()
        self.duration_value_entry.set_editable(False)

        self.keypad_button = Gtk.Button("Keypad")
        self.keypad_button.connect("clicked", self.keypad_button_clicked)

        self.amplitude_spin_button = Gtk.SpinButton()
        self.amplitude_spin_button.set_digits(2)
        self.amplitude_spin_button.set_range(0, 5)
        self.amplitude_spin_button.set_increments(.1,.1)
        self.amplitude_spin_button.set_value(self.instru.amplitude)
        self.amplitude_spin_button.connect(
            "value-changed", self.amplitude_spin_button_value_changed)

        #play/pause
        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

        self.block_viewer = SamplesBlockViewer(owner=self.owner)
        self.block_viewer.set_block(self.audio_block)

        self.info_grid = Gtk.Grid()
        self.info_grid.set_column_spacing(5)
        self.info_grid.attach(self.name_label, left=0, top=0, width=1, height=1)
        self.info_grid.attach(self.name_entry, left=1, top=0, width=1, height=1)
        self.info_grid.attach(self.name_save_button, left=2, top=0, width=1, height=1)
        self.info_grid.attach(self.source_label, left=0, top=1, width=1, height=1)
        self.info_grid.attach(self.filename_select, left=1, top=1, width=3, height=1)
        self.info_grid.attach(self.duration_heading_label, left=4, top=1, width=1, height=1)
        self.info_grid.attach(self.duration_value_entry, left=5, top=1, width=1, height=1)
        self.info_grid.attach(self.keypad_button, left=3, top=0, width=1, height=1)
        self.info_grid.attach(Gtk.Label("Ampl."), left=4, top=0, width=1, height=1)
        self.info_grid.attach(self.amplitude_spin_button, left=5, top=0, width=1, height=1)

        self.play_button.props.valign = Gtk.Align.START
        self.pause_button.props.valign = Gtk.Align.START
        self.play_pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.play_pause_box.pack_end(self.play_button, expand=False, fill=False, padding=0)
        self.play_pause_box.pack_end(self.pause_button, expand=False, fill=False, padding=0)

        self.control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.control_box.pack_start(self.info_grid, expand=True, fill=True, padding=0)
        self.control_box.pack_end(self.play_pause_box, expand=True, fill=True, padding=0)

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.root_box.pack_start(self.control_box, expand=False, fill=False, padding=0)
        self.root_box.pack_start(self.block_viewer, expand=True, fill=True, padding=5)

    def update_tab_name_label(self):
        self.tab_name_label.set_markup("{0}<sup> fii</sup>".format(self.instru.get_name()))

    def get_widget(self):
        return self.root_box

    def get_tab_name_label(self):
        return self.tab_name_label

    def init_show(self):
        self.name_entry.set_text(self.instru.get_name())
        self.filename_select.set_filename(self.instru.filename)
        self.show_duration()
        self.update_tab_name_label()
        self.root_box.show_all()
        self.pause_button.hide()

    def show_duration(self):
        self.duration_value_entry.set_text(
            "{0} seconds".format(self.instru.get_duration_seconds()))

    def cleanup(self):
        if self.audio_server:
            self.audio_server.remove_block(self.audio_block)

    def keypad_button_clicked(self, widget):
        self.piano_keypad = PianoKeypad(owner=self.owner)
        self.piano_keypad.set_instru(self.instru)

    def amplitude_spin_button_value_changed(self, widget):
        self.instru.set_amplitude(widget.get_value())
        self.block_viewer.redraw(full=True)

    def name_save_button_clicked(self, widget):
        new_name = self.name_entry.get_text().strip()
        if new_name and new_name != self.instru.get_name():
            if self.owner.rename_instru(self.instru, new_name):
                self.update_tab_name_label()
        self.name_entry.set_text(self.instru.get_name())

    def audio_file_selected(self, widget):
        self.instru.set_filename(self.filename_select.filename)
        if self.audio_server:
            self.audio_server.remove_block(self.audio_block)
            self.play_button.show()
            self.pause_button.hide()
        self.audio_block.destroy()
        self.audio_block = self.instru.get_file_block()
        self.audio_block.set_no_loop()
        self.block_viewer.set_block(self.audio_block)
        self.show_duration()

    def play_button_clicked(self, wiget):
        if not self.audio_server:
            self.audio_server = AudioServer.get_default()
            self.audio_server.add_block(self.audio_block)
        self.audio_block.rewind()
        self.audio_server.play(self.audio_block)
        self.play_button.hide()
        self.pause_button.show()
        self.timer_id = GObject.timeout_add(10, self.on_playahead_movement)

    def on_playahead_movement(self):
        if self.audio_block.is_playing_finished():
            self.audio_block.pause()
            self.play_button.show()
            self.pause_button.hide()
        self.block_viewer.redraw()
        return not self.audio_block.paused

    def pause_button_clicked(self, wiget):
        if not self.audio_server:
            return
        self.audio_block.pause()
        self.play_button.show()
        self.pause_button.hide()
