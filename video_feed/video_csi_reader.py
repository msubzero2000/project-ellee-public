from .video_reader import VideoReader
from jetcam.csi_camera import CSICamera
from PIL import Image
import time
import numpy as np
import cv2

class VideoCSIReader(VideoReader):
    
    def __init__(self, capture_width=400, capture_height=300, capture_fps=30,
                 flip_method=0):
        self._camera = CSICamera(capture_width=capture_width, capture_height=capture_height,
                                 capture_fps=capture_fps, flip_method=flip_method)
            
    def read_frame(self,  show_preview=False):
        img = self._camera.read()
        
        if img is None:
            return None
            
        if show_preview:
            cv2.imshow("preview", img)
            cv2.waitKey(1)
        
        return img
        
