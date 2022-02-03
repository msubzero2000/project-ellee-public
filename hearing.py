from speech_recognition import SpeechInputRecognitionStreaming
import threading


class Hearing(object):

    def __init__(self):
        self._last_speech_message = None
        self._sr = SpeechInputRecognitionStreaming()
        self._thread = threading.Thread(target=self._callback, args=(1,))
        self._thread.daemon = False
        self._thread.start()

    def __del__(self):
        self._run_thread = False
        self._thread.join()

    def start_listening(self):
        # Reset the last speech message and start listening
        if not self._sr.is_listening():
            self._last_speech_message = None
            self._sr.set_listening(True)

    def stop_listening(self):
        self._sr.set_listening(False)

    def get_last_speech_message(self):
        return self._last_speech_message

    def _speech_callback(self, message, lang_code):
        self._last_speech_message = message

        return False
        # print(self._last_speech_message)

    def _callback(self, data):
        self._sr.listen_forever(self._speech_callback)

    def is_ready(self):
        return self._sr.ready
