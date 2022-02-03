import os

from const import Const

class Person(object):

    def __init__(self, person_obj, person_face_rect, face_obj):
        self.person_name = None
        self.face_bbox = None
        self.person_bbox = None
        self.face_image = None

        self.is_face_detected = face_obj is not None

        if person_obj is not None:
            # Use the person face rect calculated from the body as we do not have a detected face
            self.face_bbox = person_face_rect
            self.person_bbox = person_obj.boundingBox.normalisedTo(
                Const.CaptureWidth, Const.CaptureHeight
            )

        if face_obj is not None:
            self.person_name = face_obj.name
            self.face_image = face_obj.face_image

            # We use the face constructed from the body bounding box instead of using the real face
            # as the real face is detected with a much lower frequency, hence causes the head movement
            # to overshoot by significant margin and make the head to oscilate around the target angle
            # We only use the face bounding box if there is no body founding box detected
            if self.face_bbox is None:
                self.face_bbox = face_obj.bounding_box

            # If we do not have person bounding box, use the detected as as the bounding box
            if self.person_bbox is None:
                self.person_bbox = self.face_bbox
