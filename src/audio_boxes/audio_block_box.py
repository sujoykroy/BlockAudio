from ..commons import Color
from ..commons import Point
from ..commons import Rect
from ..commons import draw_utils
from pointer_box import PointerBox
import cairo
from ..audio_blocks import AudioSamplesBlock

class AudioBlockBox(object):
    IdSeed = 0
    PIXEL_PER_SAMPLE = 10.
    SpreadFraction = .35

    BorderColor = Color.parse("000000")
    CurrentPosColor = Color.parse("FF0000")
    DivColor = Color.parse("b5a600")
    BeatColor = Color.parse("0098b5")
    FontName = "8"
    SpreadBoxStartColor = Color.parse("FFFFFF")
    SpreadBoxEndColor = Color.parse("FFFFFF")
    DescBorderColor = Color.parse("000000")
    DescFillColor = Color.parse("FFFFFF")
    DescTextColor = Color.parse("000000")
    HeadBoxColor= Color.parse("f458e0")
    TailBoxColor = Color.parse("42b6ff")
    BeatTextColor = Color.parse("aaaaaa")

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

        self.head_box = PointerBox(
                self, align="left", y=0, abs_width=5, fill_color=self.HeadBoxColor)
        self.tail_box = PointerBox(
                self, align="right", y=self.height*(1-self.SpreadFraction),
                      abs_width=5, fill_color=self.TailBoxColor)
        self.update_size()

    def get_id(self):
        return self.id_num

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y
        self.audio_block.set_y(y)

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

    def get_tail_box(self, abs_at):
        if self.tail_box.is_abs_within(abs_at):
            return self.tail_box
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

    def draw_spread_box_path(self, ctx):
        ctx.rectangle(
                0, self.height*(1-self.SpreadFraction),
                self.width, self.height*self.SpreadFraction)

    SpreadMidColor = Color.parse("00FFFF")
    SpreadSelectedColor = Color.parse("ffff00")

    def draw(self, ctx, is_selected=False):
        if is_selected:
            spread_fill_color = self.SpreadSelectedColor
            desc_fill_color = self.SpreadSelectedColor
        else:
            spread_fill_color = self.SpreadMidColor
            desc_fill_color = self.DescFillColor

        ctx.save()
        self.pre_draw(ctx)
        self.draw_spread_box_path(ctx)
        draw_utils.draw_fill_rect_gradient(
            ctx,
            (self.width, self.height),
            ((0, self.SpreadBoxStartColor),
             (0.5, spread_fill_color),
             (1, self.SpreadBoxStartColor)))
        ctx.restore()

        ctx.save()
        self.pre_draw(ctx)
        self.draw_spread_box_path(ctx)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 2, self.BorderColor)

        self.head_box.draw(ctx)

        desc = self.audio_block.get_description()
        text_start_point = self.abs_reverse_transform_point(Point(0, 0))
        text_start_point.x += self.head_box.abs_width

        desc_rect = draw_utils.draw_text(ctx, desc,
                    text_start_point.x, text_start_point.y,
                    corner=2, padding=2,
                    font_name=self.FontName,
                    height=10, fit_height=True,
                    border_color = self.DescBorderColor,
                    back_color=desc_fill_color,
                    text_color=self.DescTextColor)

        if isinstance(self.audio_block, AudioSamplesBlock):
            draw_utils.draw_text(ctx, self.audio_block.music_note,
                    text_start_point.x,
                    text_start_point.y+15,
                    corner=2, padding=2,
                    font_name=self.FontName,
                    height=10, fit_height=True,
                    border_color = self.DescBorderColor,
                    back_color=self.DescFillColor,
                    text_color=self.DescTextColor)

        self.tail_box.draw(ctx)

    def show_current_position(self, ctx, rect):
        x = self.audio_block.current_pos*AudioBlockBox.PIXEL_PER_SAMPLE
        point = self.abs_reverse_transform_point(Point(x, 0))
        ctx.move_to(point.x, 0)
        ctx.line_to(point.x, rect.height)
        draw_utils.draw_stroke(ctx, 2, self.CurrentPosColor)

    def set_current_position(self, abs_point):
        rel_point = self.transform_point(abs_point)
        if rel_point.x<0:
            rel_point.x = 0
        self.audio_block.set_current_pos(rel_point.x/AudioBlockBox.PIXEL_PER_SAMPLE)

    def is_abs_within_current_pos(self, abs_point):
        x = self.audio_block.current_pos*AudioBlockBox.PIXEL_PER_SAMPLE
        playhead = self.abs_reverse_transform_point(Point(x, 0))
        spread = 2
        return playhead.x- spread<=abs_point.x<=playhead.x+spread

    def show_div_marks(self, ctx, beat, rect):
        start_point = self.transform_point(Point(rect.left, 0))
        end_point = self.transform_point(Point(rect.left+rect.width, 0))
        for x in beat.get_div_pixels(start_point.x, end_point.x, 50/self.scale_x):
            point = self.abs_reverse_transform_point(Point(x, 0))
            ctx.move_to(point.x, 0)
            ctx.line_to(point.x, rect.height)
        draw_utils.draw_stroke(ctx, 1, self.DivColor)

    def show_beat_marks(self, ctx, beat, rect):
        start_point = self.transform_point(Point(rect.left, 0))
        end_point = self.transform_point(Point(rect.left+rect.width, 0))
        for index, x in beat.get_beat_pixels(start_point.x, end_point.x, 50/self.scale_x):
            point = self.abs_reverse_transform_point(Point(x, 0))
            ctx.move_to(point.x, 0)
            ctx.line_to(point.x, rect.height)
            draw_utils.draw_stroke(ctx, 1, self.BeatColor)
            draw_utils.draw_text(
                ctx, "{0}".format(index+1), point.x+2, 0,
                font_name="8", text_color=self.BeatTextColor)

    def show_outer_border_line(self, ctx, rect):
        duration_width = self.audio_block.duration*AudioBlockBox.PIXEL_PER_SAMPLE
        end_point = self.reverse_transform_point(Point(duration_width, 0))
        if duration_width<rect.left or duration_width>rect.left+rect.width:
            return
        ctx.move_to(end_point.x, 0)
        ctx.line_to(end_point.x, rect.height)
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
