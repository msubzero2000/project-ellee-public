import os
import time

ENABLE_HEAD_CONTROLLER = False
ENABLE_SIGHT = False

if ENABLE_HEAD_CONTROLLER:
    from head_controller import HeadController
else:
    from head_controller_fake import HeadControllerFake as HeadController

if ENABLE_SIGHT:
    from sight_object_detection import SightObjectDetection as Sight
else:
    from sight_object_detection_fake import SightObjectDetectionFake as Sight

from brain_state_machine import BrainStateMachine, StateMachineReturn
from const import Const


class EllaBot(object):

    def __init__(self):
        self._head = HeadController()
        self._sight = Sight()
        self._brain_sm = BrainStateMachine()

    def run(self):
        ctr = 0
        camera_heading_range = (40, 140)
        camera_pitch_range = (40, 140)

        while True:
            person, updated_od, updated_fd = self._sight.detect()
            state_return, new_face_to_register = self._brain_sm.update(person)

            if new_face_to_register is not None:
                self._sight.register_new_face(new_face_to_register)

            if ctr > 5 and updated_od:
                ctr = 0
                # adjust head every 5 frames
                if person is not None and person.face_bbox is not None:
                    f_left = person.face_bbox.x1
                    f_top = person.face_bbox.y1
                    f_right = person.face_bbox.x2
                    f_bottom = person.face_bbox.y2

                    f_center_x = (f_left + f_right) / 2
                    f_center_y = (f_top * 0.2 + f_bottom * 0.8) # Approx eye position

                    par_x = 1.0 - f_center_x / Const.CaptureWidth
                    par_y = f_center_y / Const.CaptureHeight

                    heading = camera_heading_range[0] * (1.0 - par_x) + camera_heading_range[1] * par_x
                    pitch = camera_pitch_range[0] * (1.0 - par_y) + camera_pitch_range[1] * par_y

                    head_heading, head_pitch = self._head.current_head_angle()

                    # Offset the camera heading/pitch with the current head heading/pitch
                    heading = head_heading + heading - 90
                    pitch = head_pitch + pitch - 90

                    print(f"Heading {heading:.1f} pitch {pitch:.1f}")

                    self._head.look_at(heading, pitch)
                else:
                    # Reset the head
                    if state_return == StateMachineReturn.HeadReset:
                        self._head.look_at(90, 90)
            ctr += 1


ella_bot = EllaBot()
ella_bot.run()
