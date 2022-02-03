import os
import numpy as np
import cv2
import time

from object_detection_jetnet import ObjectDetectionJetNet, ObjectName, ObjectCaptured
from face_detection import FaceDetection, FaceObject
from video_feed.video_csi_reader import VideoCSIReader
from PIL import ImageDraw, ImageFont, Image
from utilities.rectArea import RectArea
from utilities.fpsCalc import FpsCalc
from person import Person
from const import Const


class SightObjectDetection(object):
    CaptureWidth = Const.CaptureWidth
    CaptureHeight = Const.CaptureHeight

    DisplayWidth = 400
    DisplayHeight = 300

    # The offset of face relative to detected body rectangle
    FaceLeftOffset = 0.4
    FaceRightOffset = 0.6
    FaceTopOffset = 0.1
    FaceBottomOffset = 0.15

    def __init__(self):
        self._fps_calc = FpsCalc()
        self._font = ImageFont.truetype("resources/Arial.ttf", 30)
        self._small_font = ImageFont.truetype("resources/Arial.ttf", 15)

        self._video_source = VideoCSIReader(capture_width=self.CaptureWidth, capture_height=self.CaptureHeight,
                                           capture_fps=Const.CaptureFPS, flip_method=2)

        self._od = ObjectDetectionJetNet()
        self._fd = FaceDetection()
        self._focus_person = None
        self._focus_person_face_rect = None
        self._focus_face = None
        self._detected_faces = []

        self._display_preview = True
        self._object_detection_freq = 2
        self._face_detection_freq = 10

        if self._display_preview:
            self._windowHandle = cv2.namedWindow("Camera", cv2.WINDOW_AUTOSIZE)

        self._ctr = 0

    def _find_person(self, image):
        last_frame = self._od.getLastFrameCaptured(image)

        if last_frame is None:
            return None, None

        # Find a focus person
        if self._focus_person is not None:
            person, distance = self._od.findExistingObject(self._focus_person, objectName=ObjectName.Person)
        else:
            person, distance = self._od.findNewObject(objectName=ObjectName.Person)

        face_rect = None
        if person is not None:
            # Generate face bounding box from person bounding box
            face_x1 = person.boundingBox.x1 + person.boundingBox.length() * self.FaceLeftOffset
            face_x2 = person.boundingBox.x1 + person.boundingBox.length() * self.FaceRightOffset
            face_y1 = person.boundingBox.y1 + person.boundingBox.height() * self.FaceTopOffset
            face_y2 = person.boundingBox.y1 + person.boundingBox.height() * self.FaceBottomOffset

            face_rect = RectArea(face_x1 * self.CaptureWidth,
                          face_y1 * self.CaptureHeight,
                          face_x2 * self.CaptureWidth,
                          face_y2 * self.CaptureHeight)

        return person, face_rect

    def _draw_person(self, person, face_rect, draw):
        if person is not None:
            if self._display_preview:
                # Draw person bounding box
                p_box = person.boundingBox.normalisedTo(self.DisplayWidth, self.DisplayHeight).round()

                draw.rectangle((p_box.x1, p_box.y1, p_box.x2, p_box.y2),
                               fill=None, outline=(255, 0, 0), width=4)

            if self._display_preview:
                f_box = face_rect.normalisedTo(self.DisplayWidth, self.DisplayHeight).round()

                # Draw face bounding box
                draw.rectangle((f_box.x1, f_box.y1, f_box.x2, f_box.y2),
                               fill=None, outline=(100, 100, 100), width=4)

    def _find_face(self, image):
        detected_faces = self._fd.detect(image)

        return detected_faces

    def _draw_face(self, detected_faces, focus_face, draw):
        if not self._display_preview:
            return

        for face in detected_faces:
            f_box = face.bounding_box.normalisedFrom(
                self.CaptureWidth, self.CaptureHeight).normalisedTo(
                self.DisplayWidth, self.DisplayHeight).round()

            # Draw face bounding box
            if focus_face == face:
                draw.rectangle((f_box.x1, f_box.y1, f_box.x2, f_box.y2),
                               fill=None, outline=(0, 255, 0), width=4)
            else:
                draw.rectangle((f_box.x1, f_box.y1, f_box.x2, f_box.y2),
                               fill=None, outline=(150, 150, 0), width=2)

            # Draw face name
            name = face.name
            if name is None:
                name = "None"

            draw.text((f_box.x1, f_box.y1), f"{name}", stroke_fill=(0, 255, 0), font=self._small_font)

    def _find_largest_face(self, detected_faces):
        # Find the face with the maximum overlap to focus_person
        largest_face_area = 0
        largest_face = None

        for face in detected_faces:
            face_area = face.bounding_box.area()

            if face_area > largest_face_area:
                largest_face_area = face_area
                largest_face = face

        return largest_face

    def _find_focus_face(self, detected_faces, focus_person):
        max_overlap_area = 0
        best_face = None

        if focus_person is None:
            return self._find_largest_face(detected_faces)

        for face in detected_faces:
            cur_overlap_rect = face.bounding_box.intersect(focus_person.boundingBox.normalisedTo(
                self.CaptureWidth, self.CaptureHeight
            ))

            if cur_overlap_rect is not None:
                cur_overlap_area = cur_overlap_rect.area()

                if cur_overlap_area > max_overlap_area:
                    max_overlap_area = cur_overlap_area
                    best_face = face

        # If no face overlaps the focus person body, focus on the largest face
        if best_face is None:
            best_face = self._find_largest_face(detected_faces)

        return best_face

    def detect(self):
        image = self._video_source.read_frame()

        draw = None
        updated_od = False
        updated_fd = False
        if self._display_preview:
            orig_image = Image.fromarray(image)
            annot_image = orig_image.resize((self.DisplayWidth, self.DisplayHeight))
            draw = ImageDraw.Draw(annot_image)

        if self._ctr % self._object_detection_freq == 0:
            # Update focus person at specified fequency
            self._focus_person, self._focus_person_face_rect = self._find_person(image)
            updated_od = True


        self._draw_person(self._focus_person, self._focus_person_face_rect, draw)

        # Perform a face detection/recognition at required frequency
        if self._ctr % self._face_detection_freq == 0:
            updated_fd = True
            self._detected_faces = self._find_face(image)

            # Find the face which belongs to the self._focus_person
            self._focus_face = self._find_focus_face(self._detected_faces, self._focus_person)

        self._draw_face(self._detected_faces, self._focus_face, draw)

        fps = self._fps_calc.log()
        print(f"FPS {fps}")

        if self._display_preview:
            draw.text((5, 5), f"FPS {fps:.1f}", stroke_fill=(255, 255, 0), font=self._font)

            np_image = np.array(annot_image)
            cv2.imshow("Camera", np_image)
            cv2.waitKey(30)

        self._ctr += 1

        # Either a person body or a face must be detected to return a person object
        found_person = None
        if self._focus_person is not None or self._focus_face is not None:
            found_person = Person(self._focus_person, self._focus_person_face_rect, self._focus_face)

        return found_person, updated_od, updated_fd

    def register_new_face(self, face_obj):
        self._fd.register_new_face(face_obj)