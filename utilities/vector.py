import os
import math

class Vector(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def abs(self):
        return Vector(abs(self.x), abs(self.y))

    def length(self):
        return math.sqrt(pow(self.x, 2) + pow(self.y, 2))

    def normalise(self):
        length = self.length()
        return Vector(self.x / length, self.y / length)

    def rotateClockwise(self):
        return Vector(self.y, -self.x)

    def rotateAntiClockwise(self):
        return Vector(-self.y, self.x)

    def multiply(self, vector):
        return Vector(self.x * vector.x, self.y * vector.y)

    def scale(self, length):
        return Vector(self.x * length, self.y * length)

    def subtract(self, vec):
        return Vector(self.x - vec.x, self.y - vec.y)

    def add(self, vec):
        return Vector(self.x + vec.x, self.y + vec.y)

    def rotate(self, angle):
        anglePi = angle * math.pi / 180.0
        return Vector(self.x * math.cos(anglePi) - self.y * math.sin(anglePi),
                      self.x * math.sin(anglePi) + self.y * math.cos(anglePi))
