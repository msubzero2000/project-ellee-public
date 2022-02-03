import re
import sys
import os

from google.cloud import speech as speech
import pyaudio
from six.moves import queue

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Path to your google cloud json auth file"

# Audio recording parameters
RATE = 44100
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStreamInputSource(object):

    Microphone = "Microphone"
    Loopback = "Loopback"
    SoundFlower = "Soundflower (2ch)"


class MicrophoneStreamSettings(object):

    def __init__(self, numChannels, rate):
        self.numChannels = numChannels
        self.rate = rate


class MicrophoneStream(object):
    _soundSettings = {
        MicrophoneStreamInputSource.Microphone: MicrophoneStreamSettings(numChannels=1, rate=44100),
        MicrophoneStreamInputSource.Loopback: MicrophoneStreamSettings(numChannels=1, rate=16000),
        MicrophoneStreamInputSource.SoundFlower: MicrophoneStreamSettings(numChannels=1, rate=16000)
    }
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk, soundInputSource):
        self._chunk = chunk
        self._soundInputSource = soundInputSource

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()

        deviceIndex = 0

        for i in range(self._audio_interface.get_device_count()):
            info = self._audio_interface.get_device_info_by_index(i)
            print(f"Found device {info}")

            if self._soundInputSource == MicrophoneStreamInputSource.Loopback and "loopback" in info['name'].lower():
                deviceIndex = i
                print(f"Used device {info}")
                break
            elif self._soundInputSource == MicrophoneStreamInputSource.Microphone and "microphone" in info['name'].lower():
                deviceIndex = i
                print(f"Used device {info}")
                break
            elif self._soundInputSource == MicrophoneStreamInputSource.SoundFlower and "soundflower (2ch)" in info['name'].lower():
                deviceIndex = i
                print(f"Used device {info}")
                break


        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=self._soundSettings[self._soundInputSource].numChannels, rate=self._soundSettings[self._soundInputSource].rate,
            input_device_index=deviceIndex,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )
        # Do not listen at start
        self._listening = False
        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def setListening(self, listen):
        self._listening = listen

    def isListening(self):
        return self._listening

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return

            if not self._listening:
                continue

            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


class SpeechInputRecognitionStreaming(object):

    def __init__(self, soundInputSource=MicrophoneStreamInputSource.Microphone, language_supports=["en-US"]):
        self._soundInputSource = soundInputSource
        self._language_supports = language_supports
        self._stream = None
        self.ready = False

    def _listenPrintLoop(self, responses, callback, stream):
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.
        """
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.
            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            transcript = result.alternatives[0].transcript

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result
            overwrite_chars = ' ' * (num_chars_printed - len(transcript))

            if not result.is_final:
                # sys.stdout.write(transcript + overwrite_chars + '\r')
                # sys.stdout.flush()

                num_chars_printed = len(transcript)

            else:
                finaltext = transcript + overwrite_chars

                # Don't listen while we are going to start talking
                # stream.setListening(False)

                if stream.isListening():
                    if callback(finaltext, result.language_code):
                        break
                # stream.setListening(True)

                # Can start listening again now

                num_chars_printed = 0

    def set_listening(self, is_listening):
        self._stream.setListening(is_listening)

    def is_listening(self):
        return self._stream.isListening()

    def listen_forever(self, callback):
        while True:
            language_code = self._language_supports[0]  # a BCP-47 language tag
            # alternative_language_codes = []
            #
            # if len(self._language_supports) > 1:
            #     alternative_language_codes = self._language_supports[1:]

            client = speech.SpeechClient()
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=language_code,
                enable_automatic_punctuation=True
                # alternative_language_codes=alternative_language_codes
            )
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True)

            with MicrophoneStream(RATE, CHUNK, self._soundInputSource) as stream:
                self._stream = stream
                audio_generator = stream.generator()
                requests = (speech.StreamingRecognizeRequest(audio_content=content)
                            for content in audio_generator)

                self.ready = True
                responses = client.streaming_recognize(streaming_config, requests)

                try:
                    self._listenPrintLoop(responses, callback, stream)
                    break
                except Exception as ex:
                    # Most likely stream too long exception, so just log and restart
                    print(ex)
                    pass
