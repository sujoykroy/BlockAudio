from colors import Color
import pango, pangocairo, cairo, math

def set_default_line_style(ctx):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

def set_ctx_color(ctx, color):
    if isinstance(color, tuple):
        ctx.set_source_rgba(*color)
    elif isinstance(color, Color):
        ctx.set_source_rgba(*color.get_array())
    elif isinstance(color, str):
        ctx.set_source_rgba(*Color.from_html(color).get_array())
    else:
        ctx.set_source(color)

def draw_stroke(ctx, line_width, color=Color(0,0,0,1)):
    ctx.save()
    if isinstance(color, Color):
        ctx.set_source_rgba(*color.get_array())
    elif isinstance(color, str):
        ctx.set_source_rgba(*Color.from_html(color).get_array())
    else:
        ctx.set_source(color)
    ctx.set_line_width(line_width)
    ctx.stroke()
    ctx.restore()

def draw_fill(ctx, color=Color(1, 1, 1,1)):
    ctx.save()
    if isinstance(color, Color):
        ctx.set_source_rgba(*color.get_array())
    elif isinstance(color, str):
        ctx.set_source_rgba(*Color.from_html(color).get_array())
    elif isinstance(color, cairo.Pattern):
        ctx.set_source(color)
    ctx.fill()
    ctx.restore()
