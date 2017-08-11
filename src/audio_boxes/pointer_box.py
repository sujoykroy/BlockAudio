from ..commons import draw_utils, Color, Point

class PointerBox(object):
    BorderColor = Color.parse("000000")

    def __init__(self, parent_box, align, y, abs_width, fill_color):
        self.parent_box = parent_box
        self.align = align
        self.y = y
        self.abs_width = abs_width
        self.fill_color = fill_color

    def get_position(self):
        if self.align == "right":
            return Point(self.parent_box.width, self.y)
        return Point(0, self.y)

    def pre_draw1(self, ctx):
        self.parent_box.pre_draw(ctx)
        ctx.translate(self.parent_box.width-self.width, 0)

    def draw_path(self, ctx):
        if self.align == "right":
            top_point = self.parent_box.abs_reverse_transform_point(
                            Point(self.parent_box.width, self.y))
            bottom_point = self.parent_box.abs_reverse_transform_point(
                            Point(self.parent_box.width, self.parent_box.height))
            ctx.rectangle(
                top_point.x-self.abs_width, top_point.y,
                self.abs_width, bottom_point.y-top_point.y)
        else:
            top_point = self.parent_box.abs_reverse_transform_point(
                            Point(0, self.y))
            bottom_point = self.parent_box.abs_reverse_transform_point(
                            Point(0, self.parent_box.height))
            ctx.rectangle(
                top_point.x, top_point.y,
                self.abs_width, bottom_point.y-top_point.y)

    def draw(self, ctx):
        self.draw_path(ctx)
        draw_utils.draw_fill(ctx, self.fill_color)

        self.draw_path(ctx)
        draw_utils.draw_stroke(ctx, 1, self.BorderColor)

    def is_abs_within(self, point):
        if self.align == "left":
            left_top = Point(0, self.y)
            left_top = self.parent_box.abs_reverse_transform_point(left_top)

            bottom_top = Point(0, self.parent_box.height)
            bottom_top = self.parent_box.abs_reverse_transform_point(bottom_top)

            right_bottom = bottom_top.copy()
            right_bottom.x = left_top.x + self.abs_width
        else:
            right_top = Point(self.parent_box.width, self.y)
            right_top = self.parent_box.abs_reverse_transform_point(right_top)

            right_bottom = Point(self.parent_box.width, self.parent_box.height)
            right_bottom = self.parent_box.abs_reverse_transform_point(right_bottom)

            left_top = right_top.copy()
            left_top.x = right_top.x - self.abs_width

        rel_point = self.parent_box.abs_reverse_transform_point(point)
        if point.x<left_top.x or point.x>right_bottom.x:
            return False
        if point.y<left_top.y or point.y>right_bottom.y:
            return False
        return True

