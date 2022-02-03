class ObjectName(object):
    Person = "person"
    Dog = "dog"


class ObjectCaptured(object):
    _MIN_PERSON_LENGTH = 3 / 100   # 3% of screen width
    _MIN_OBJ_LENGTH = 2 / 100 # 2% of screen width

    def __init__(self, name, boundingBox, confScore):
        self.name = name
        self.boundingBox = boundingBox
        self.confScore = confScore

    def getEstimatedDistance(self):
        # Distance is the inverse of bounding box length
        return 1.0 / self.boundingBox.length()

    def getEyeCenter(self):
        return Vector(self.boundingBox.center()[0], self.boundingBox.y1 + self.boundingBox.height() * 0.1)

    def isBigEnough(self):
        if self.name == ObjectName.Person and self.boundingBox.length() >= self._MIN_PERSON_LENGTH:
            return True

        if self.boundingBox.length() >= self._MIN_OBJ_LENGTH:
            return True

        return False
