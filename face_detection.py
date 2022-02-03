import face_recognition
import os
import cv2
import numpy as np
from utilities.fileSearch import FileSearch
from utilities.rectArea import RectArea
from face_object import FaceObject


class FaceDetection(object):
    FACE_FOLDER = "resources/faces"

    def __init__(self):
        face_files = FileSearch.collectFilesEndsWithName(".jpg", os.path.join(os.getcwd(), self.FACE_FOLDER))
        self.face_encoding_db = []
        self.face_labels = []

        for face in face_files:
            img = face_recognition.load_image_file(face)
            name = face.split("/")[-1].replace(".jpg", "")
            self.face_labels.append(name)
            self.face_encoding_db.append(face_recognition.face_encodings(img)[0])

    def detect(self, image):
        # Flip color channel
        res_img = image[:, :, ::-1]
        face_locations = face_recognition.face_locations(res_img)
        found_faces = []

        if len(face_locations) > 0:
            found_faces_encoding = face_recognition.face_encodings(res_img, face_locations)

            for i, cur_face in enumerate(found_faces_encoding):
                matches = face_recognition.compare_faces(self.face_encoding_db, cur_face)
                face_distances = face_recognition.face_distance(self.face_encoding_db, cur_face)
                cur_best_face_distance_idx = np.argmin(face_distances)

                found_face_name = None

                if matches[cur_best_face_distance_idx]:
                    found_face_name = self.face_labels[cur_best_face_distance_idx]

                top, left, bottom, right = face_locations[i]
                face_bbox = RectArea(left, top, right, bottom)
                found_faces.append(FaceObject(found_face_name, face_bbox, face_distances[cur_best_face_distance_idx], res_img))

        return found_faces

    def register_new_face(self, face_object):
        save_path = os.path.join(os.getcwd(), f"{self.FACE_FOLDER}/{face_obj.name}.jpg")
        face_object.face_image.save(save_path)
