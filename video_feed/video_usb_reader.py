from .video_reader import VideoReader
from jetcam.usb_camera import USBCamera
from PIL import Image
import time
import numpy as np

class VideoUSBReader(VideoReader):

    def __init__(self):
        self._camera = USBCamera(width=224, height=224, capture_width=640, capture_height=480, capture_fps=30, capture_device=0)

    def read_frame(self,  show_preview=False):
        img = self._camera.read()

        if img is None:
            return None

        if show_preview:
            cv2.imshow("preview", img)
            cv2.waitKey(1)

        return img
