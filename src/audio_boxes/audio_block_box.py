from ..commons import Color
from ..commons import Point
from ..commons import Rect
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

    def set_position(self, point, rect=None):
        self.x = point.x
        self.y = point.y
        if rect:
            scaled_width = self.scale_x*self.width
            scaled_height = self.scale_y*self.height
            if scaled_width<rect.width:
                self.x = rect.left
            else:
                if self.x>rect.left:
                    self.x = rect.left
                elif self.x+scaled_width<rect.left+rect.width:
                    self.x = rect.left+rect.width-scaled_width
            if scaled_height<rect.height:
                self.y = rect.top
            else:
                if self.y>rect.top:
                    self.y = rect.top
                elif self.y+scaled_height<rect.top+rect.height:
                    self.y = rect.top+rect.height-scaled_height

    def update_size(self):
        self.width = self.audio_block.duration*AudioBlockBox.PIXEL_PER_SAMPLE

    def zoom_x(self, mult, center):
        rel_center = self.transform_point(center)
        self.scale_x *= mult
        after_center = self.reverse_transform_point(rel_center)
        shift = after_center.diff(center)
        self.x -= shift.x
        if self.x>0:
            self.x = 0
        self.y -= shift.y

    def set_scroll_x(self, frac, rect):
        scaled_width = self.width*self.scale_x
        extra_width = scaled_width-rect.width
        if extra_width<=0:
            return
        self.x = -extra_width*frac

    def get_scroll_x(self, rect):
        scaled_width = self.width*self.scale_x
        extra_width = scaled_width-rect.width
        if extra_width<=0:
            return 0.
        frac = -self.x*1.0/extra_width
        return frac

    def set_scroll_y(self, frac, rect):
        scaled_height = self.height*self.scale_y
        extra_height = scaled_height-rect.height
        if extra_height<=0:
            return
        self.y = -extra_height*frac

    def get_scroll_y(self, rect):
        scaled_height = self.height*self.scale_y
        extra_height = scaled_height-rect.height
        if extra_height<=0:
            return 0.
        frac = -self.y*1.0/extra_height
        return frac

    def transform_point(self, point):
        point = point.copy()
        point.translate(-self.x, -self.y)
        point.scale(1./self.scale_x, 1./self.scale_y)
        return point

    def reverse_transform_point(self, point):
        point = point.copy()
        point.scale(self.scale_x, self.scale_y)
        point.translate(self.x, self.y)
        return point

    def abs_reverse_transform_point(self, point):
        point = self.reverse_transform_point(point)
        if self.parent_box:
            point = self.parent_box.abs_reverse_transform_point(point)
        return point

    def get_rect(self, left_top, right_bottom):
        left_top = self.transform_point(left_top)
        right_bottom = self.transform_point(right_bottom)
        return Rect(left_top.x, left_top.y, right_bottom.x-left_top.x, right_bottom.y-left_top.y)

    def is_within(self, point):
        return self.x<=point.x<=self.x+self.width and self.y<=point.y<=self.y+self.height

    def get_expander(self, at):
        if self.expander_box.is_within(at):
            return self.expander_box
        return None

    def set_size(self, width, height=None):
        if width<self.width:
            self.scale_x = float(width)/self.width
        else:
            self.scale_x = 1.
        if height:
            if height<self.height:
                self.scale_y = float(height)/self.height
            else:
                self.scale_y = 1.

    def __eq__(self, other):
        return isinstance(other, AudioBlockBox) and other.id_num == self.id_num

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

        desc = self.audio_block.get_description()
        text_start_point = self.abs_reverse_transform_point(Point(0, 0))
        text_end_point = self.abs_reverse_transform_point(Point(self.width, self.height))
        text_size = text_end_point.diff(text_start_point)
        text_size.translate(-5,-5)
        draw_utils.draw_text(ctx, desc,
                    text_start_point.x, text_start_point.y,
                    font_name=self.FontName,
                    width=text_size.x, fit_width=True,
                    height=text_size.y, fit_height=True,
                    text_color="000000")


        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.BorderColor)

        self.expander_box.draw(ctx)

    def show_current_position(self, ctx):
        x = self.audio_block.play_pos*AudioBlockBox.PIXEL_PER_SAMPLE
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
            bw = 200
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
