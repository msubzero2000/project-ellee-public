
import threading
import time

from playsound import playsound
from utilities.stopwatch import Stopwatch


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class Audio(object):

    _AFTER_PLAYING_DURATION = 1
  
    def __init__(self):
        self._thread = None
        self._timeSinceStopPlaying = None

    def _play(self, name):
        playsound(name)

    def play(self, name):
        if self._thread is not None and not self._thread.isAlive():
            self._thread.stop()

        self._thread = None

        self._thread = StoppableThread(target=self._play, args=(name,))
        self._thread.start()
        self._timeSinceStopPlaying = None

    def isPlaying(self):
        ret = self._thread is not None and self._thread.isAlive()

        if not ret and self._thread is not None and self._timeSinceStopPlaying is None:
            self._timeSinceStopPlaying = Stopwatch()

        return ret

    def isAfterPlaying(self):
        if self._thread is None:
            return False

        if not self._thread.isAlive():
            if self._timeSinceStopPlaying is None:
                self._timeSinceStopPlaying = Stopwatch()
                return True
            else:
                return self._timeSinceStopPlaying.get() / 1000 < self._AFTER_PLAYING_DURATION

        return False
