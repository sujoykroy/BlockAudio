from ..commons.colors import Color
from ..commons.point import Point
from ..commons import draw_utils
from expander_box import ExpanderBox
import cairo
import pango
import pangocairo
from ..audio_blocks import AudioSamplesBlock

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
        self.image = None

        self.expander_box = ExpanderBox(self)
        self.update_size()

    def get_id(self):
        return self.id_num

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def get_position(self):
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

    def get_expander(self, at):
        if self.expander_box.is_within(at):
            return self.expander_box
        return None

    def set_size(self, width, height):
        if width<self.width:
            self.scale_x = float(width)/self.width
        else:
            self.scale_x = 1.
        if height<self.height:
            self.scale_y = float(height)/self.height
        else:
            self.scale_y = 1.

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

        inclusive_width = self.audio_block.inclusive_duration*self.PIXEL_PER_SAMPLE
        x = 0
        image = self.get_image()
        if image:
            sx = inclusive_width*1./image.get_width()
            sy = self.height*1./image.get_height()
            while x<self.width:
                ctx.save()
                self.pre_draw(ctx)
                ctx.translate(x, 0)
                ctx.scale(sx, sy)
                ctx.set_source_surface(image)
                ctx.scale(1/sx, 1/sy)
                ctx.rectangle(0, 0, self.width-x, self.height)
                ctx.clip()
                ctx.paint()
                ctx.restore()

                ctx.save()
                self.pre_draw(ctx)
                self.draw_path(ctx)
                #ctx.clip()
                ctx.restore()
                x += inclusive_width
                if not self.audio_block.loop:
                    break

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

        self.expander_box.draw(ctx)

    def show_current_position(self, ctx):
        x = self.audio_block.current_pos*AudioBlockBox.PIXEL_PER_SAMPLE
        ctx.save()
        self.pre_draw(ctx)
        ctx.move_to(x, 0)
        ctx.line_to(x, self.height)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.HeadColor)

    def show_div_marks(self, ctx, beat):
        ctx.save()
        self.pre_draw(ctx)
        ctx.new_path()
        for x in beat.get_div_pixels(self.x, self.x+self.width):
            ctx.save()
            ctx.move_to(x, 0)
            ctx.line_to(x, self.height)
            ctx.restore()
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.DivColor)

    def show_beat_marks(self, ctx, beat):
        ctx.save()
        self.pre_draw(ctx)
        ctx.new_path()
        for x in beat.get_beat_pixels(self.x, self.x+self.width):
            ctx.save()
            ctx.move_to(x, 0)
            ctx.line_to(x, self.height)
            ctx.restore()
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.BeatColor)

    def show_border_line(self, ctx):
        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.BorderColor)

    def get_image(self):
        if self.image:
            return self.image

        if isinstance(self.audio_block, AudioSamplesBlock):
            bw = 100
            bh = 50
            self.image = cairo.ImageSurface(cairo.FORMAT_ARGB32, bw, bh)
            ctx = cairo.Context(self.image)
            samples = self.audio_block.samples
            xunit = samples.shape[0]*1./bw
            yunit = bh/(2*samples.shape[1])
            for r in xrange(samples.shape[1]):
                ctx.save()
                #ctx.translate(0, r*(bh*1./samples.shape[1]))
                for x in xrange(bw):
                    i = int(x*xunit)
                    y = (2*r+(1-samples[i][r]))*yunit
                    if x == 0:
                        ctx.move_to(x, y)
                    else:
                        ctx.line_to(x, y)
                ctx.restore()
                draw_utils.draw_stroke(ctx, 1, "00FFFF")
            #self.image.write_to_png("/home/sujoy/Temporary/test.png")
        return self.image
