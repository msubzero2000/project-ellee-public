from .video_reader import VideoReader
import cv2
from PIL import Image
import time
import numpy as np

class VideoOfflineReader(VideoReader):
    
    def __init__(self, file_path):
        self._cap = cv2.VideoCapture(file_path)
            
    def read_frame(self,  show_preview=False):
        ret_val, img = self._cap.read()
        if not ret_val:
            return None
        if show_preview:
            cv2.imshow("preview", img)
            cv2.waitKey(1)
        
        return img
        
