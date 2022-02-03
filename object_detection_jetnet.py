import jetson.inference
import jetson.utils
import cv2
from utilities.rectArea import RectArea
from utilities.vector import Vector
from object_captured import ObjectCaptured, ObjectName


class FrameCaptured(object):

    def __init__(self):
        self._objects = []

    def addObject(self, objCaptured):
        self._objects.append(objCaptured)

    def findExistingObject(self, existingObj, objectName=ObjectName.Person, exclusionNames={},
                           find_new_obj_if_needed=True):
        max_overlap_area = 0
        best_object = None

        for obj in self._objects:
            if objectName is not None and obj.name != objectName:
                continue
            if obj.name in exclusionNames or obj.isBigEnough() == False:
                continue
            area_rect = existingObj.boundingBox.intersect(obj.boundingBox)
            if area_rect is None:
                area = 0.0
            else:
                area = area_rect.area()

            if area > max_overlap_area:
                best_object = obj

        if best_object is not None:
            return best_object, best_object.getEstimatedDistance()

        # If we cannot find an overlapping object, just return the largest object
        if find_new_obj_if_needed:
            return self.findNewObject(objectName, exclusionNames)

        return None, None

    def findNewObject(self, objectName=ObjectName.Person, exclusionNames={}):
        # Find the largest object
        largest_area = 0
        largest_obj = None

        for obj in self._objects:
            if objectName is not None and obj.name != objectName:
                continue
            if obj.name in exclusionNames:
                continue

            if obj.isBigEnough():
                cur_area = obj.boundingBox.area()
                if cur_area > largest_area:
                    largest_obj = obj
                    largest_area = cur_area

        if largest_obj is not None:
            return largest_obj, obj.getEstimatedDistance()

        return None, None


class ObjectDetectionJetNet(object):
    # Supported coco labels
    class_labels = {1: ObjectName.Person,
                    18: ObjectName.Dog}

    def __init__(self, max_detected_object=None):
        self.max_detected_object = max_detected_object
        self._lastFrameCaptured = None

        self._setup_object_detection()

    def _setup_object_detection(self):
        model = "ssd-mobilenet-v2"
        threshold = 0.1

        param = []
        param.append("--log-level=error")
        self._net = jetson.inference.detectNet(model, argv=param, threshold=threshold)

    def _update(self, img):
        min_confidence = 0.1
        frame_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        width = img.shape[1]
        height = img.shape[0]
        cuda_img = jetson.utils.cudaFromNumpy(frame_rgba)

        detections = self._net.Detect(cuda_img, width, height)
        objList = []

        for i, obj in enumerate(detections):
            score = obj.Confidence
            if score < min_confidence:
                continue

            # Only care about some objects
            if obj.ClassID not in self.class_labels:
                continue

            label = self.class_labels[obj.ClassID]
            x1 = obj.Left
            y1 = obj.Top
            x2 = obj.Right
            y2 = obj.Bottom
            objList.append({"class": label, "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, "score": score})

        objList.sort(key=lambda x: x['score'], reverse=True)
        if self.max_detected_object is not None:
            objList = objList[:self.max_detected_object]

        self._lastFrameCaptured = FrameCaptured()

        for obj in objList:
            x1 = obj['box']['x1']
            y1 = obj['box']['y1']
            x2 = obj['box']['x2']
            y2 = obj['box']['y2']

            objName = obj['class']

            self._lastFrameCaptured.addObject(ObjectCaptured(objName,
                    RectArea(x1 / width,
                             y1 / height,
                             x2 / width,
                             y2 / height), obj['score']))

    def getLastFrameCaptured(self, image):
        self._update(image)
        return self._lastFrameCaptured

    def findExistingObject(self, existingObj, objectName):
        return self._lastFrameCaptured.findExistingObject(existingObj, objectName)

    def findNewObject(self, objectName):
        return self._lastFrameCaptured.findNewObject(objectName)


class ObjectDetectionFake(object):

    def __init__(self):
        self._lastFrameCaptured = None
        self._ctr = 0

    # Update should happen inside a separate thread
    # Need to make the code below thread safe
    def _update(self):
        # Get from video feed
        # image = self._readFromVideoFeed()
        # Call object detection model
        # frame = self._objDetect(image)
        # self._framesCaptured.append(frame)
        # if len(self._framesCaptured) > self._MAX_FRAME_CAPTURED:
        #    self._framesCaptured = self._framesCaptured[-self._MAX_FRAME_CAPTURED:]
        self._lastFrameCaptured = FrameCaptured()

        self._ctr += 1
        mod = self._ctr % 2500
        # return True

        if mod < 250:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.0, 0.1, 0.1), 0.9))
        elif mod < 500:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.9, 0.9, 1.0, 1.0), 0.9))
        elif mod < 750:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.9, 0.0, 1.0, 0.1), 0.9))
        # elif mod < 1000:
        #     self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
        elif mod < 1500:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
            self._lastFrameCaptured.addObject(ObjectCaptured("Horse", RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
        elif mod < 1900:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
            self._lastFrameCaptured.addObject(ObjectCaptured("Giraffe", RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
        else:
            # no object
            pass


    def getLastFrameCaptured(self):
        self._update()
        return self._lastFrameCaptured

    def findExistingObject(self, existingObj):
        return self._lastFrameCaptured.findExistingObject(existingObj)

    def findNewObject(self):
        return self._lastFrameCaptured.findNewObject()
