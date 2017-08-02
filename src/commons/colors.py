import numpy

class Color(object):
    def __init__(self, red, green, blue, alpha):
        self.values = numpy.array([red, green, blue, alpha]).astype("f" )

    def copy(self):
        return Color(*list(self.values))

    def get_array(self):
        return list(self.values)

    def copy_from(self, color):
        if not isinstance(color, Color): return
        self.values = color.values.copy()

    def to_text(self):
        return "{0},{1},{2},{3}".format(*list(self.values))

    def to_html(self):
        arr = list(self.values)
        for i in range(len(arr)):
            arr[i] = hex(int(arr[i]*255))[2:]
            if len(arr[i]) == 1:
                arr[i] = "0" + arr[i]
        return "#" + "".join(arr)

    def set_inbetween(self, start_color, end_color, frac):
        if not isinstance(start_color, Color) or not isinstance(end_color, Color):
            return
        self.values = start_color.values + (end_color.values-start_color.values)*frac

    @classmethod
    def from_text(cls, text):
        if text is None or text == "None": return None
        r, g, b, a = text.split(",")
        return cls(float(r), float(g), float(b), float(a))

    @classmethod
    def from_html(cls, html):
        arr = []
        for i in range(0, len(html), 2):
            arr.append(int(html[i:i+2], 16)/255.)
        if len(arr)<4:
            arr.append(1.)
        return Color(*arr)

    @classmethod
    def parse(cls, color):
        if isinstance(color, Color):
            return color
        elif isinstance(color, str):
            return Color.from_html(color)
        else:
            return color
