from gi.repository import Gtk, Gdk, GObject
from ..audio_boxes import *
from ..audio_blocks import *
from ..commons import Point, Rect
from ..commons import MusicNote
from .. import gui_utils

class TimedGroupPage(object):
    def __init__(self, owner, audio_block):
        self.owner = owner
        self.audio_block = audio_block
        self.mouse_point = Point(0., 0.)
        self.mouse_init_point = Point(0., 0.)
        self.audio_server = None
        self.current_pos_selected = False

        self.selected_block_box = None
        self.selected_box = None
        self.tge_rect = Rect(0, 0, 1, 1)

        if isinstance(self.audio_block, AudioTimedGroup):
            block_box = AudioTimedGroupBox(self.audio_block)
        else:
            block_box = AudioBlockBox(self.audio_block)
        self.block_box = block_box

        self.tab_name_label = Gtk.Label()

        self.name_label = Gtk.Label("Name")
        self.name_entry = Gtk.Entry()
        self.name_save_button = Gtk.Button("Rename")
        self.name_save_button.connect("clicked", self.name_save_button_clicked)

        self.duration_label = Gtk.Label("Duration")
        self.duration_spin_button =  Gtk.SpinButton()
        self.duration_spin_button.set_digits(3)
        self.duration_spin_button.set_range(0, 10000000)
        self.duration_spin_button.set_increments(1, 1)
        self.duration_spin_button.connect(
            "value-changed", self.duration_spin_button_value_changed)

        self.duration_unit_combo_box = gui_utils.NameValueComboBox()
        self.duration_unit_combo_box.build_and_set_model(AudioBlock.get_time_unit_model())
        self.duration_unit_combo_box.set_value("Beat")
        self.duration_unit_combo_box.connect(
            "changed", self.duration_unit_combo_box_changed)

        #play/pause
        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

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

        #child block edit
        self.child_block_edit_box = Gtk.Grid()
        self.child_block_edit_box.set_column_spacing(2)

        self.child_block_instru_edit_button = Gtk.Button("Instrument")
        self.child_block_block_edit_button = Gtk.Button("Block")

        self.child_block_note_combo_box = gui_utils.NameValueComboBox()
        self.child_block_note_combo_box.build_and_set_model(MusicNote.get_names())
        self.child_block_note_combo_box.connect(
            "changed", self.child_block_note_combo_box_changed)

        self.child_block_duration_label = Gtk.Label("Duration")
        self.child_block_duration_spin_button =  Gtk.SpinButton()
        self.child_block_duration_spin_button.set_digits(3)
        self.child_block_duration_spin_button.set_range(0, 10000000)
        self.child_block_duration_spin_button.set_increments(1, 1)
        self.child_block_duration_spin_button.connect(
            "value-changed", self.child_block_duration_spin_button_value_changed)

        self.child_block_duration_unit_combo_box = gui_utils.NameValueComboBox()
        self.child_block_duration_unit_combo_box.build_and_set_model(
             AudioBlock.get_time_unit_model())
        self.child_block_duration_unit_combo_box.set_value("Beat")
        self.child_block_duration_unit_combo_box.connect(
            "changed", self.child_block_duration_unit_combo_box_changed)

        self.child_block_start_label = Gtk.Label("Start At")
        self.child_block_start_spin_button =  Gtk.SpinButton()
        self.child_block_start_spin_button.set_digits(3)
        self.child_block_start_spin_button.set_range(0, 10000000)
        self.child_block_start_spin_button.set_increments(1, 1)
        self.child_block_start_spin_button.connect(
            "value-changed", self.child_block_start_spin_button_value_changed)

        self.child_block_start_unit_combo_box = gui_utils.NameValueComboBox()
        self.child_block_start_unit_combo_box.build_and_set_model(
            AudioBlock.get_time_unit_model())
        self.child_block_start_unit_combo_box.set_value("Beat")
        self.child_block_start_unit_combo_box.connect(
            "changed", self.child_block_start_unit_combo_box_changed)

        self.child_block_instru_label = Gtk.Label("Instrument")
        self.child_block_block_label = Gtk.Label("Block")

        self.child_block_edit_box.attach(
                self.child_block_instru_label, left=5, top=2, width=2, height=1)
        self.child_block_edit_box.attach(
                self.child_block_block_label, left=5, top=2, width=2, height=1)

        self.child_block_edit_box.attach(
                self.child_block_instru_edit_button, left=7, top=2, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_block_edit_button, left=7, top=2, width=1, height=1)

        self.child_block_edit_box.attach(
                Gtk.Label("Note"), left=5, top=1, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_note_combo_box, left=6, top=1, width=1, height=1)

        self.child_block_edit_box.attach(
                Gtk.Label("Start At"), left=1, top=1, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_start_spin_button, left=2, top=1, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_start_unit_combo_box, left=3, top=1, width=1, height=1)

        self.child_block_edit_box.attach(
                Gtk.Label("Duration"), left=1, top=2, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_duration_spin_button, left=2, top=2, width=1, height=1)
        self.child_block_edit_box.attach(
                self.child_block_duration_unit_combo_box, left=3, top=2, width=1, height=1)


        self.control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.control_grid = Gtk.Grid()
        self.control_box.pack_start(self.control_grid, expand=True, fill=True, padding=0)

        self.control_grid.attach(self.name_label, left=0, top=0, width=1, height=1)
        self.control_grid.attach(self.name_entry, left=1, top=0, width=2, height=1)
        self.control_grid.attach(self.name_save_button, left=3, top=0, width=1, height=1)

        self.control_grid.attach(self.duration_label, left=0, top=1, width=1, height=1)
        self.control_grid.attach(self.duration_spin_button, left=1, top=1, width=1, height=1)
        self.control_grid.attach(self.duration_unit_combo_box, left=2, top=1, width=1, height=1)

        self.play_button.props.valign = Gtk.Align.START
        self.pause_button.props.valign = Gtk.Align.START

        self.play_pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.play_pause_box.pack_end(self.play_button, expand=False, fill=False, padding=0)
        self.play_pause_box.pack_end(self.pause_button, expand=False, fill=False, padding=0)
        self.control_box.pack_end(self.play_pause_box, expand=True, fill=True, padding=0)

        self.hcontainer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hcontainer.pack_start(
                self.timed_group_editor, expand=True, fill=True, padding=0)
        self.hcontainer.pack_end(
                self.timed_group_editor_vscrollbar, expand=False, fill=False, padding=0)

        self.vcontainer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vcontainer.pack_start(
                self.control_box, expand=False, fill=False, padding=0)
        self.vcontainer.pack_start(
                self.hcontainer, expand=True, fill=True, padding=5)
        self.vcontainer.pack_end(
                self.child_block_edit_box, expand=False, fill=False, padding=0)
        self.vcontainer.pack_end(
                self.timed_group_editor_hscrollbar, expand=False, fill=False, padding=0)

    def update_tab_name_label(self):
        self.tab_name_label.set_markup("{0}<sup> bg</sup>".format(self.audio_block.get_name()))

    def get_widget(self):
        return self.vcontainer

    def get_tab_name_label(self):
        return self.tab_name_label

    def init_show(self):
        self.audio_block.build(self.owner.beat)
        self.name_entry.set_text(self.audio_block.get_name())
        self.duration_unit_combo_box.set_value(self.audio_block.duration_unit)
        self.duration_spin_button.set_value(self.audio_block.duration_value)

        self.update_tab_name_label()
        self.vcontainer.show_all()
        self.pause_button.hide()
        self.child_block_edit_box.hide()

    def cleanup(self):
        if self.audio_server:
            self.audio_server.remove_block(self.audio_block)

    def show_audio_block_info(self):
        if self.selected_block_box:
            block = self.selected_block_box.audio_block
            self.child_block_note_combo_box.set_value(block.music_note)
            self.child_block_duration_spin_button.set_value(block.duration_value)
            self.child_block_duration_unit_combo_box.set_value(block.duration_unit)
            #self.child_block_start_spin_button.set_value(block.duration_value)
            #self.child_block_start_unit_combo_box.set_value(block.duration_unit)
            self.child_block_edit_box.show()
        else:
            self.child_block_edit_box.hide()

    def name_save_button_clicked(self, widget):
        new_name = self.name_entry.get_text().strip()
        if new_name and new_name != self.audio_block.get_name():
            self.owner.rename_timed_group(self.audio_block, new_name)
            self.name_entry.set_text(self.audio_block.get_name())
            self.update_tab_name_label()

    def duration_spin_button_value_changed(self, widget):
        self.audio_block.set_duration_value(widget.get_value(), self.owner.beat)
        prev_width = self.block_box.width
        self.block_box.update_size()
        if self.block_box.width>prev_width and self.block_box.x==0:
            self.block_box.set_size(self.tge_rect.width)
        self.redraw_timed_group_editor()

    def duration_unit_combo_box_changed(self, widget):
        self.audio_block.set_duration_unit(widget.get_value(), self.owner.beat)
        self.duration_spin_button.set_value(self.audio_block.duration_value)

    def child_block_duration_spin_button_value_changed(self, widget):
        pass

    def child_block_duration_unit_combo_box_changed(self, widget):
        pass

    def child_block_start_spin_button_value_changed(self, widget):
        pass

    def child_block_start_unit_combo_box_changed(self, widget):
        pass

    def child_block_note_combo_box_changed(self, widget):
        if self.selected_block_box:
            note_name = self.child_block_note_combo_box.get_value()
            if note_name:
                self.selected_block_box.audio_block.set_note(note_name)
                self.block_box.update_size()
                self.timed_group_editor.queue_draw()

    def play_button_clicked(self, wiget):
        if not self.audio_server:
            self.audio_server = AudioServer.get_default()
            self.audio_server.add_block(self.audio_block)
        self.audio_block.play()
        self.play_button.hide()
        self.pause_button.show()
        self.timer_id = GObject.timeout_add(100, self.on_playahead_movement)

    def pause_button_clicked(self, wiget):
        if not self.audio_server:
            return
        self.audio_block.pause()
        self.play_button.show()
        self.pause_button.hide()

    def on_playahead_movement(self):
        self.redraw_timed_group_editor()
        return self.audio_server and not self.audio_server.paused

    def redraw_timed_group_editor(self):
        self.timed_group_editor.queue_draw()

    def update_scrollbars(self):
        rect = Rect(0,0, self.tge_rect.width, self.tge_rect.height)

        scroll_x = self.block_box.get_scroll_x(rect)
        self.timed_group_editor_hscrollbar.set_value(scroll_x)

        scroll_y = self.block_box.get_scroll_y(rect)
        self.timed_group_editor_vscrollbar.set_value(scroll_y)

    def on_timed_group_editor_draw(self, widget, ctx):
        if not self.block_box:
            return
        self.block_box.show_div_marks(ctx, self.owner.beat, self.tge_rect)

        rect = self.block_box.get_rect(Point(0,0), Point(self.tge_rect.width, self.tge_rect.height))
        self.block_box.draw(ctx, rect, self.selected_block_box)

        self.block_box.show_beat_marks(ctx, self.owner.beat, self.tge_rect)
        self.block_box.show_current_position(ctx, rect)
        self.block_box.show_outer_border_line(ctx)
        ctx.rectangle(0, 0, widget.get_allocated_width(), widget.get_allocated_height())
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.stroke()

    def on_timed_group_editor_configure_event(self, widget, event):
        tge = self.timed_group_editor
        self.tge_rect = Rect(0, 0, tge.get_allocated_width(), tge.get_allocated_height())
        if self.block_box:
            self.block_box.set_size(self.tge_rect.width, None)

    def on_timed_group_editor_mouse_press(self, widget, event):
        self.mouse_init_point.x = self.mouse_point.x
        self.mouse_init_point.y = self.mouse_point.y
        if event.button == 1:#Left mouse
            new_block = None
            if self.owner.keyboard_state.control_key_pressed and \
               self.owner.keyboard_state.shift_key_pressed:
                block = self.owner.get_selected_timed_group()
                if block and block != self.audio_block:
                    new_block = block
            elif self.owner.keyboard_state.control_key_pressed:
                instru = self.owner.get_selected_instru()
                if instru:
                    new_block = instru.create_note_block()

            if new_block:
                pos = self.block_box.transform_point(self.mouse_point)
                self.block_box.add_block(
                    new_block, at=pos.x, y=pos.y, sample_unit=False)
                if len(self.audio_block.blocks) == 1:
                    self.block_box.set_size(self.tge_rect.width, None)
                self.redraw_timed_group_editor()
            else:
                if self.block_box:
                    self.selected_box = self.block_box.find_box_at(self.mouse_point)
                if not self.selected_box:
                    self.current_pos_selected=self.block_box.is_abs_within_current_pos(
                        self.mouse_point)
                else:
                    self.current_pos_selected = False
                    self.redraw_timed_group_editor()

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
        self.current_pos_selected = None

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
                    beat=self.owner.beat)
            self.redraw_timed_group_editor()
        elif self.current_pos_selected:
            self.block_box.set_current_position(self.mouse_point)
            self.redraw_timed_group_editor()

    def on_timed_group_editor_mouse_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            mult = 1.
        elif event.direction == Gdk.ScrollDirection.DOWN:
            mult = -1.
        if self.owner.keyboard_state.control_key_pressed:
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