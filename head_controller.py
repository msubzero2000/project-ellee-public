import os
from adafruit_servokit import ServoKit
import board
import busio
import time
import math
import threading
from queue import Queue


class HeadController(object):
    servo_deg_to_sv_mappings = [[(4, 0), (90, 100)],  # servo 0 (d1, sv1), (d2, sv2), ...
                                [(4, 0), (90, 100)]]  # servo 1 (d1, sv1), (d2, sv2), ...

    servo_range = [[10, 170], [35, 90]]

    HEADING_SERVO = 0
    PITCH_SERVO = 1

    max_speed = 1.5
    min_speed = 0.5

    def __init__(self):
        self.servo_value = {}

        # On the Jetson Nano
        # Bus 0 (pins 28,27) is board SCL_1, SDA_1 in the jetson board definition file
        # Bus 1 (pins 5, 3) is board SCL, SDA in the jetson definition file
        # Default is to Bus 1; We are using Bus 0, so we need to construct the busio first ...
        print("Initializing Servos")
        i2c_bus0 = (busio.I2C(board.SCL_1, board.SDA_1))
        print("Initializing ServoKit")
        self.kit = ServoKit(channels=16, i2c=i2c_bus0)

        self._target_heading = 90
        self._target_pitch = 90

        self._run_thread = True
        self._thread = threading.Thread(target=self._callback, args=(1,))
        self._thread.daemon = False
        self._thread.start()

    def __del__(self):
        self._run_thread = False
        self._thread.join()

    def _angle_to_servo_value(self, servo_no, angle):
        # Make sure we do not pass the servo range
        min_angle = self.servo_range[servo_no][0]
        max_angle = self.servo_range[servo_no][1]
        angle = min(max(min_angle, angle), max_angle)

        d1, sv1 = self.servo_deg_to_sv_mappings[servo_no][0]
        d2, sv2 = self.servo_deg_to_sv_mappings[servo_no][1]

        # avoid division by 0
        if d2 == d1:
            d2 = d1 + 0.0001

        sv = (sv2 - sv1) * (angle - d1) / (d2 - d1) + sv1
        sv = max(0, min(180, sv))

        return sv

    def _servo_value_to_angle(self, servo_no, value):
        d1, sv1 = self.servo_deg_to_sv_mappings[servo_no][0]
        d2, sv2 = self.servo_deg_to_sv_mappings[servo_no][1]

        # avoid division by 0
        if sv2 == sv1:
            sv2 = sv1 + 0.0001

        angle = (value - sv1) * (d2 - d1) / (sv2 - sv1) + d1

        return angle

    def _move_to(self, servo_no, angle):
        sv = self._angle_to_servo_value(servo_no, angle)
        print(f"Moving servo {servo_no} to {angle} deg => {sv}")

        new_value = max(0, min(180, sv))
        self.kit.servo[servo_no].angle = new_value
        self.servo_value[servo_no] = new_value

    def _move_head(self):
        if self.HEADING_SERVO not in self.servo_value or self.PITCH_SERVO not in self.servo_value:
            # If we never recorded one of the servo value, just move the servo without
            # speed throttling and wait for 1 sec as we don't know our current servo position
            self._move_to(self.HEADING_SERVO, self._target_heading)
            self._move_to(self.PITCH_SERVO, self._target_pitch)
            time.sleep(1)
        else:
            # Calculate the next step
            target_heading_value = self._angle_to_servo_value(self.HEADING_SERVO, self._target_heading)
            target_pitch_value = self._angle_to_servo_value(self.PITCH_SERVO, self._target_pitch)

            heading_delta = (target_heading_value - self.servo_value[self.HEADING_SERVO])
            pitch_delta = (target_pitch_value - self.servo_value[self.PITCH_SERVO])

            # calculate distance
            distance = math.sqrt(pow(heading_delta, 2) + pow(pitch_delta, 2))
            if distance <= self.min_speed:
                sv_new_heading = self._angle_to_servo_value(self.HEADING_SERVO, self._target_heading)
                sv_new_pitch = self._angle_to_servo_value(self.PITCH_SERVO, self._target_pitch)
                sleep_time = 0.01
            else:
                capped_distance = min(distance, self.max_speed)
                norm_distance = capped_distance / distance
                # Add a further slowdown by using sleep_time
                sleep_time = 0.01 + 0.05 * (1.0 - min(1.0, distance / 20.0))

                sv_new_heading = self.servo_value[self.HEADING_SERVO] + heading_delta * norm_distance
                sv_new_pitch = self.servo_value[self.PITCH_SERVO] + pitch_delta * norm_distance

            # print(f"Heading {sv_new_heading:.1f} pitch {sv_new_pitch:.1f}")
            self._set_servo(self.HEADING_SERVO, sv_new_heading, sleep_time)
            self._set_servo(self.PITCH_SERVO, sv_new_pitch, sleep_time)
            # Sleep enough to make sure the servo has reached the destination for the current step

    def _set_servo(self, servo_no, value, sleep_time):
        self.kit.servo[servo_no].angle = value
        # Sleep enough to make sure the servo has reached the destination for the current step
        time.sleep(sleep_time)

        self.servo_value[servo_no] = value

    def look_at(self, heading, pitch):
        min_heading = self.servo_range[self.HEADING_SERVO][0]
        max_heading = self.servo_range[self.HEADING_SERVO][1]
        heading = min(max(min_heading, heading), max_heading)

        min_pitch = self.servo_range[self.PITCH_SERVO][0]
        max_pitch = self.servo_range[self.PITCH_SERVO][1]
        pitch = min(max(min_pitch, pitch), max_pitch)

        # Avoid doing too many small head movement due to detection noise
        if abs(heading - self._target_heading) > 2:
            self._target_heading = heading

        if abs(pitch - self._target_pitch) > 2:
            self._target_pitch = pitch

    def _callback(self, data):
        while self._run_thread:
            self._move_head()

    def current_head_angle(self):
        heading = self._servo_value_to_angle(self.HEADING_SERVO, self.servo_value[self.HEADING_SERVO])
        pitch = self._servo_value_to_angle(self.PITCH_SERVO, self.servo_value[self.PITCH_SERVO])

        return heading, pitch