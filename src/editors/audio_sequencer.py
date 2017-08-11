from gi.repository import Gtk, Gdk
from ..audio_boxes import *
from ..audio_blocks import *
from ..formulators import *
from ..commons import Point, Beat, KeyboardState, Rect
from ..commons import MusicNote
from .. import gui_utils

from gi.repository import GObject
GObject.threads_init()

class AudioSequencer(Gtk.Window):
    def __init__(self, width=800, height=600, instru_list=None, timed_group_list=None):
        Gtk.Window.__init__(self, title="Sequencer", resizable=True)
        self.set_size_request(width, height)

        self.keyboard_state = KeyboardState()

        self.connect("delete-event", self.quit)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        if not instru_list:
            instru_list = []
        if not timed_group_list:
            timed_group = AudioTimedGroup()
            timed_group.set_name("Main")
            timed_group_list = [timed_group]
        self.instru_list = instru_list
        self.timed_group_list = timed_group_list

        self.instru_list_label = Gtk.Label("Instruments")
        self.instru_list_label.set_pattern("___________")
        self.instru_list_label.set_justify(Gtk.Justification.CENTER)

        self.instru_list_view = Gtk.TreeView()
        self.instru_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.instru_list_view.set_headers_visible(False)

        self.add_file_instru_button = Gtk.Button("Add File Instrument")
        self.add_file_instru_button.connect("clicked", self.add_file_instru_button_clicked)

        self.formula_list_label = Gtk.Label("Formulators")
        self.formula_list_label.set_pattern("___________")
        self.formula_combo_box = gui_utils.NameValueComboBox()
        self.formula_combo_box.build_and_set_model([
            ["Sine", SineFormulator]
        ])
        self.add_formula_instru_button = Gtk.Button("Add Formula Instrument")
        self.add_formula_instru_button.connect("clicked", self.add_formula_instru_button_clicked)

        self.timed_group_list_label = Gtk.Label("Block Groups")
        self.timed_group_list_label.set_pattern("____________")
        self.timed_group_list_label.set_justify(Gtk.Justification.CENTER)

        self.timed_group_list_view = Gtk.TreeView()
        self.timed_group_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.timed_group_list_view.set_headers_visible(False)

        self.add_block_group_button = Gtk.Button("Add Block Group")
        self.add_block_group_button.connect("clicked", self.add_block_group_button_clicked)

        self.play_control_box = Gtk.HBox()

        #play/pause
        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

        self.play_control_box.pack_start(self.play_button, expand=False, fill=False, padding=5)
        self.play_control_box.pack_start(self.pause_button, expand=False, fill=False, padding=5)

        #timed group editor
        self.timed_group_editor = Gtk.DrawingArea()
        self.timed_group_editor.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)

        self.timed_group_editor.connect(
                "draw", self.on_timed_group_editor_draw)
        self.timed_group_editor.connect(
                "configure-event", self.on_timed_group_editor_configure_event)
        self.timed_group_editor.connect(
                "button-press-event", self.on_timed_group_editor_mouse_press)
        self.timed_group_editor.connect(
                "button-release-event", self.on_timed_group_editor_mouse_release)
        self.timed_group_editor.connect(
                "motion-notify-event", self.on_timed_group_editor_mouse_move)
        self.timed_group_editor.connect(
                "scroll-event", self.on_timed_group_editor_mouse_scroll)

        #timed group editor vertical scroller
        self.timed_group_editor_vadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.timed_group_editor_vscrollbar = Gtk.VScrollbar(self.timed_group_editor_vadjust)
        self.timed_group_editor_vscrollbar.connect(
            "value-changed", self.on_timed_group_editor_scrollbar_value_changed, "vert")

        #timed group editor horizontal scroller
        self.timed_group_editor_hadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.timed_group_editor_hscrollbar = Gtk.HScrollbar(self.timed_group_editor_hadjust)
        self.timed_group_editor_hscrollbar.connect(
            "value-changed", self.on_timed_group_editor_scrollbar_value_changed, "horiz")

        self.audio_block_edit_box = Gtk.Grid()
        self.audio_block_note_list = gui_utils.NameValueComboBox()
        self.audio_block_note_list.build_and_set_model(MusicNote.get_names())
        self.audio_block_note_list.connect("changed", self.audio_block_note_list_changed)

        self.audio_block_edit_box.attach(
                Gtk.Label("Note"), left=1, top=1, width=1, height=1)
        self.audio_block_edit_box.attach(
                self.audio_block_note_list, left=2, top=1, width=1, height=1)

        self.audio_block = None
        self.block_box = None
        self.audio_server = None

        self.mouse_point = Point(0., 0.)
        self.mouse_init_point = Point(0., 0.)
        self.selected_box = None
        self.beat = Beat(bpm=120/8,
                         sample_rate=AudioBlock.SampleRate,
                         pixel_per_sample=AudioBlockBox.PIXEL_PER_SAMPLE)
        self.tge_rect = Rect(0, 0, 1, 1)

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.root_box)

        self.blockinstru_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.blockinstru_box.set_size_request(100, -1)

        self.blockinstru_box.pack_start(
                self.instru_list_label, expand=False, fill=False, padding=5)

        self.instru_list_view_container = Gtk.ScrolledWindow()
        self.instru_list_view_container.add_with_viewport(self.instru_list_view)


        self.blockinstru_box.pack_start(
                self.instru_list_view_container, expand=True, fill=True, padding=0)
        self.blockinstru_box.pack_start(
                self.add_file_instru_button, expand=False, fill=False, padding=5)

        self.blockinstru_box.pack_start(
                self.formula_list_label, expand=False, fill=False, padding=5)

        self.blockinstru_box.pack_start(
                self.formula_combo_box, expand=False, fill=False, padding=0)
        self.blockinstru_box.pack_start(
                self.add_formula_instru_button, expand=False, fill=False, padding=5)

        self.blockinstru_box.pack_start(
                self.timed_group_list_label, expand=False, fill=False, padding=5)

        self.timed_group_list_view_container = Gtk.ScrolledWindow()
        self.timed_group_list_view_container.add_with_viewport(self.timed_group_list_view)

        self.blockinstru_box.pack_start(
                self.timed_group_list_view_container, expand=True, fill=True, padding=5)
        self.blockinstru_box.pack_end(
                self.add_block_group_button, expand=False, fill=False, padding=0)

        self.instru_hcontainer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.instru_hcontainer.pack_start(
                self.timed_group_editor, expand=True, fill=True, padding=0)
        self.instru_hcontainer.pack_end(
                self.timed_group_editor_vscrollbar, expand=False, fill=False, padding=0)

        self.instru_vcontainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.instru_vcontainer.pack_start(
                self.instru_hcontainer, expand=True, fill=True, padding=0)
        self.instru_vcontainer.pack_end(
                self.audio_block_edit_box, expand=False, fill=False, padding=0)
        self.instru_vcontainer.pack_end(
                self.timed_group_editor_hscrollbar, expand=False, fill=False, padding=0)

        self.block_instru_notebook = Gtk.Notebook()
        self.block_instru_notebook.append_page(self.instru_vcontainer, Gtk.Label("Block Group"))

        self.root_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_paned.add1(self.blockinstru_box)
        self.root_paned.add2(self.block_instru_notebook)

        self.root_box.pack_start(self.root_paned, expand=True, fill=True, padding=5)
        #self.root_box.pack_start(self.blockinstru_box, expand=False, fill=False, padding=5)
        #self.root_box.pack_start(self.block_instru_notebook, expand=True, fill=True, padding=2)

        self.build_instru_list_view()
        self.build_timed_group_list_view()
        self.show_all()
        self.pause_button.hide()
        self.audio_block_edit_box.hide()

    def add_file_instru_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "open", "audio")
        if filename:
            instru = AudioFileInstru(filename=filename)
            self.instru_list.append(instru)
            self.build_instru_list_view()

    def add_formula_instru_button_clicked(self, widget):
        formulator_class = self.formula_combo_box.get_value()
        if formulator_class:
            instru = AudioFormulaInstru(formulator=formulator_class())
            self.instru_list.append(instru)
            self.build_instru_list_view()

    def add_block_group_button_clicked(self, widget):
        timed_group = AudioTimedGroup()
        self.timed_group_list.append(timed_group)
        self.build_timed_group_list_view()

    def build_instru_list_view(self):
        instru_store = Gtk.TreeStore(str, object)

        instru_dict = dict()
        for instru in self.instru_list:
            instru_dict[instru.get_name()] = instru
        for name in sorted(instru_dict.keys()):
            instru_store.append(None, [name, instru_dict[name]])
        self.instru_list_view.set_model(instru_store)

    def get_selected_instru(self):
        model, tree_iter = self.instru_list_view.get_selection().get_selected()
        if tree_iter:
            return model.get_value(tree_iter, 1)
        return None

    def build_timed_group_list_view(self):
        group_store = Gtk.TreeStore(str, object)

        group_dict = dict()
        for group in self.timed_group_list:
            group_dict[group.get_name()] = group
        for name in sorted(group_dict.keys()):
            group_store.append(None, [name, group_dict[name]])
        self.timed_group_list_view.set_model(group_store)

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
        self.redraw_timed_group_editor()
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
                self.timed_group_editor.get_allocated_width(),
                self.timed_group_editor.get_allocated_height())
            if self.audio_server:
                self.audio_server.add_block(self.audio_block)
        else:
            self.block_box = None
        self.redraw_timed_group_editor()

    def show_audio_block_info(self):
        if self.selected_block_box:
            self.audio_block_note_list.set_value(self.selected_block_box.audio_block.music_note)
            self.audio_block_edit_box.show()
        else:
            self.audio_block_edit_box.hide()

    def audio_block_note_list_changed(self, widget):
        if self.selected_block_box:
            note_name = self.audio_block_note_list.get_value()
            if note_name:
                self.selected_block_box.audio_block.set_note(note_name)
                self.block_box.update_size()
                self.timed_group_editor.queue_draw()

    def redraw_timed_group_editor(self):
        self.timed_group_editor.queue_draw()

    def on_timed_group_editor_draw(self, widget, ctx):
        if not self.block_box:
            return
        self.block_box.show_div_marks(ctx, self.beat)

        rect = self.block_box.get_rect(Point(0,0), Point(self.tge_rect.width, self.tge_rect.height))
        self.block_box.draw(ctx, rect)

        self.block_box.show_beat_marks(ctx, self.beat)
        self.block_box.show_current_position(ctx)
        self.block_box.show_outer_border_line(ctx)

    def on_timed_group_editor_configure_event(self, widget, event):
        tge = self.timed_group_editor
        self.tge_rect = Rect(0, 0, tge.get_allocated_width(), tge.get_allocated_height())
        if self.block_box:
            self.block_box.set_size(self.tge_rect.width, None)
    def on_timed_group_editor_mouse_press(self, widget, event):
        self.mouse_init_point.x = self.mouse_point.x
        self.mouse_init_point.y = self.mouse_point.y
        if event.button == 1:#Left mouse
            if self.keyboard_state.control_key_pressed:
                instru = self.get_selected_instru()
                if instru:
                    pos = self.block_box.transform_point(self.mouse_point)
                    self.block_box.add_block(
                        instru.create_note_block(), at=pos.x, y=pos.y, sample_unit=False)
                    self.redraw_timed_group_editor()
            else:
                if self.block_box:
                    self.selected_box = self.block_box.find_box_at(self.mouse_point)
            if event.type == Gdk.EventType._2BUTTON_PRESS:#double button click
                if isinstance(self.selected_box, AudioBlockBox):
                    self.selected_block_box = self.selected_box
                else:
                    self.selected_block_box = None
                self.show_audio_block_info()
        elif event.button == 3:#Left mouse
            self.selected_box = self.block_box

        if self.selected_box:
            self.selected_box_init_position = self.selected_box.get_position()

    def on_timed_group_editor_mouse_release(self,widget, event):
        self.selected_box = None

    def on_timed_group_editor_mouse_move(self, widget, event):
        self.mouse_point.x = event.x
        self.mouse_point.y = event.y
        if self.selected_box:
            if self.selected_box == self.block_box:
                diff = self.mouse_point.diff(self.mouse_init_point)
                new_pos = self.selected_box_init_position.copy()
                new_pos.translate(diff.x, diff.y)
                self.selected_box.set_position(new_pos, rect=self.tge_rect)
                self.update_scrollbars()
            else:
                self.block_box.move_box(
                    self.selected_box, self.selected_box_init_position,
                    self.mouse_init_point, self.mouse_point,
                    beat=self.beat)
            self.redraw_timed_group_editor()

    def update_scrollbars(self):
        rect = Rect(0,0, self.tge_rect.width, self.tge_rect.height)

        scroll_x = self.block_box.get_scroll_x(rect)
        self.timed_group_editor_hscrollbar.set_value(scroll_x)

        scroll_y = self.block_box.get_scroll_y(rect)
        self.timed_group_editor_vscrollbar.set_value(scroll_y)

    def on_timed_group_editor_mouse_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            mult = 1.
        elif event.direction == Gdk.ScrollDirection.DOWN:
            mult = -1.
        if self.keyboard_state.control_key_pressed:
            self.block_box.zoom_x(1+.1*mult, self.mouse_point)
            self.redraw_timed_group_editor()
            self.update_scrollbars()

    def on_timed_group_editor_scrollbar_value_changed(self, scrollbar, scroll_dir):
        if not self.block_box:
            return
        value = scrollbar.get_value()
        rect = Rect(0,0, self.tge_rect.width, self.tge_rect.height)
        if scroll_dir == "horiz":
            self.block_box.set_scroll_x(value, rect)
        elif scroll_dir == "vert":
            self.block_box.set_scroll_y(value, rect)
        self.redraw_timed_group_editor()

    def on_key_press(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=True)

    def on_key_release(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=False)

    def quit(self, wiget, event):
        if self.audio_server:
            self.audio_server.close()
        AudioServer.close_all()
        Gtk.main_quit()

