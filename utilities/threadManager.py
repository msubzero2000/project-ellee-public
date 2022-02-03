import threading
from queue import Queue

class ThreadManager(object):

    @classmethod
    def execute(self, callback, inputList, numThreads, data):
        threads = []
        inputQueue = Queue()
        resultList = []

        for input in inputList:
            inputQueue.put(input)

        for i in range(numThreads):
            inputQueue.put(None)

        for i in range(numThreads):
            t = threading.Thread(target=callback, args=(inputQueue, resultList, data))
            t.daemon = False
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

        return resultList