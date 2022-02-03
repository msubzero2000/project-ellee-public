import os

from utilities.stopwatch import Stopwatch


class FpsCalc(object):
    _MAX_HISTORY = 5

    def __init__(self):
        self._history = []
        self._stopWatch = Stopwatch()

    def log(self):
        self._history.append(self._stopWatch.get())
        if len(self._history) > self._MAX_HISTORY:
            self._history = self._history[-self._MAX_HISTORY:]

        startTime = self._history[0]
        stopTime = self._history[-1]
        if startTime == stopTime:
            fps = 1.0
        else:
            fps = (1000 * len(self._history)) / (stopTime - startTime)

        return fps
