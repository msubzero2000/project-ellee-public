import abc


class VideoReader(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def read_frame(self):
        """ required method """
