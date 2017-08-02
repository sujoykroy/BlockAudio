import math, cairo
from xml.etree.ElementTree import Element as XmlElement

RAD_PER_DEG = math.pi/180.

class Point(object):
    TAG_NAME = "point"

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "Point(x={0}, y={1})".format(self.x, self.y)

    def get_xml_element(self):
        elm = XmlElement(self.TAG_NAME)
        elm.attrib["p"] = self.to_text()
        return elm

    @staticmethod
    def create_from_xml_element(elm):
        return Point.from_text(elm.attrib.get("p", "0,0"))

    def translate(self, x, y):
        self.x += x
        self.y += y

    def rotate_coordinate(self, angle):
        angle *= RAD_PER_DEG
        x = self.x*math.cos(angle)+self.y*math.sin(angle)
        y = -self.x*math.sin(angle)+self.y*math.cos(angle)
        self.x = x
        self.y = y

    def rotate_around_origin(self, angle):
        angle *= RAD_PER_DEG
        a = math.atan2(self.y, self.x)
        d = math.sqrt(self.x*self.x+self.y*self.y)
        self.x = d*math.cos(a+angle)
        self.y = d*math.sin(a+angle)

    def diff(self, other):
        return Point(self.x-other.x, self.y-other.y)

    def copy(self):
        return Point(self.x, self.y)

    def get_angle(self):
        return math.atan2(self.y, self.x)/RAD_PER_DEG

    def assign(self, x, y):
        self.x = x
        self.y = y

    def scale(self, sx, sy):
        self.x *= sx
        self.y *= sy

    def copy_from(self, other):
        self.x = other.x
        self.y = other.y

    def distance(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx+dy*dy)

    def to_text(self):
        return "{0},{1}".format(self.x, self.y)

    def set_inbetween(self, point1, point2, ratio):
        self.x = point1.x + (point2.x-point1.x)*ratio
        self.y = point1.y + (point2.y-point1.y)*ratio

    def transform(self, matrix):
        self.x, self.y = matrix.transform_point(self.x, self.y)

    def reverse_transform(self, matrix):
        matrix = cairo.Matrix()*matrix
        matrix.invert()
        self.x, self.y = matrix.transform_point(self.x, self.y)

    def to_array(self):
        return [self.x, self.y]

    @classmethod
    def from_text(cls, text):
        try:
            x, y = text.split(",")
            point = cls(float(x), float(y))
        except:
            return None
        return point

