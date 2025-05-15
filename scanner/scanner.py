from itertools import product
import time
import numpy as np

from scanner.motion_controller import MotionController
from scanner.probe_controller import ProbeController
from scanner.gcode_simulator_dep import GcodeSimulator

class Scanner:
    def __init__(self, motion_controller=None, probe_controller=None):
        self._motion_controller = MotionController(GcodeSimulator())  
        self._probe_controller = ProbeController(None)
        self._update_target_callback = None  
        self._update_data_callback = None  

    def set_update_target_callback(self, callback):
        """Set a callback function to update the target position"""
        self._update_target_callback = callback

    def set_update_data_callback(self, callback):
        """Set a callback function to update scan data"""
        self._update_data_callback = callback

    def run_scan(self, scan_order="XY", x_dim=50.0, y_dim=50.0, x_step=10.0, y_step=10.0,
                 x_start=None, y_start=None, x_end=None, y_end=None):
        try:
            if x_start is None or y_start is None or x_end is None or y_end is None:
                x_start = -x_dim / 2
                y_start = -y_dim / 2
                x_end = x_dim / 2
                y_end = y_dim / 2

            x_range = np.arange(x_start, x_end + x_step, x_step)
            y_range = np.arange(y_start, y_end + y_step, y_step)

            x_range = x_range[x_range <= x_end]
            y_range = y_range[y_range <= y_end]

            scan_xy = []
            if scan_order == "XY":
                for i, y in enumerate(y_range):
                    if i % 2 == 0:
                        for x in x_range:
                            scan_xy.append((x, y))
                    else:
                        for x in reversed(x_range):
                            scan_xy.append((x, y))
            else:  
                for i, x in enumerate(x_range):
                    if i % 2 == 0:
                        for y in y_range:
                            scan_xy.append((x, y))
                    else:
                        for y in reversed(y_range):
                            scan_xy.append((x, y))

            start = time.time()
            self.scan_data = []
            for i, (x, y) in enumerate(scan_xy):
                x = float(x)
                y = float(y)
                if self._update_target_callback:
                    try:
                        self._update_target_callback(x, y)
                    except Exception as e:
                        raise
                try:
                    self._motion_controller.move_absolute({0: x, 1: y})
                except Exception as e:
                    raise
                if i == 0:
                    self._probe_controller.scan_begin()
                else:
                    data = self._probe_controller.scan_read_measurement(i - 1, (x, y))
                    if data:
                        self.scan_data.append(data)
                        if self._update_data_callback:
                            self._update_data_callback(i - 1, (x, y), data)

                while self._motion_controller.is_moving():
                    time.sleep(0.001)

                self._probe_controller.scan_trigger_and_wait(i, (x, y))

                time.sleep(0.05)

            self._motion_controller.move_absolute({0: 0, 1: 0})
            if self._update_target_callback:
                self._update_target_callback(0, 0)
            data = self._probe_controller.scan_read_measurement(len(scan_xy) - 1, (x, y))
            if data:
                self.scan_data.append(data)
                if self._update_data_callback:
                    self._update_data_callback(len(scan_xy) - 1, (x, y), data)
            self._probe_controller.scan_end()

        except Exception as e:
            raise

    def close(self):
        self._motion_controller.disconnect()
        self._probe_controller.disconnect()

    @property
    def motion_controller(self):
        return self._motion_controller

    @motion_controller.setter
    def motion_controller(self, value):
        self._motion_controller = value

    @property
    def probe_controller(self):
        return self._probe_controller

    @probe_controller.setter
    def probe_controller(self, value):
        self._probe_controller = value