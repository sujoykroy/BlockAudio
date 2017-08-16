from gi.repository import Gtk, GObject
from ..gui_utils.file_op import FileSelect
from ..commons import draw_utils, Color
import moviepy.editor
import numpy
import cairo
from ..audio_blocks import AudioServer
from ..audio_boxes import AudioBlockBox
import time

class FileInstruPage(object):
    CurveColor = Color.parse("FFF422")

    def __init__(self, owner, instru):
        self.owner = owner
        self.instru = instru
        self.audio_server = None
        self.audio_block = None
        self.image_surface = None
        self.tab_name_label = Gtk.Label()

        self.name_label = Gtk.Label("Name")
        self.name_entry = Gtk.Entry()
        self.name_save_button = Gtk.Button("Rename")
        self.name_save_button.connect("clicked", self.name_save_button_clicked)

        self.source_label = Gtk.Label("Source")
        self.filename_select = FileSelect("audio")
        #self.filename_select.connect("file-selected", self.filename_selected)

        self.duration_heading_label = Gtk.Label("Duration")
        self.duration_value_entry = Gtk.Entry()
        self.duration_value_entry.set_editable(False)

        #play/pause
        self.play_button = Gtk.Button("Play")
        self.play_button.connect("clicked", self.play_button_clicked)
        self.pause_button = Gtk.Button("Pause")
        self.pause_button.connect("clicked", self.pause_button_clicked)

        self.graph_board = Gtk.DrawingArea()
        self.graph_board.connect("draw", self.on_graph_board_draw)

        self.info_grid = Gtk.Grid()
        self.info_grid.set_column_spacing(5)
        self.info_grid.attach(self.name_label, left=0, top=0, width=1, height=1)
        self.info_grid.attach(self.name_entry, left=1, top=0, width=1, height=1)
        self.info_grid.attach(self.name_save_button, left=2, top=0, width=1, height=1)
        self.info_grid.attach(self.source_label, left=0, top=1, width=1, height=1)
        self.info_grid.attach(self.filename_select, left=1, top=1, width=3, height=1)
        self.info_grid.attach(self.duration_heading_label, left=4, top=1, width=1, height=1)
        self.info_grid.attach(self.duration_value_entry, left=5, top=1, width=1, height=1)

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
        self.root_box.pack_start(self.graph_board, expand=True, fill=True, padding=5)

    def update_tab_name_label(self):
        self.tab_name_label.set_markup("{0}<sup> fii</sup>".format(self.instru.get_name()))

    def get_widget(self):
        return self.root_box

    def get_tab_name_label(self):
        return self.tab_name_label

    def init_show(self):
        #self.instru.build(self.owner.beat)
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

    def name_save_button_clicked(self, widget):
        new_name = self.name_entry.get_text().strip()
        if new_name and new_name != self.instru.get_name():
            if self.owner.rename_instru(self.instru, new_name):
                self.update_tab_name_label()
        self.name_entry.set_text(self.instru.get_name())

    def play_button_clicked(self, wiget):
        if not self.audio_server:
            self.audio_server = AudioServer.get_default()
        if not self.audio_block:
            self.audio_block = self.instru.get_file_block()
            self.audio_block.set_no_loop()
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
        self.graph_board.queue_draw()
        return not self.audio_block.paused

    def pause_button_clicked(self, wiget):
        if not self.audio_server:
            return
        self.audio_block.pause()
        self.play_button.show()
        self.pause_button.hide()

    PlayHeadColor = Color.parse("FF0000")
    LineColor = Color.parse("000000")

    def on_graph_board_draw(self, widget, ctx):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        if not self.image_surface or \
               self.image_surface.get_width() != w or \
               self.image_surface.get_height() != h:
            self.build_image_surface(w*.8, h)

        ctx.save()
        ctx.scale(w*1./self.image_surface.get_width(), h*1./self.image_surface.get_height())
        ctx.set_source_surface(self.image_surface)
        ctx.paint()
        ctx.restore()

        #channel sperator
        audioclip = moviepy.editor.AudioFileClip(self.instru.filename)
        for ch in xrange(1, audioclip.nchannels):
            ctx.new_path()
            ctx.save()
            ctx.scale(1, h/4.)
            ctx.translate(0, ch*2)
            ctx.move_to(0, 0)
            ctx.line_to(w, 0)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 1, self.LineColor)

        #show current playhead
        if self.audio_block:
            pos = self.audio_block.play_pos
            pos_frac = pos*1./self.audio_block.duration
            ctx.move_to(w*pos_frac, 0)
            ctx.line_to(w*pos_frac, h)
            draw_utils.draw_stroke(ctx, 1, self.PlayHeadColor)

        #show div marks
        duration = self.instru.get_base_block().duration
        scale_x = w*1./(duration*AudioBlockBox.PIXEL_PER_SAMPLE)

        for x in self.owner.beat.get_div_pixels(0, w, 1/scale_x):
            print x
            x *= scale_x
            ctx.move_to(x, 0)
            ctx.line_to(x, h)
            draw_utils.draw_stroke(ctx, 1, AudioBlockBox.DivColor)

        #show beat marks
        for index, x in self.owner.beat.get_beat_pixels(0, w, 50/scale_x):
            x *= scale_x
            ctx.move_to(x, 0)
            ctx.line_to(x, h)
            draw_utils.draw_stroke(ctx, 1, AudioBlockBox.BeatColor)
            draw_utils.draw_text(
                ctx, "{0}".format(index+1),x+2, 0,
                font_name="8", text_color=AudioBlockBox.BeatTextColor)

        ctx.rectangle(0, 0, w, h)
        draw_utils.draw_stroke(ctx, 1, self.LineColor)

    def build_image_surface(self, w, h):
        w = int(w)
        h = int(h)
        surface = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
        ctx = cairo.Context(surface)
        audioclip = moviepy.editor.AudioFileClip(self.instru.filename)
        xunit = audioclip.duration*1./w
        for ch in xrange(audioclip.nchannels):
            ctx.save()
            ctx.scale(1, h/4.)
            ctx.translate(0, ch*2)
            for x in xrange(w):
                sample = audioclip.get_frame(x*xunit)
                if x == 0:
                    ctx.move_to(x, 1-sample[ch])
                else:
                    ctx.line_to(x, 1-sample[ch])
            ctx.restore()
            draw_utils.draw_stroke(ctx, 1, self.CurveColor)
        self.image_surface = surface
