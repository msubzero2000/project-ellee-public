import os


class FaceObject(object):

    def __init__(self, name, bounding_box, score, face_image=None):
        self.name = name
        self.bounding_box = bounding_box
        self.score = score
        self.face_image = face_image
