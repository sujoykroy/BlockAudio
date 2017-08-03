from ..commons import draw_utils, Color, Point

class ExpanderBox(object):
    BorderColor = Color.parse("000000")
    FillColor = Color.parse("f926a2")

    def __init__(self, parent_box):
        self.parent_box = parent_box
        self.width=10000

    def get_position(self):
        return Point(self.parent_box.width-self.width, 0)

    def pre_draw(self, ctx):
        self.parent_box.pre_draw(ctx)
        ctx.translate(self.parent_box.width-self.width, 0)

    def draw_path(self, ctx):
        ctx.rectangle(0, 0, self.width, self.parent_box.height)

    def draw(self, ctx):
        ctx.new_path()
        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_fill(ctx, self.FillColor)

        ctx.new_path()
        ctx.save()
        self.pre_draw(ctx)
        self.draw_path(ctx)
        ctx.restore()
        draw_utils.draw_stroke(ctx, 1, self.BorderColor)

    def is_within(self, point):
        if point.x<self.parent_box.x+self.parent_box.width-self.width:
            return False
        if point.x>self.parent_box.x+self.parent_box.width:
            return False
        if point.y<self.parent_box.y:
            return False
        if point.y>self.parent_box.y+self.parent_box.height:
            return False
        return True

