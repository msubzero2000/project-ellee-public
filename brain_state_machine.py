import os

from utilities.stopwatch import Stopwatch
from intent import Intent, GetRespondState
from const import Const
from face_object import FaceObject


class BrainState(object):
    Idle = "Idle"
    Engaging = "Engaging"
    Conversing = "Conversing"


class StateMachineReturn(object):
    Nothing = "Nothing"
    HeadReset = "HeadReset"


class BrainStateMachine(object):
    TimeToDisengaged = 6    # If the focus person is invisible for longer than 6 seconds, reset the state back to idle
    TimeToConverse = 2      # If face is visible for 2 seconds, start talking

    MinFaceWidthToRegister = Const.CaptureWidth / 20 # Do not register face smaller than 1/20 the capture window size
    MinFaceHeightToRegister = Const.CaptureHeight / 20

    def __init__(self):
        self._state = BrainState.Idle
        self._intent = Intent()
        self._person = None
        self._known_person_name = None
        self._stop_watch = None
        self._disengaged_stop_watch = None

    def _update_engaged_person(self, person):
        if person is None:
            return

        if not self._person.is_face_detected and person.is_face_detected:
            # Put more priority on person with detected face
            self._person = person
            # Put more priority on known person
        elif self._person.is_face_detected and person.is_face_detected and self._person.person_name is None and person.person_name is not None:
            self._person = person

        # Record any person who we know. We will use this to decide if we need to register a new person at the end
        # of the current conversation
        if person.person_name is not None:
            self._known_person_name = person.person_name

    def is_disengaged(self, person):
        if person is not None:
            # If we have a person, keep resetting disengaged_stop_watch
            self._disengaged_stop_watch = Stopwatch()
        else:
            # Otherwise check if disengaged_stop_watch is timing out
            if self._disengaged_stop_watch is None:
                self._disengaged_stop_watch = Stopwatch()

            duration = self._disengaged_stop_watch.get() / 1000

            if duration >= self.TimeToDisengaged:
                return True

        return False

    def _greet_person(self):
        if self._person.person_name is not None:
            self._intent.speak(f"Hi {self._person.person_name}. It's good to see you. What do you want to talk about today?")
        else:
            self._intent.speak(f"Hi there! My name is {Const.MyName}. Do you want to chat with me? You can ask me about anything")

    def update(self, person):
        state_return = StateMachineReturn.Nothing
        new_face_to_register = None
        if self._state == BrainState.Idle:
            if person is not None:
                self._state = BrainState.Engaging
                # Remember this person
                self._person = person
                self._stop_watch = Stopwatch()
                self._disengaged_stop_watch = None
                # print(f"State IDLE")
            else:
                state_return = StateMachineReturn.HeadReset
        elif self._state == BrainState.Engaging:
            self._update_engaged_person(person)
            duration = self._stop_watch.get() / 1000
            # If a face is detected for x amount of time, starts talking
            if self._person.is_face_detected and duration > self.TimeToConverse:
                # Start conversing
                self._state = BrainState.Conversing
                self._greet_person()
            # print(f"State ENGAGING")
        elif self._state == BrainState.Conversing:
            self._update_engaged_person(person)

            # Only process the sub state machine when not speaking
            if not self._intent.is_speaking():
                # Start listening if we are not speaking anymore
                self._intent.start_listening()

                if self.is_disengaged(person):
                    print("Disengaged - Cannot see anyone")
                    # No one to talk to anymore... or at least out of sight. Back to idle state
                    # First we check if we can extract any info from current conversation
                    new_face_to_register = self._register_new_person_if_any()
                    self._reset()
                else:
                    # Pool thought module to hear what the human said and to generate respond from GPT3
                    get_respond_state, respond_message = self._intent.get_respond()

                    if get_respond_state == GetRespondState.HearingTimeOut:
                        # Did not hear anything from the human for a while. Apologise and remove last conversation from the record
                        self._intent.remove_last_conversation()
                        # Don't record this conversation
                        self._intent.speak(f"Sorry I didn't hear you. Do you want to say or ask me about anything?", record=False)
                    elif get_respond_state == GetRespondState.GPT3TimeOut:
                        # Got GPT3 issue. Aplogise and remove last conversation from the record
                        self._intent.remove_last_conversation()
                        # Don't record this conversation
                        self._intent.speak(f"Sorry My brain has some issue gathering some thoughts. Would you please say again?", record=False)
                    elif get_respond_state == GetRespondState.Completed:
                        if respond_message is not None and len(respond_message) > 0:
                            self._intent.speak(respond_message)
            # print(f"State CONVERSING")

        return state_return, new_face_to_register

    def _register_new_person_if_any(self):
        new_face = None
        # If we do not know this person, and we don't know anyone detected during current conversation...
        # let's try to extract their name from
        # the conversation and register the name against the captured face (if any)
        if self._person is not None and self._person.person_name is None and self._person.face_image is not None and self._known_person_name is None:
            if self._person.face_bbox.width() >= self.MinFaceWidthToRegister and self._person.face_bbox.height() >= self.MinFaceHeightToRegister:
                name = self._intent.extract_name()
                if name is not None:
                    new_face = FaceObject(name=name, bounding_box=None, score=None, face_image=self._person.face_image)

        return new_face

    def _reset(self):
        self._state = BrainState.Idle

        # Forget the focus person we were engaged with
        self._person = None
        self._known_person_name = None

        # Stop listening
        self._intent.reset()
        self._disengaged_stop_watch = None