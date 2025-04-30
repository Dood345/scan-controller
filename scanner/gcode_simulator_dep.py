from typing import Sequence, Any

from scanner.plugin_setting import PluginSettingString, PluginSettingInteger
from scanner.motion_controller import MotionControllerPlugin

import zmq
import time
import math
import threading

DEFAULT_PORT = 5556
DEFAULT_VELOCITY = 25.0  # Add a standard velocity

class GcodeSimulator(MotionControllerPlugin):
    port: PluginSettingInteger
    number_of_axes: PluginSettingInteger

    _socket: zmq.Socket

    axis_names = ("X", "Y", "Z", "W")

    def __init__(self) -> None:
        self.port = PluginSettingInteger("Port Number", DEFAULT_PORT)
        self.number_of_axes = PluginSettingInteger("Number of Axes", 0, read_only=True)
        super().__init__()
        self.add_setting_pre_connect(self.port)
        self.add_setting_post_connect(self.number_of_axes)
        self._connected = False
        self._current_positions = {i: 0.0 for i in range(4)}
        self._target_positions = {i: 0.0 for i in range(4)}
        self._is_moving = False
        self._start_positions = self._current_positions.copy()
        self._last_move_time = 0.0
        self._move_duration = 0.5
        self._socket_lock = threading.Lock()
        self._position_lock = threading.Lock()
        self._velocity = DEFAULT_VELOCITY 

    def write_line(self, line: str) -> None:
        with self._socket_lock:
            self._socket.send_string(f"{line}\n", flags=zmq.DONTWAIT)

    def read_line(self, timeout_ms: int = 500) -> str:  # Increased timeout
        with self._socket_lock:
            if self._socket.poll(timeout_ms, zmq.POLLIN):
                return self._socket.recv_string()
            raise TimeoutError("ZMQ read timeout")
        
    def _update_motion(self):
        if self._is_moving:
            elapsed = time.time() - self._last_move_time
            # Use standard velocity-based timing calculation
            if elapsed < self._move_duration:
                fraction = min(1.0, elapsed / self._move_duration)
                positions = {
                    i: self._start_positions[i] + (self._target_positions[i] - self._start_positions[i]) * fraction
                    for i in range(4)
                }
                self._current_positions.update(positions)
            else:
                self._is_moving = False
                self._current_positions.update(self._target_positions)
            
    def _simulate_motion_loop(self):
        while self._connected:
            self._update_motion()
            time.sleep(0.01)  

    def format_axis_command(self, command: str, axis_vals: dict[int, float]) -> str:
        return f"{command} " + " ".join(f"{self.axis_names[axis]}{val:.3f}" for axis, val in axis_vals.items())

    def check_for_error(self, return_code: str) -> str:
        if return_code.startswith("Error"):
            raise ValueError(f"Device returned error message: '{return_code}'.")
        return return_code

    def connect(self) -> None:
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect(f"tcp://localhost:{self.port.value}")
        self.get_current_positions()
        self.number_of_axes.value = 4
        self._connected = True

        self._sim_thread = threading.Thread(target=self._simulate_motion_loop, daemon=True)
        self._sim_thread.start()

    def disconnect(self) -> None:
        self.number_of_axes.value = 0
        self._connected = False
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()

    def is_connected(self) -> bool:
        return self._connected

    def get_axis_display_names(self) -> tuple[str, ...]:
        return self.axis_names

    def get_axis_units(self) -> tuple[str, ...]:
        return ("mm",) * len(self.axis_names)

    def set_velocity(self, velocities: dict[int, float]) -> None:
        avg_velocity = sum(velocities.values()) / len(velocities) if velocities else DEFAULT_VELOCITY
        self._velocity = avg_velocity
        
        self.write_line(self.format_axis_command("V00", velocities))
        self.check_for_error(self.read_line())

    def set_acceleration(self, accel: dict[int, float]) -> None:
        self.write_line(self.format_axis_command("A00", accel))
        self.check_for_error(self.read_line())

    def move_relative(self, move_dist: dict[int, float]) -> dict[int, float] | None:
        total_distance = math.sqrt(sum(dist ** 2 for dist in move_dist.values()))
        self._move_duration = total_distance / self._velocity if self._velocity > 0 else 0.5
        self._move_duration = max(self._move_duration, 0.15)
        
        self._start_positions = self._current_positions.copy()  
        new_positions = {}
        for axis, dist in move_dist.items():
            new_pos = self._current_positions[axis] + dist
            self._target_positions[axis] = new_pos
            new_positions[axis] = new_pos

        self._is_moving = True
        self._last_move_time = time.time()
        self.write_line(self.format_axis_command("G01", move_dist))
        self.check_for_error(self.read_line())
        return new_positions

    def move_absolute(self, move_pos: dict[int, float]) -> dict[int, float] | None:
        total_distance = math.sqrt(sum(
            (pos - self._current_positions[axis]) ** 2
            for axis, pos in move_pos.items()
        ))

        now = time.time()
        self._start_positions = self._current_positions.copy()
        self._last_move_time = now
        self._move_duration = total_distance / self._velocity if self._velocity > 0 else 0.5
        self._move_duration = max(self._move_duration, 0.15)
        self._is_moving = True

        self._target_positions.update(move_pos)

        if hasattr(self, '_simulator_window'):
            self._simulator_window.syncMovement(
                self._start_positions,
                self._target_positions,
                self._move_duration,
                self._last_move_time
            )

        cmd = self.format_axis_command("G00", move_pos)
        self.write_line(cmd)
        self.check_for_error(self.read_line())
        self._update_motion
        return move_pos

    def home(self, axes: list[int]) -> dict[int, float]:
        home_positions = {axis: 0.0 for axis in axes}
        self.move_absolute(home_positions)
        return home_positions
    
    def get_current_positions(self) -> tuple[float, ...]:
        return tuple(self._current_positions[i] for i in range(len(self._current_positions)))

    def get_target_positions(self) -> tuple[float, ...]:
        return tuple(self._target_positions[i] for i in range(len(self.axis_names)))
    
    def is_moving(self) -> bool:
        if self._is_moving:
            elapsed = time.time() - self._last_move_time
            if elapsed < self._move_duration:
                self._update_motion()
                return True
            self._is_moving = False
            self._current_positions.update(self._target_positions)
        return False

    def get_endstop_minimums(self) -> tuple[float, ...]:
        self.write_line("E00-?")
        return tuple(float(p.strip("XYZW")) for p in self.check_for_error(self.read_line()).split())

    def get_endstop_maximums(self) -> tuple[float, ...]:
        self.write_line("E00+?")
        return tuple(float(p.strip("XYZW")) for p in self.check_for_error(self.read_line()).split())