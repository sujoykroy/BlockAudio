from gi.repository import Gtk, GObject
from ..gui_utils.file_op import FileSelect
from ..commons import draw_utils, Color
from .. import gui_utils
import moviepy.editor
import numpy
import cairo
from ..audio_blocks import AudioServer, AudioBlockTime
from ..audio_boxes import AudioBlockBox
import time
from samples_block_viewer import SamplesBlockViewer

class FormulaInstruPage(object):
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
        self.filename_select = FileSelect([["Python", "*.py"]])
        self.filename_select.connect("file-selected", self.formula_file_selected)

        self.duration_label = Gtk.Label("Duration")
        self.duration_spin_button =  Gtk.SpinButton()
        self.duration_spin_button.set_digits(3)
        self.duration_spin_button.set_range(0, 10000000)
        self.duration_spin_button.set_increments(.1, .1)
        self.duration_spin_button.connect(
            "value-changed", self.duration_spin_button_value_changed)

        self.duration_unit_combo_box = gui_utils.NameValueComboBox()
        self.duration_unit_combo_box.build_and_set_model(AudioBlockTime.get_model())
        self.duration_unit_combo_box.set_value("Beat")
        self.duration_unit_combo_box.connect(
            "changed", self.duration_unit_combo_box_changed)

        #play/pause
        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

        self.param_widgets = []
        self.param_grid = Gtk.Grid()
        self.block_viewer = SamplesBlockViewer(owner=self.owner)
        self.block_viewer.set_block(self.audio_block)

        self.info_grid = Gtk.Grid()
        self.info_grid.set_column_spacing(5)
        self.info_grid.attach(self.name_label, left=0, top=0, width=1, height=1)
        self.info_grid.attach(self.name_entry, left=1, top=0, width=1, height=1)
        self.info_grid.attach(self.name_save_button, left=2, top=0, width=1, height=1)
        self.info_grid.attach(self.source_label, left=0, top=2, width=1, height=1)
        self.info_grid.attach(self.filename_select, left=1, top=2, width=3, height=1)
        self.info_grid.attach(self.duration_label, left=0, top=1, width=1, height=1)
        self.info_grid.attach(self.duration_spin_button, left=1, top=1, width=1, height=1)
        self.info_grid.attach(self.duration_unit_combo_box, left=2, top=1, width=1, height=1)

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
        self.root_box.pack_start(self.param_grid, expand=False, fill=False, padding=0)
        self.root_box.pack_start(self.block_viewer, expand=True, fill=True, padding=5)

        self.build_param_widgets()

    def update_tab_name_label(self):
        self.tab_name_label.set_markup("{0}<sup> foi</sup>".format(self.instru.get_name()))

    def get_widget(self):
        return self.root_box

    def get_tab_name_label(self):
        return self.tab_name_label

    def init_show(self):
        self.name_entry.set_text(self.instru.get_name())
        self.duration_unit_combo_box.set_value(self.instru.duration_time.unit)
        self.duration_spin_button.set_value(self.instru.duration_time.value)
        self.update_tab_name_label()
        self.root_box.show_all()
        self.pause_button.hide()
        if self.instru.is_customized():
            self.filename_select.show()
            self.filename_select.set_filename(self.instru.formulator_path)
        else:
            self.filename_select.hide()

    def cleanup(self):
        if self.audio_server:
            self.audio_server.remove_block(self.audio_block)

    def build_param_widgets(self):
        for param_label, param_widget in self.param_widgets:
            self.param_grid.remove(param_label)
            self.param_grid.remove(param_widget)

        for param_data in self.instru.get_param_list():
            param_name = param_data[0]
            param_type = param_data[1]
            if param_type == float:
                min_value = param_data[2].get("min", -10000.)
                max_value = param_data[2].get("max", 10000)
                step_value = param_data[2].get("step", 1)

                spin_button =  Gtk.SpinButton()
                spin_button.set_digits(3)
                spin_button.set_range(min_value, max_value)
                spin_button.set_increments(step_value, step_value)
                spin_button.connect(
                    "value-changed",
                    self.param_spin_button_value_changed,
                    param_name)
                spin_button.set_value(self.instru.get_param(param_name))
                widget = spin_button
            else:
                widget = None
            if widget:
                widget.param_data = param_data
                label_name = param_name[0].upper() + param_name[1:]
                self.param_widgets.append([Gtk.Label(label_name), widget])

        cell_per_column = 2
        for i in xrange(len(self.param_widgets)):
            row = i//cell_per_column
            column = i%cell_per_column
            self.param_grid.attach(
                self.param_widgets[i][0], top=row, left=column*2, width=1, height=1)
            self.param_grid.attach(
                self.param_widgets[i][1], top=row, left=column*2+1, width=1, height=1)
        self.param_grid.show()

    def recreate_block_viewer(self):
        if self.audio_block:
            self.audio_block.destroy()
        self.audio_block = self.instru.create_note_block()
        self.audio_block.set_no_loop()
        self.block_viewer.set_block(self.audio_block)
        if self.audio_server:
            self.audio_server.add_block(self.audio_block)

    def name_save_button_clicked(self, widget):
        new_name = self.name_entry.get_text().strip()
        if new_name and new_name != self.instru.get_name():
            if self.owner.rename_instru(self.instru, new_name):
                self.update_tab_name_label()
        self.name_entry.set_text(self.instru.get_name())

    def param_spin_button_value_changed(self, widget, param_name):
        self.instru.set_param(param_name, widget.get_value())
        self.recreate_block_viewer()

    def formula_file_selected(self, widget):
        self.instru.load_formulator(self.filename_select.filename)
        if self.audio_server:
            self.audio_server.remove_block(self.audio_block)
            self.play_button.show()
            self.pause_button.hide()
        self.build_param_widgets()
        self.recreate_block_viewer()

    def duration_spin_button_value_changed(self, widget):
        self.instru.set_duration_value(widget.get_value(), self.owner.beat)
        self.recreate_block_viewer()

    def duration_unit_combo_box_changed(self, widget):
        unit_value = widget.get_value()
        self.instru.set_duration_unit(unit_value, self.owner.beat)
        self.duration_spin_button.set_value(self.instru.duration_time.value)
        self.recreate_block_viewer()

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
