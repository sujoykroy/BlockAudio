class Rect(object):
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def __repr__(self):
        return "Rect(l={0}, t={1}, w={2}, h={3})".format(self.left, self.top, self.width, self.height)
