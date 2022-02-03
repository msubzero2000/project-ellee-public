import os
import boto3
import hashlib

from audio import Audio
from utilities.fileSearch import FileSearch


class Speech(object):
    AWS_KEY = "Your AWS Key"
    AWS_SECRET = "Your AWS Secret"

    def __init__(self, audioFolder):
        self._audio = Audio()
        self._audioFolder = audioFolder
        audioFilePathList = FileSearch.collectFilesEndsWithNameRecursively(".mp3", audioFolder)

        self._cache = {}
        for path in audioFilePathList:
            fileName = path.split("/")[-1].split(".")[0]
            self._cache[fileName] = path

        self._pollyClient = boto3.Session(
                        aws_access_key_id=self.AWS_KEY,
                        aws_secret_access_key=self.AWS_SECRET,
                        region_name='ap-southeast-2').client('polly')

    def speak(self, text):
        hashObject = hashlib.sha1(text.encode())
        hash = hashObject.hexdigest()

        if hash in self._cache:
            audioFilePath = self._cache[hash]
        else:
            print("GENERATING NEW TTS")
            audioFilePath = self._tts(text, hash)

        self._cache[hash] = audioFilePath

        self._audio.play(audioFilePath)


    def isSpeaking(self):
        return self._audio.isPlaying()

    def isAfterSpeaking(self):
        return self._audio.isAfterPlaying()

    def _tts(self, text, hash):
        response = self._pollyClient.synthesize_speech(VoiceId='Ivy',
                        OutputFormat='mp3',
                        Text = text)
        if not os.path.exists(self._audioFolder):
            os.mkdir(self._audioFolder)

        filePath = os.path.join(self._audioFolder, "{0}.mp3".format(hash))
        file = open(filePath, 'wb')
        file.write(response['AudioStream'].read())
        file.close()

        return filePath
