from .camera import Camera
import atexit
import cv2
import numpy as np
import threading
import traitlets


class CSICamera(Camera):
    
    # capture_device = traitlets.Integer(default_value=0)
    # capture_fps = traitlets.Integer(default_value=20)
    # capture_width = traitlets.Integer(default_value=500)
    # capture_height = traitlets.Integer(default_value=400)
    
    def __init__(self, *args, **kwargs):
        super(CSICamera, self).__init__(*args, **kwargs)
        try:
            self.cap = cv2.VideoCapture(self._gst_str(kwargs), cv2.CAP_GSTREAMER)

            re, image = self.cap.read()

            if not re:
                raise RuntimeError('Could not read image from camera.')
        except:
            raise RuntimeError(
                'Could not initialize camera.  Please see error trace.')

        atexit.register(self.cap.release)
                
    def _gst_str(self, kwargs):
        return 'nvarguscamerasrc sensor-id=%d ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=%d ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
                0, kwargs['capture_width'], kwargs['capture_height'], kwargs['capture_fps'], kwargs['flip_method'], kwargs['capture_width'], kwargs['capture_height'])
    
    def _read(self):
        re, image = self.cap.read()
        if re:
            return image
        else:
            raise RuntimeError('Could not read image from camera')
