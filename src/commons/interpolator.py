import numpy
from scipy import interpolate

class Interpolator(object):
    def __init__(self, points=None, kind='linear'):
        if points is None:
            points = []
        self.points = points
        self.kind = kind
        self.rebuild()

    def rebuild(self):
        arr = numpy.zeros((0, 2), dtype=numpy.float32)
        for point in self.points:
            arr = numpy.append(arr, [point.x, point.y])
        arr.shape= (-1, 2)
        indices = numpy.argsort(arr[:, 0])
        arr = arr[indices]
        self.evaluator = interpolate.interp1d(arr[:, 0], arr[:,1], kind=self.kind)

    def get_values(self, xs):
        return self.evaluator(xs)

    def add_point(self, point):
        self.points.append(point)
        self.rebuild()

    def remove_point_at_index(self, index):
        if self.kind == "cubic" and len(self.points)<=4:
            return False
        del self.points[index]
        self.rebuild()
        return True
