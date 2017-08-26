from gi.repository import Gtk, Gdk
import cairo
from ..commons import draw_utils, Color, Point
from ..audio_boxes import AudioBlockBox
from ..audio_blocks import AudioFileBlock

class SamplesBlockViewer(Gtk.Box):
    CurveColor = Color.parse("FFF422")
    PlayHeadColor = Color.parse("FF0000")
    LineColor = Color.parse("000000")

    def __init__(self, owner, *arg, **kwarg):
        super(SamplesBlockViewer, self).__init__(*arg, **kwarg)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.audio_block = None
        self.image_surface = None
        self.image_name = None
        self.owner = owner
        self.board_zoom = 1.
        self.board_offset_x = 0
        self.board_offset_y = 0
        self.mouse_point = Point(0, 0)
        self.mouse_init_point = Point(0, 0)
        self.board_init_offset = Point(0, 0)
        self.move_board = False

        #timed group editor
        self.graph_board = Gtk.DrawingArea()
        self.graph_board.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)

        self.graph_board.connect(
                "draw", self.on_graph_board_draw)

        self.graph_board.connect(
                "configure-event", self.on_graph_board_configure_event)
        self.graph_board.connect(
                "button-press-event", self.on_graph_board_mouse_press)
        self.graph_board.connect(
                "button-release-event", self.on_graph_board_mouse_release)
        self.graph_board.connect(
                "motion-notify-event", self.on_graph_board_mouse_move)
        self.graph_board.connect(
                "scroll-event", self.on_graph_board_mouse_scroll)

        #timed group editor vertical scroller
        self.graph_board_vadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.graph_board_vscrollbar = Gtk.VScrollbar(self.graph_board_vadjust)
        self.graph_board_vscrollbar.connect(
            "value-changed", self.on_graph_board_scrollbar_value_changed, "vert")

        #timed group editor horizontal scroller
        self.graph_board_hadjust = Gtk.Adjustment(0, 0, 1., .01, 0, 0)
        self.graph_board_hscrollbar = Gtk.HScrollbar(self.graph_board_hadjust)
        self.graph_board_hscrollbar.connect(
            "value-changed", self.on_graph_board_scrollbar_value_changed, "horiz")

        self.hcontainer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hcontainer.pack_start(
            self.graph_board, expand=True, fill=True, padding=0)
        self.hcontainer.pack_start(
            self.graph_board_vscrollbar, expand=False, fill=False, padding=0)

        self.pack_start(self.hcontainer, expand=True, fill=True, padding=0)
        self.pack_start(self.graph_board_hscrollbar, expand=False, fill=False, padding=0)
        self.show_all()

    def set_block(self, audio_samples_block):
        self.audio_block = audio_samples_block
        self.image_surface = None
        self.image_name = None
        self.board_zoom = 1.
        self.board_offset_x = 0
        self.board_offset_y = 0
        self.redraw()

    def redraw(self, full=False):
        if full:
            self.image_surface = None
        self.graph_board.queue_draw()

    def generate_image_name(self):
        return "{0}{1}{2}{3}{4}".format(
            self.graph_board.get_allocated_width(),
            self.graph_board.get_allocated_height(),
            self.board_zoom,
            self.board_offset_x,
            self.board_offset_y)

    def on_graph_board_draw(self, widget, ctx):
        if not self.audio_block:
            return

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        image_name = self.generate_image_name()
        if not self.image_surface or self.image_name != image_name:
            self.build_image_surface(image_name, w*.8, h)

        ctx.save()
        ctx.scale(w*1./self.image_surface.get_width(), h*1./self.image_surface.get_height())
        ctx.set_source_surface(self.image_surface)
        ctx.paint()
        ctx.restore()

        #channel separator
        for ch in xrange(1, self.audio_block.samples.shape[1]):
            ctx.new_path()
            ctx.save()
            ctx.translate(
                    -w*(self.board_zoom-1)*self.board_offset_x,
                    -h*(self.board_zoom-1)*self.board_offset_y)
            ctx.scale(self.board_zoom, self.board_zoom)
            ctx.scale(1, h/4.)
            ctx.translate(0, ch*2)
            ctx.move_to(0, 0)
            ctx.line_to(w, 0)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 1, self.LineColor)

        xunit_no_zoom =  self.audio_block.duration*AudioBlockBox.PIXEL_PER_SAMPLE/float(w)
        xunit = xunit_no_zoom/self.board_zoom

        #show div marks
        ofx = w*(self.board_zoom-1)*self.board_offset_x*xunit
        ctx.save()
        ctx.translate(
                    -w*(self.board_zoom-1)*self.board_offset_x,
                    -h*(self.board_zoom-1)*self.board_offset_y)
        ctx.scale(self.board_zoom, self.board_zoom)
        for x in self.owner.beat.get_div_pixels(ofx, ofx+w*xunit, 10*xunit):
            x /= xunit_no_zoom
            ctx.move_to(x, 0)
            ctx.line_to(x, h)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 1, AudioBlockBox.DivColor)

        #show beat marks
        ctx.save()
        ctx.translate(
                    -w*(self.board_zoom-1)*self.board_offset_x,
                    -h*(self.board_zoom-1)*self.board_offset_y)
        ctx.scale(self.board_zoom, self.board_zoom)
        for index, x in self.owner.beat.get_beat_pixels(ofx, ofx+w*xunit, 50*xunit):
            x /= xunit_no_zoom
            ctx.move_to(x, 0)
            ctx.line_to(x, h)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, AudioBlockBox.BeatColor)

        for index, x in self.owner.beat.get_beat_pixels(ofx, ofx+w*xunit, 50*xunit):
            x /= xunit
            x -= w*(self.board_zoom-1)*self.board_offset_x
            draw_utils.draw_text(
                ctx, "{0}".format(index+1),x+2, 0,
                font_name="8", text_color=AudioBlockBox.BeatTextColor)

        #show current playhead
        if self.audio_block:
            pos = self.audio_block.play_pos
            pos_pixel = pos*AudioBlockBox.PIXEL_PER_SAMPLE/xunit_no_zoom
            ctx.save()
            ctx.translate(
                    -w*(self.board_zoom-1)*self.board_offset_x,
                    -h*(self.board_zoom-1)*self.board_offset_y)
            ctx.scale(self.board_zoom, self.board_zoom)
            ctx.move_to(pos_pixel, 0)
            ctx.line_to(pos_pixel, h)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 1, self.PlayHeadColor)

        ctx.rectangle(0, 0, w, h)
        draw_utils.draw_stroke(ctx, 1, self.LineColor)

    def build_image_surface(self, image_name, w, h):
        w = int(w)
        h = int(h)
        surface = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
        ctx = cairo.Context(surface)

        xunit = self.audio_block.duration*1./(w*self.board_zoom)
        offset_sample = max(xunit*w*(self.board_zoom-1)*self.board_offset_x, 0)
        offset_sample = int(offset_sample)

        for ch in xrange(self.audio_block.samples.shape[1]):
            ctx.save()
            ctx.translate(0, -max(w*(self.board_zoom-1)*self.board_offset_y, 0))
            ctx.scale(1, h*self.board_zoom/4.)
            ctx.translate(0, ch*2)
            for x in xrange(w):
                if isinstance(self.audio_block, AudioFileBlock):
                    self.audio_block.load_samples()
                sample = self.audio_block.samples[offset_sample+int(x*xunit), ch]
                if x == 0:
                    ctx.move_to(x, 1-sample)
                else:
                    ctx.line_to(x, 1-sample)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 1, self.CurveColor)
        self.image_surface = surface
        self.image_name = image_name

    def on_graph_board_configure_event(self, widget, event):
        board = self.graph_board

    def on_graph_board_mouse_press(self, widget, event):
        self.mouse_init_point.x = self.mouse_point.x
        self.mouse_init_point.y = self.mouse_point.y
        self.move_board = False
        if event.button == 1:#Left mouse
            w = self.graph_board.get_allocated_width()
            extra_w = w*(self.board_zoom-1)
            ox = max(extra_w*self.board_offset_x, 0)
            ox += self.mouse_point.x
            xunit = self.audio_block.duration*1./(w*self.board_zoom)
            self.audio_block.set_current_pos(int(ox*xunit))
            self.audio_block.set_play_pos(int(ox*xunit))
            self.redraw()
        elif event.button == 3:#Left mouse
            self.move_board = True
            self.board_init_offset.x = self.board_offset_x
            self.board_init_offset.y = self.board_offset_y

    def on_graph_board_mouse_release(self,widget, event):
        self.move_board = False

    def on_graph_board_mouse_move(self, widget, event):
        self.mouse_point.x = event.x
        self.mouse_point.y = event.y
        if self.move_board:
            diff = self.mouse_init_point.diff(self.mouse_point)

            w = self.graph_board.get_allocated_width()
            extra_w = w*(self.board_zoom-1)
            ox = max(extra_w*self.board_init_offset.x, 0)
            ox += diff.x
            if extra_w<=0:
                self.board_offset_x = 0.
            else:
                self.board_offset_x = min(max(ox/extra_w, 0), 1)
            self.graph_board_hscrollbar.set_value(self.board_offset_x)

            h = self.graph_board.get_allocated_height()
            extra_h = h*(self.board_zoom-1)
            oy = max(extra_h*self.board_init_offset.y, 0)
            oy += diff.y
            if extra_h<=0:
                self.board_offset_y = 0.
            else:
                self.board_offset_y = min(max(oy/extra_h, 0), 1)
            self.graph_board_vscrollbar.set_value(self.board_offset_y)

            self.redraw()

    def on_graph_board_mouse_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            mult = 1.
        elif event.direction == Gdk.ScrollDirection.DOWN:
            mult = -1.

        w = self.graph_board.get_allocated_width()
        extra_w = w*(self.board_zoom-1)
        ox = max(extra_w*self.board_offset_x, 0)

        h = self.graph_board.get_allocated_height()
        extra_h = h*(self.board_zoom-1)
        oy = max(extra_h*self.board_offset_y, 0)

        rel_point = self.mouse_point.copy()
        rel_point.x += ox
        rel_point.x /= self.board_zoom
        rel_point.y += oy
        rel_point.y /= self.board_zoom

        self.board_zoom = max(self.board_zoom*(1+mult*.01), 1)

        new_extra_w = w*(self.board_zoom-1)
        new_extra_h = h*(self.board_zoom-1)

        after_point = rel_point.copy()
        after_point.x *= self.board_zoom
        after_point.y *= self.board_zoom
        after_point.x -= ox
        after_point.y -= oy

        diff = after_point.diff(self.mouse_point)
        if new_extra_w<=0:
            self.board_offset_x = 0
        else:
            self.board_offset_x = min(max((ox+diff.x)/new_extra_w, 0), 1)
        if new_extra_h<=0:
            self.board_offset_y = 0
        else:
            self.board_offset_y = min(max((oy+diff.y)/new_extra_h, 0), 1)

        self.graph_board_hscrollbar.set_value(self.board_offset_x)
        self.graph_board_hscrollbar.set_value(self.board_offset_x)
        self.redraw()

    def on_graph_board_scrollbar_value_changed(self, scrollbar, scroll_dir):
        if not self.audio_block:
            return
        value = scrollbar.get_value()
        if scroll_dir == "horiz":
            self.board_offset_x = value
        elif scroll_dir == "vert":
            self.board_offset_y = value
        self.redraw()
