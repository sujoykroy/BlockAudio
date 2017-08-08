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

def draw_text(ctx, text,
              x, y, width=None, corner=5, align=None, fit_width=False, height=None, fit_height=False,
              text_color=None, back_color=None, border_color=None, border_width=1,
              padding=0, font_name=None, pre_draw=None):

    pangocairo_context = pangocairo.CairoContext(ctx)
    pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

    layout = pangocairo_context.create_layout()
    font = pango.FontDescription(font_name)
    layout.set_wrap(pango.WRAP_WORD)
    layout.set_font_description(font)
    layout.set_alignment(pango.ALIGN_LEFT)

    layout.set_markup(text)

    l, t, w, h = layout.get_pixel_extents()[1]
    scale_x = 1
    scale_y = 1
    if width:
        if width<w:
            if fit_width:
                scale_x = width/float(w)
        else:
            layout.set_width(int(width*pango.SCALE))
            w = width
    else:
        width = 0

    if height:
        if height<h:
            if fit_height:
                scale_y = height/float(h)
        else:
            h = height
    else:
        height = 0

    if align:
        if align.find("bottom-center")>=0:
            y -= t+h*scale_y+2*padding
        elif align.find("bottom")>=0:
            y -= -t+h*scale_x+padding
        if align.find("right")>=0:
            x -= w*scale_x+padding

    if back_color:
        ctx.save()
        if pre_draw: pre_draw(ctx)
        ctx.translate(x, y)
        ctx.scale(scale_x, scale_y)
        draw_rounded_rectangle(ctx, 0, 0, w+2*padding, h+2*padding, corner)
        ctx.restore()
        if isinstance(back_color, GradientColor):
            draw_fill(ctx, back_color.get_pattern_for(0, 0, w+2*padding, 0))
        else:
            draw_fill(ctx, back_color)

    if border_color:
        ctx.save()
        if pre_draw: pre_draw(ctx)
        ctx.translate(x, y)
        ctx.scale(scale_x, scale_y)
        draw_rounded_rectangle(ctx, 0, 0, w+2*padding, h+2*padding, corner)
        ctx.restore()
        if isinstance(border_color, GradientColor):
            draw_stroke(ctx, border_width, border_color.get_pattern(0, 0, w+2*padding, 0))
        else:
            draw_stroke(ctx, border_width, border_color)
    if not text_color:
        ctx.set_source_rgba(0,0,0,1)
    elif isinstance(text_color, Color):
        ctx.set_source_rgba(*text_color.get_array())
    elif isinstance(text_color, GradientColor):
        ctx.set_source(text_color.get_pattern_for(0, 0, w+2*padding, 0))
    elif type(text_color) is str:
        ctx.set_source_rgba(*Color.from_html(text_color).get_array())

    ctx.save()
    if pre_draw: pre_draw(ctx)
    ctx.translate(x, y)

    ctx.move_to(padding, padding)
    ctx.scale(scale_x, scale_y)
    pangocairo_context.update_layout(layout)
    pangocairo_context.show_layout(layout)

    ctx.restore()

    return (x, y, w+2*padding, h+2*padding)
