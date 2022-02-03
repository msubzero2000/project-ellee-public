import os
import math

from .vector import Vector


class RectArea(object):

    @staticmethod
    def fromPoints(points):
        x1 = None
        y1 = None
        x2 = None
        y2 = None

        for x, y in points:
            if x1 is None or x1 > x:
                x1 = x
            if y1 is None or y1 > y:
                y1 = y
            if x2 is None or x2 < x:
                x2 = x
            if y2 is None or y2 < y:
                y2 = y

        return RectArea(x1, y1, x2, y2)

    def __init__(self, x1, y1, x2, y2):
        if x1 < x2:
            self.x1 = x1
            self.x2 = x2
        else:
            self.x1 = x2
            self.x2 = x1

        if y1 < y2:
            self.y1 = y1
            self.y2 = y2
        else:
            self.y1 = y2
            self.y2 = y1

    def union(self, anotherRectArea):
        newRectArea = RectArea(min(self.x1, anotherRectArea.x1), min(self.y1, anotherRectArea.y1),
                               max(self.x2, anotherRectArea.x2), max(self.y2, anotherRectArea.y2))

        return newRectArea

    def intersect(self, anotherRectArea):
        if self.isOverlap(anotherRectArea):
            return RectArea(max(self.x1, anotherRectArea.x1), max(self.y1, anotherRectArea.y1),
                     min(self.x2, anotherRectArea.x2), min(self.y2, anotherRectArea.y2))

        return None

    def area(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def isOverlap(self, anotherRectArea):
        if (anotherRectArea.x1 <= self.x2 and anotherRectArea.y1 <= self.y2 and
            anotherRectArea.x2 >= self.x1 and anotherRectArea.y2 >= self.y1):
            return True

        return False

    def isPointInside(self, x, y):
        return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2

    def isInside(self, anotherRectArea):
        return anotherRectArea.isPointInside(self.x1, self.y1) and anotherRectArea.isPointInside(self.x2, self.y2)

    def aspectRatio(self):
        return abs(self.y2 - self.y1) / abs(self.x2 - self.x1)

    def center(self):
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def length(self):
        return self.x2 - self.x1

    def scale(self, scale):
        return RectArea(self.x1 * scale, self.y1 * scale, self.x2 * scale, self.y2 * scale)

    # Normalise the coordinate system to 0-1 based on the supplied stageWidth, stageHeight
    def normalisedFrom(self, stageWidth, stageHeight):
        return RectArea(self.x1 / stageWidth, self.y1 / stageHeight, self.x2 / stageWidth, self.y2 / stageHeight)

    # Normalise the coordinate system back from 0-1 to stageWidth, stageHeight
    def normalisedTo(self, stageWidth, stageHeight):
        return RectArea(self.x1 * stageWidth, self.y1 * stageHeight, self.x2 * stageWidth, self.y2 * stageHeight)

    def round(self):
        return RectArea(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def width(self):
        return abs(self.x2 - self.x1)

    def height(self):
        return abs(self.y2 - self.y1)

    # Return a grown box by scale (keeping the center of the box the same)
    def grow(self, scale):
        centerX, centerY = self.center()
        newWidth = self.width() * scale
        newHeight = self.height() * scale

        return RectArea(centerX - newWidth / 2, centerY - newHeight / 2, centerX + newWidth / 2, centerY + newHeight / 2)

    def offset(self, vector: Vector):
        return RectArea(self.x1 + vector.x, self.y1 + vector.y, self.x2 + vector.x, self.y2 + vector.y)

    def distanceFromRect(self, anotherRectArea):
        ourCenterX, ourCenterY = self.center()

        anotherCenterX, anotherCenterY = anotherRectArea.center()

        return math.sqrt(pow(ourCenterX - anotherCenterX, 2) + pow(ourCenterY - anotherCenterY, 2))

    def toJson(self):

        return {'x1': self.x1,
                'y1': self.y1,
                'x2': self.x2,
                'y2': self.y2}

    def overlapArea(self, anotherRectArea):
        if self.isOverlap(anotherRectArea) is False:
            return 0, 0

        xmin = max(self.x1, anotherRectArea.x1)
        xmax = min(self.x2, anotherRectArea.x2)
        ymin = max(self.y1, anotherRectArea.y1)
        ymax = min(self.y2, anotherRectArea.y2)

        area = RectArea(xmin, ymin, xmax, ymax).area()
        return area, (area/anotherRectArea.area())
