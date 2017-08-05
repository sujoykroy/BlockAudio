from gi.repository import Gtk, Gdk
from ..commons import Point, Interpolator, draw_utils, Color
import math
import numpy

class InterpEditor(Gtk.Grid):
    CIRCLE_SIZE = 5.
    CircleFillColor = Color.parse("FFFFFF")
    CircleBorderColor = Color.parse("000000")
    CureveStrokeColor = Color.parse("0000FF")
    GridStrokeColor  = Color.parse("CCCCCC")
    GridDeepStrokeColor = Color.parse("FF0000")

    def __init__(self, board_width, board_height, keyboard_state, **kwarg):
        super(InterpEditor, self).__init__(**kwarg)
        self.connect("key-press-event", self.on_key_press)
        self.board_width = board_width
        self.board_height = board_height

        self.board = Gtk.DrawingArea()
        #self.board.set_size_request(400, 300)
        self.attach(self.board, left=0, top=0, width=1, height=1)
        self.board.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)

        self.board.connect("draw", self.on_board_draw)
        self.board.set_size_request(board_width, board_height)
        #self.board.connect("configure-event", self.on_board_configure_event)
        self.board.connect("button-press-event", self.on_board_mouse_press)
        self.board.connect("button-release-event", self.on_board_mouse_release)
        self.board.connect("motion-notify-event", self.on_board_mouse_move)
        #self.board.connect("scroll-event", self.on_board_mouse_scroll)

        self.interpolator = None
        self.mouse_point = Point(0, 0)
        self.mouse_init_point = Point(0, 0)
        self.selected_point = None
        self.selected_point_index = -1

    def on_key_press(self, widget, event):
        print event

    def set_interpolator(self, interpolator):
        self.interpolator = interpolator
        self.board.queue_draw()

    def transform_point(self, point):
        point = point.copy()
        point.scale(1./self.board_width, 1./self.board_height)
        point.y = 1-point.y
        return point

    def reverse_transform_point(self, point):
        point = point.copy()
        point.y = 1-point.y
        point.scale(self.board_width, self.board_height)
        return point

    def on_board_mouse_press(self, widget, event):
        self.mouse_init_point.x = self.mouse_point.x
        self.mouse_init_point.y = self.mouse_point.y

        self.selected_point = None
        self.selected_point_index = -1

        if not self.interpolator:
            return

        ms_point = self.transform_point(self.mouse_point)
        for i in xrange(len(self.interpolator.points)):
            interp_point = self.interpolator.points[i]
            interp_point = self.reverse_transform_point(interp_point)
            if interp_point.distance(self.mouse_point)<self.CIRCLE_SIZE:
                self.selected_point = self.interpolator.points[i]
                self.selected_point_index = i
                break

        if event.button == 1 and not self.selected_point:#Left mouse
            if event.type == Gdk.EventType._2BUTTON_PRESS:#double button click
                self.interpolator.add_point(ms_point)
                self.board.queue_draw()

    def on_board_mouse_release(self,widget, event):
        self.selected_point = None
        self.selected_point_index = -1

    def on_board_mouse_move(self, widget, event):
        self.mouse_point.x = event.x
        self.mouse_point.y = event.y
        if self.selected_point:
            current_point = self.transform_point(self.mouse_point)
            if current_point.y>1:
                current_point.y = 1
            elif current_point.y<0:
                current_point.y = 0
            if current_point.x<0:
                current_point.x = 0
            elif current_point.x>1:
                current_point.x = 1

            if self.selected_point_index in  (0, 1):
                 self.selected_point.y = current_point.y
            else:
                self.selected_point.copy_from(current_point)

            for i in xrange(len(self.interpolator.points)):
                if i == self.selected_point_index:
                    continue
                interp_point = self.interpolator.points[i]
                interp_point = self.reverse_transform_point(interp_point)
                if interp_point.distance(self.mouse_point)<self.CIRCLE_SIZE*.5:
                    if self.interpolator.remove_point_at_index(i):
                        self.selected_point = None
                        self.selected_point_index = -1
                    break

            self.interpolator.rebuild()
            self.board.queue_draw()

    def _draw_circle_path(self, ctx, point):
        ctx.save()
        ctx.translate(point.x*self.board_width, self.board_height*(1-point.y))
        ctx.scale(self.CIRCLE_SIZE, self.CIRCLE_SIZE)
        ctx.move_to(1, 0)
        ctx.arc(0, 0, 1, 0, math.pi*2)
        ctx.restore()

    def on_board_draw(self, widget, ctx):
        if not self.interpolator:
            return

        ctx.rectangle(0, 0, self.board_width, self.board_height)
        draw_utils.draw_fill(ctx, "FFFFFF")

        y_line_count = 10
        for yc in xrange(y_line_count):
            y = self.board_height*yc*1./y_line_count
            ctx.move_to(0, y)
            ctx.line_to(self.board_width, y)
        x_line_count = 10
        for xc in xrange(x_line_count):
            x = self.board_width*xc*1./x_line_count
            ctx.move_to(x, 0)
            ctx.line_to(x, self.board_height)
        draw_utils.draw_stroke(ctx, 1, self.GridStrokeColor)

        ctx.move_to(0, self.board_height*.5)
        ctx.line_to(self.board_width, self.board_height*.5)

        ctx.move_to(self.board_width*.5, 0)
        ctx.line_to(self.board_width*.5, self.board_height)
        draw_utils.draw_stroke(ctx, 1, self.GridDeepStrokeColor)

        xs = numpy.arange(0, self.board_width, dtype=numpy.float32)
        ys = self.interpolator.get_values(xs/self.board_width)
        ctx.save()
        ctx.scale(1, self.board_height)
        #ctx.translate(0, .5)
        #ctx.scale(1, -1)
        for i in xrange(len(xs)):
            if i == 0:
                ctx.move_to(xs[i], 1-ys[i])
            else:
                ctx.line_to(xs[i], 1-ys[i])
        ctx.restore()
        draw_utils.draw_stroke(ctx, 1, self.CureveStrokeColor)

        for point in self.interpolator.points:
            self._draw_circle_path(ctx, point)
            draw_utils.draw_fill(ctx, self.CircleFillColor)
            self._draw_circle_path(ctx, point)
            draw_utils.draw_stroke(ctx, 1, self.CircleBorderColor)

