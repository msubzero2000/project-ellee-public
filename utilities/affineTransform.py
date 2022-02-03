import copy
import math
from affine import Affine
from utilities.vector import Vector

class AffineTransform(object):

    def __init__(self, affine=Affine.identity()):
        self._affine = affine

    def rotate(self, angle):
        self._affine *= Affine.rotation(angle)

    def translate(self, offset):
        self._affine *= Affine.translation(offset.x, offset.y)

    def scale(self, scale):
        self._affine *= Affine.scale(scale)

    def transform(self, point):
        result = self._affine * (point.x, point.y)
        return Vector(result[0], result[1])

    def copy(self):
        return AffineTransform(copy.deepcopy(self._affine))

    def getTranslation(self):
        return Vector(self._affine[2], self._affine[5])

    def getRotation(self):
        angle = math.atan2(self._affine[3], self._affine[0]) * 180.0 / math.pi

        return angle
