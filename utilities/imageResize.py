import os

from PIL import Image

class ImageResizeMode(object):
    STRETCH_TO_FIT = "stretchToFit" # Ignore aspect ratio, just stretch to the target dimension
    RESIZE_TO_FIT = "resizeToFit"   # Keeping aspect ratio, resize as big as possible but no part of image outside the target dimension
    RESIZE_TO_FILL = "resizeToFill" # Keeping aspect ratio, resize as small as possible but making sure target dimension area has been completely filled


class ImageResize(object):

    @classmethod
    def resizeImageDimension(cls, imgWidth: int, imgHeight: int, targetWidth: int, targetHeight: int,
                             resizeMode: ImageResizeMode, canResizeUp: bool=True):
        if resizeMode == ImageResizeMode.STRETCH_TO_FIT:
            newWidth = targetWidth
            newHeight = targetHeight

            if not canResizeUp:
                if newWidth > imgWidth:
                    newWidth = imgWidth
                if newHeight > imgHeight:
                    newHeight =imgHeight

            return newWidth, newHeight
        else:
            sx = imgWidth / targetWidth
            sy = imgHeight / targetHeight

            if resizeMode == ImageResizeMode.RESIZE_TO_FIT:
                s = sx if sx > sy else sy
            else:
                s = sx if sx < sy else sy

            if not canResizeUp and s < 1.0:
                s = 1.0

            newWidth = int(imgWidth / s)
            newHeight = int(imgHeight / s)

            return newWidth, newHeight

    @classmethod
    def resizeImage(cls, image: Image, targetWidth: int, targetHeight: int,
                    resizeMode: ImageResizeMode, canResizeUp: bool=True, addPadding: bool = False):
        newWidth, newHeight = ImageResize.resizeImageDimension(image.size[0], image.size[1], targetWidth, targetHeight,
                                                               resizeMode, canResizeUp)

        newImage = image.resize((int(newWidth), int(newHeight)))

        if addPadding and resizeMode == ImageResizeMode.RESIZE_TO_FIT and (newWidth != targetWidth or newHeight != targetHeight):
            extraWidth = targetWidth - newWidth
            extraHeight = targetHeight - newHeight

            paddedImage = Image.new('RGB', (targetWidth, targetHeight), (0, 0, 0))
            paddedImage.paste(newImage, (int(extraWidth / 2), int(extraHeight / 2)))

            return paddedImage

        return newImage


