import os
import threading
import random

from speech import Speech
from thoughts import Thoughts
from hearing import Hearing
from utilities.stopwatch import Stopwatch


class GetRespondState(object):
    Idle = "Idle"
    Listening = "Listening"
    WaitingForGPT3 = "WaitingForGPT3"
    HearingTimeOut = "HearingTimeOut"
    GPT3TimeOut = "GPT3TimeOut"
    Completed = "Completed"


class Intent(object):

    HumanPrefix = "Human"

    ListeningTimeOut = 15  # Wait to listen for a speech for 8 seconds before timeout
    Gpt3TimeOut = 5       # Wait for Gpt3 for 5 seconds before timeout

    MinConversationExchangeToRegisterNewFace = 6  # At least there should be 6 exchanges (meaning 2 from human)
                                                  # to register this person as a new face
    def __init__(self):
        self._conversations = []
        self._speech = Speech("audio")
        self._hearing = Hearing()
        self._thoughts = Thoughts()
        self._respond_state = GetRespondState.Idle
        self._last_gpt3_response = None
        self._gpt3_call_completed = False
        self._stop_watch = Stopwatch()

    def speak(self, text, record=True):
        print(f"AI: {text}")
        self._hearing.stop_listening()
        self._speech.speak(text)

        # Record what the AI said (unless told not to)
        if record:
            self._conversations.append(f"AI: {text}")

    def is_speaking(self):
        return self._speech.isSpeaking()

    def start_listening(self):
        self._hearing.start_listening()

    def stop_listening(self):
        self._hearing.stop_listening()

    def get_respond(self):
        respond_message = None

        # Start the state machine if the state was idle or previously completed/timeout
        if self._respond_state in [GetRespondState.Idle, GetRespondState.GPT3TimeOut,
                                   GetRespondState.HearingTimeOut, GetRespondState.Completed]:
            self.start_listening()
            self._respond_state = GetRespondState.Listening
            self._stop_watch = Stopwatch()
        elif self._respond_state == GetRespondState.Listening:
            # Pool the hearing module to get the last heard message
            last_heard_message = self._hearing.get_last_speech_message()

            # Got message?
            if last_heard_message is not None and len(last_heard_message) > 0:
                print(f"Human: {last_heard_message}")
                self.stop_listening()

                # Record the message into our conversation history
                self._conversations.append(f"{self.HumanPrefix}: {last_heard_message}")

                self._respond_state = GetRespondState.WaitingForGPT3
                self._gpt3_call_completed = False
                self._last_gpt3_response = None
                self._stop_watch = Stopwatch()

                # Pass the convo history to GP3 to generate responds in async manner
                self._last_request_id = random.random() # Generate a random request id and keep it for request cancellation
                self._thread = threading.Thread(target=self._callback, args=(self._last_request_id,))
                self._thread.daemon = False
                self._thread.start()
            else:
                # Keep listening until timeout
                duration = self._stop_watch.get() / 1000

                if duration >= self.ListeningTimeOut:
                    self._respond_state = GetRespondState.HearingTimeOut
        elif self._respond_state == GetRespondState.WaitingForGPT3:
            if self._gpt3_call_completed:
                # Reset the state back to idle
                self._respond_state = GetRespondState.Completed
                # Finally return the gpt3 response
                respond_message = self._last_gpt3_response
            else:
                # Keep waiting until timeout
                duration = self._stop_watch.get() / 1000

                if duration >= self.Gpt3TimeOut:
                    self._respond_state = GetRespondState.GPT3TimeOut

        return self._respond_state, respond_message

    def reset(self):
        self.stop_listening()
        self._respond_state = GetRespondState.Idle
        # Reset the conversation history
        self._conversations = []

    def _callback(self, request_id):
        full_conversations, last_response = self._thoughts.conversation(self._conversations)

        # Only return the response if the last request id is ours. Otherwise, another request might be
        # running and let it be the one to return the response.
        if self._last_request_id == request_id:
            # Record the response and signal the main thread that we are completed
            self._last_gpt3_response = last_response
            self._gpt3_call_completed = True
            self._last_request_id = None

    def remove_last_conversation(self):
        self._conversations = self._conversations[:-1]

    def extract_name(self):
        # Need at least a few exchanges to consider registering a new face
        if len(self._conversations) > self.MinConversationExchangeToRegisterNewFace:
            name = self._thoughts.extract_name(self._conversations)

            return name

        return None