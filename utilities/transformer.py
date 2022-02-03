import os
import math
from affine import Affine

from utilities.vector import Vector


class Transformer(object):

    def __init__(self, offset=Vector(0, 0), scale=1.0, angle=0.0):
        self._pos = offset
        self._scale = scale
        self._angle = angle
        self._affine = Affine.identity()

    def apply(self, offset, scale):
        self._affine = self._affine.translation(offset.x, offset.y)
        offset = offset.scale(self._scale)

        self._pos = self._pos.add(offset)
        self._scale = scale

        return self._pos, self._scale, self._angle

    def copy(self):
        return Transformer(self._pos, self._scale, self._angle)

    def offset(self, offset):
        self._pos = self._pos.add(offset)

    def transform(self, offset, angle):
        self._pos = self._pos.add(offset)
        if angle is not None:
            self._angle += angle