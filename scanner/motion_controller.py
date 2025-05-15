from abc import ABC, abstractmethod
from typing import Sequence, Dict, List, Tuple
import time
import math
import threading
import numpy as np

from scanner.plugin_setting import PluginSetting

class MotionControllerPlugin(ABC):
    settings_pre_connect: list[PluginSetting]
    settings_post_connect: list[PluginSetting]

    def __init__(self) -> None:
        self.settings_pre_connect = []
        self.settings_post_connect = []

    def add_setting_pre_connect(self, setting: PluginSetting):
        self.settings_pre_connect.append(setting)
    
    def add_setting_post_connect(self, setting: PluginSetting):
        self.settings_post_connect.append(setting)

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_axis_display_names(self) -> tuple[str, ...]:
        pass

    @abstractmethod
    def get_axis_units(self) -> tuple[str, ...]:
        pass

    @abstractmethod
    def set_velocity(self, velocities: dict[int, float]) -> None:
        pass

    @abstractmethod
    def set_acceleration(self, accels: dict[int, float]) -> None:
        pass

    @abstractmethod
    def move_relative(self, move_dist: dict[int, float]) -> dict[int, float] | None:
        pass

    @abstractmethod
    def move_absolute(self, move_pos: dict[int, float]) -> dict[int, float] | None:
        pass

    @abstractmethod
    def home(self, axes: list[int]) -> dict[int, float]:
        pass

    @abstractmethod
    def get_current_positions(self) -> tuple[float, ...]:
        pass

    @abstractmethod
    def get_target_positions(self) -> tuple[float, ...]:
        pass

    @abstractmethod
    def is_moving(self) -> bool:
        pass

    @abstractmethod
    def get_endstop_minimums(self) -> tuple[float, ...]:
        pass

    @abstractmethod
    def get_endstop_maximums(self) -> tuple[float, ...]:
        pass

class MotionDriverSimulated(MotionControllerPlugin):
    def __init__(self):
        super().__init__()
        self._connected = False
        self._positions = [0.0, 0.0, 0.0]  
        self._target_positions = [0.0, 0.0, 0.0] 
        self._moving = False
        self._move_duration = 0.1  
        self._move_start_time = 0
        self._axis_labels = ("X", "Y", "Z")
        self._axis_units = ("mm", "mm", "mm")
        self._endstop_minimums = (-300.0, -300.0, -300.0)
        self._endstop_maximums = (300.0, 300.0, 300.0)

    def connect(self) -> None:
        self._connected = True
        self._sim_thread = threading.Thread(target=self._simulate_motion_loop, daemon=True)
        self._sim_thread.start()

    def disconnect(self) -> None:
        self._connected = False

    def get_axis_display_names(self) -> tuple[str, ...]:
        return self._axis_labels

    def get_axis_units(self) -> tuple[str, ...]:
        return self._axis_units

    def set_velocity(self, velocities: dict[int, float]) -> None:
        pass

    def set_acceleration(self, accels: dict[int, float]) -> None:
        pass

    def move_absolute(self, move_pos: dict[int, float]) -> dict[int, float] | None:
        if not self._connected:
            raise RuntimeError("Motion driver not connected")
        
        now = time.time()
        self._start_positions = self._positions.copy()
        self._last_move_time = now

        total_distance = math.sqrt(sum(
            (move_pos[axis] - self._start_positions[axis]) ** 2
            for axis in move_pos
        ))

        self._velocity = 25.0 
        self._move_duration = total_distance / self._velocity if self._velocity > 0 else 0.5
        self._move_duration = max(self._move_duration, 0.05) 
        self._moving = True

        for axis, pos in move_pos.items():
            if 0 <= axis < len(self._target_positions):
                self._target_positions[axis] = pos

        return {axis: self._target_positions[axis] for axis in move_pos}

    def move_relative(self, move_dist: dict[int, float]) -> dict[int, float] | None:
        if not self._connected:
            raise RuntimeError("Motion driver not connected")
            
        self._moving = True
        self._move_start_time = time.time()
        
        new_positions = {}
        for axis, delta in move_dist.items():
            if 0 <= axis < len(self._positions):
                new_pos = self._positions[axis] + delta
                self._target_positions[axis] = new_pos
                new_positions[axis] = new_pos
                
        return new_positions

    def home(self, axes: list[int]) -> dict[int, float]:
        if not self._connected:
            raise RuntimeError("Motion driver not connected")
            
        self._moving = True
        self._move_start_time = time.time()
        
        home_positions = {}
        for axis in axes:
            if 0 <= axis < len(self._target_positions):
                self._target_positions[axis] = 0.0
                home_positions[axis] = 0.0
                
        return home_positions

    def get_current_positions(self) -> tuple[float, ...]:
        return tuple(self._positions)

    def get_target_positions(self) -> tuple[float, ...]:
        return tuple(self._target_positions)
    
    def _simulate_motion_loop(self):
        while self._connected:
            self._update_motion()
            time.sleep(0.01)

    def _update_motion(self):
        if self._moving:
            elapsed = time.time() - self._last_move_time
            fraction = min(elapsed / self._move_duration, 1.0)
            for i in range(len(self._positions)):
                start = self._start_positions[i]
                target = self._target_positions[i]
                self._positions[i] = start + (target - start) * fraction
            if fraction >= 1.0:
                self._positions = self._target_positions.copy()
                self._moving = False

    def is_moving(self) -> bool:
        return self._moving

    def get_endstop_minimums(self) -> tuple[float, ...]:
        return self._endstop_minimums

    def get_endstop_maximums(self) -> tuple[float, ...]:
        return self._endstop_maximums

class MotionController:
    _axis_labels: tuple[str, ...]
    _target_positions: list[float]
    _endstop_minimums: tuple[float, ...]
    _endstop_maximums: tuple[float, ...]

    _driver: MotionControllerPlugin
    _is_driver_connected: bool

    def __init__(self, motion_plugin: MotionControllerPlugin) -> None:
        self._driver = motion_plugin
        self._is_driver_connected = False
        self.disconnect()

    def connect(self) -> None:
        try:
            self._driver.connect()
            self._is_driver_connected = True
            self._axis_labels = self._driver.get_axis_display_names()
            self._target_positions = list(self._driver.get_current_positions())
            self._endstop_minimums = self._driver.get_endstop_minimums()
            self._endstop_maximums = self._driver.get_endstop_maximums()
        except Exception as e:
            print(f"Error connecting motion controller: {e}")
            raise

    def is_connected(self) -> bool:
        return self._is_driver_connected
    
    def disconnect(self) -> None:
        try:
            was_connected = self._is_driver_connected
            self._is_driver_connected = False
            self._axis_labels = ()
            self._target_positions = []
            self._endstop_minimums = ()
            self._endstop_maximums = ()
            if was_connected:
                self._driver.disconnect()
        except Exception as e:
            print(f"Error disconnecting motion controller: {e}")

    def must_be_connected(self) -> None:
        if not self._is_driver_connected:
            raise ConnectionError("Motion driver must be connected to use this functionality.")
    
    def must_be_valid_index(self, inds: Sequence[int]) -> None:
        try:
            if min(inds) < 0:
                raise ValueError(f"Axis index '{min(inds)}' is invalid.")
            if max(inds) >= len(self._axis_labels):
                raise ValueError(f"Axis index '{max(inds)}' is invalid.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Invalid axis indices: {e}")

    def swap_motion_plugin(self, motion_plugin: MotionControllerPlugin) -> None:
        self.disconnect()
        self._driver = motion_plugin
    
    def set_velocity(self, axis_velocities: dict[int, float]) -> None:
        self.must_be_connected()
        self._driver.set_velocity(axis_velocities)

    def set_acceleration(self, axis_accels: dict[int, float]) -> None:
        self.must_be_connected()
        self._driver.set_acceleration(axis_accels)

    def move_absolute(self, axis_positions: dict[int, float]) -> None:
        self.must_be_connected()
        self.must_be_valid_index(axis_positions.keys())

        for ind in axis_positions:
            if ind < len(self._endstop_maximums):  
                axis_positions[ind] = max(min(axis_positions[ind], self._endstop_maximums[ind]), 
                                        self._endstop_minimums[ind])
        ret_positions = self._driver.move_absolute(axis_positions)
        if ret_positions is None:
            ret_positions = axis_positions
        if self._driver.is_moving():
            for ind, val in ret_positions.items():
                if ind < len(self._target_positions): 
                    self._target_positions[ind] = val
        if not self._driver.is_moving():
            current_positions = self._driver.get_current_positions()
            for ind in range(len(self._target_positions)):
                if ind < len(current_positions):
                    self._target_positions[ind] = current_positions[ind]

    def move_relative(self, axis_offsets: dict[int, float]) -> None:
        self.must_be_connected()
        self.must_be_valid_index(axis_offsets.keys())

        current_positions = self._driver.get_current_positions()
        abs_positions = {
            axis: current_positions[axis] + offset for axis, offset in axis_offsets.items()
        }

        self.move_absolute(abs_positions)


    def home(self, axes: list[int]) -> dict[int, float]:
        self.must_be_connected()
        self.must_be_valid_index(axes)
        home_positions = self._driver.home(axes)
        return home_positions

    def is_moving(self) -> bool:
        self.must_be_connected()
        return self._driver.is_moving()
    
    def get_current_positions(self) -> tuple[float, ...]:
        self.must_be_connected()
        return self._driver.get_current_positions()

    def get_target_positions(self) -> tuple[float, ...]:
        self.must_be_connected()
        return self._driver.get_target_positions()