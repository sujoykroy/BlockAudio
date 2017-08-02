from ..commons.colors import Color
from ..commons.point import Point
from ..commons import draw_utils
import cairo
import pango
import pangocairo

class AudioBlockBox(object):
    IdSeed = 0
    PIXEL_PER_SAMPLE = 10.
    BorderColor = Color.parse("000000")
    HeadColor = Color.parse("FF0000")
    DivColor = Color.parse("CCCCCC")
    BeatColor = Color.parse("555555")
    FontName = "12"

    def __init__(self, audio_block, parent_box=None, fill_color="0000FF"):
        self.id_num = AudioBlockBox.IdSeed+1
        AudioBlockBox.IdSeed += 1

        self.audio_block = audio_block
        self.parent_box = parent_box
        self.fill_color = Color.parse(fill_color)

        self.scale_x = 1.
        self.scale_y = 1.
        self.x = 0.
        self.y = 0.
        self.height = 50.
        self.update_size()

    def get_id(self):
        return self.id_num

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def get_postion(self):
        return Point(self.x, self.y)

    def update_size(self):
        self.width = self.audio_block.duration*AudioBlockBox.PIXEL_PER_SAMPLE

    def transform_point(self, point):
        point = point.copy()
        point.translate(-self.x, -self.y)
        point.scale(1./self.scale_x, 1./self.scale_y)
        return point

    def is_within(self, point):
        return self.x<=point.x<=self.x+self.width and self.y<=point.y<=self.y+self.height

    def set_size(self, width, height):
        if width<self.width:
            self.scale_x = float(width)/self.width
        else:
            self.scale_x = 1.
        if height<self.height:
            self.scale_y = float(height)/self.height
        else:
            self.scale_y = 1.
        print self.scale_x, self.scale_y

    def __eq__(self, other):
        return isinstance(self, AudioBlockBox) and other.id_num == self.id_num

    def pre_draw(self, ctx):
        if self.parent_box:
            self.parent_box.pre_draw(ctx)
        ctx.translate(self.x, self.y)
        ctx.scale(self.scale_x, self.scale_y)

    def draw_path(self, ctx):
        ctx.rectangle(0, 0, self.width, self.height)

    def draw(self, ctx):
        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_fill(ctx, self.fill_color)

        ctx.save()
        self.pre_draw(ctx)
        pangocairo_context = pangocairo.CairoContext(ctx)
        pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

        desc_layout = pangocairo_context.create_layout()
        font = pango.FontDescription(self.FontName)
        desc_layout.set_wrap(pango.WRAP_WORD)
        desc_layout.set_font_description(font)
        desc_layout.set_alignment(pango.ALIGN_LEFT)

        desc = self.audio_block.get_description()
        desc_layout.set_markup(desc)

        desc_width, desc_height = desc_layout.get_pixel_extents()[1][2:]
        padding = 5

        if desc_width<self.width-2*padding:
            scale_x = (self.width-2*padding)/desc_width
            ctx.scale(scale_x, 1)
        if desc_height<self.height-2*padding:
            scale_y = (self.height-2*padding)/self.height
            ctx.scale(1, scale_y)

        pangocairo_context.update_layout(desc_layout)
        pangocairo_context.show_layout(desc_layout)
        ctx.restore()

        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.BorderColor)

    def show_current_position(self, ctx):
        x = self.audio_block.current_pos*AudioBlockBox.PIXEL_PER_SAMPLE
        ctx.save()
        self.pre_draw(ctx)
        ctx.move_to(x, 0)
        ctx.line_to(x, self.height)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.HeadColor)

    def show_beat_marks(self, ctx, beat):
        ctx.save()
        self.pre_draw(ctx)
        for x in beat.get_div_pixels(self.x, self.x+self.width):
            ctx.save()
            ctx.move_to(x, 0)
            ctx.line_to(x, self.height)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 2, self.DivColor)

