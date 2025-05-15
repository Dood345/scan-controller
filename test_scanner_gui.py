import sys
import numpy as np
import time
import traceback
from PySide6.QtCore import QTimer, Slot, Qt, QThread, Signal
from PySide6.QtGui import QCloseEvent, QMouseEvent, QWheelEvent, QPainter, QPen, QPaintEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                              QVBoxLayout, QWidget, QMessageBox, QFormLayout,
                              QDoubleSpinBox, QComboBox, QLabel, QGroupBox,
                              QSizePolicy, QScrollArea, QSpinBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from gui.scanner_qt import ScannerQt
from gui.ui_scanner import Ui_MainWindow
from gui.qt_util import QPluginSetting
from scanner.plugin_setting import PluginSettingString, PluginSettingFloat, PluginSettingInteger
from scanner.probe_simulator import ProbeSimulator

class PlotUpdater(QThread):
    update_signal = Signal(float, bool)

    def __init__(self, update_function):
        super().__init__()
        self.update_function = update_function
        self.active = True
        self.value = 0
        self.initial = False

    def run(self):
        while self.active:
            try:
                self.update_signal.emit(self.value, self.initial)
                self.msleep(50)
            except Exception as e:
                self.active = False

    def stop(self):
        self.active = False
        self.wait()

class PositionDrawer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.desiredX_norm = 0.5
        self.desiredY_norm = 0.5
        self.currentX_norm = 0.5
        self.currentY_norm = 0.5

    def paintEvent(self, event: QPaintEvent) -> None:
        squareSize = min(event.rect().width(), event.rect().height())
        qp = QPainter(self)
        qp.drawRect(0, 0, squareSize - 1, squareSize - 1)
        desiredX = self.desiredX_norm * squareSize
        desiredY = (1 - self.desiredY_norm) * squareSize
        qp.setPen(QPen(Qt.GlobalColor.black, 1))
        qp.drawEllipse(int(desiredX) - 6, int(desiredY) - 6, 12, 12)
        currentX = self.currentX_norm * squareSize
        currentY = (1 - self.currentY_norm) * squareSize
        qp.setPen(QPen(Qt.GlobalColor.darkCyan, 1))
        qp.setBrush(Qt.GlobalColor.darkCyan)
        qp.drawEllipse(int(currentX) - 4, int(currentY) - 4, 8, 8)

class ConnectThread(QThread):
    connect_finished = Signal(bool)
    connect_error = Signal(str)

    def __init__(self, controller, max_retries=3, controller_type="motion"):
        super().__init__()
        self.controller = controller
        self.max_retries = max_retries
        self.controller_type = controller_type

    def run(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                self.controller.connect()
                if not self.controller.is_connected():
                    raise RuntimeError(f"{self.controller_type.capitalize()} connection failed immediately after connect")
                
                self.connect_finished.emit(True)
                return

            except (ConnectionError, TimeoutError, RuntimeError) as e:
                attempt += 1
                if attempt == self.max_retries:
                    self.connect_error.emit(f"Failed after {self.max_retries} attempts: {str(e)}")
                self.msleep(1000)
            except Exception as e:
                self.connect_error.emit(str(e))
                return

class ScanThread(QThread):
    scan_finished = Signal()
    scan_error = Signal(str)
    update_target = Signal(float, float)
    update_data = Signal(int, tuple, list)

    def __init__(self, scanner, scan_order, x_dim, y_dim, x_step, y_step, start_position):
        super().__init__()
        self.scanner = scanner
        self.scan_order = scan_order
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.x_step = x_step
        self.y_step = y_step
        self.start_position = start_position
        self._pause = False
        self._stop = False

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            if not self.scanner.motion_controller.is_connected():
                raise ConnectionError("Motion controller not connected")
            if not self.scanner.probe_controller.is_connected():
                raise ConnectionError("Probe controller not connected")

            self.scanner.motion_controller.move_absolute({0: 0, 1: 0})
            self.update_target.emit(0, 0)
            while self.scanner.motion_controller.is_moving():
                QThread.msleep(20)
            QThread.msleep(100)

            if self.start_position == "Center":
                x_start = -self.x_dim / 2
                y_start = -self.y_dim / 2
            else:
                x_start = 0
                y_start = 0

            self.update_target.emit(x_start, y_start)
            self.scanner.motion_controller.move_absolute({0: x_start, 1: y_start})
            while self.scanner.motion_controller.is_moving():
                QThread.msleep(10)
            QThread.msleep(100)

            x_end = x_start + self.x_dim
            y_end = y_start + self.y_dim

            x_positions = list(np.arange(x_start, x_end + self.x_step / 2, self.x_step))
            y_positions = list(np.arange(y_start, y_end + self.y_step / 2, self.y_step))

            if self.scan_order == "YX":
                x_positions, y_positions = y_positions, x_positions

            for i, y in enumerate(y_positions):
                row = x_positions if i % 2 == 0 else reversed(x_positions)
                for x in row:
                    while self._pause and not self._stop:
                        QThread.msleep(100)
                    if self._stop:
                        return

                    self.update_target.emit(x, y)
                    self.scanner.motion_controller.move_absolute({0: x, 1: y})

                    while self.scanner.motion_controller.is_moving():
                        QThread.msleep(10)

                    data = self.scanner.probe_controller.scan_read_measurement(0, (x, y))
                    self.update_data.emit(0, (x, y), data)

            self.scan_finished.emit()
        except (ConnectionError, TimeoutError, ValueError) as e:
            self.scan_error.emit(str(e))
        except Exception as e:
            self.scan_error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.resize(1094, 618)
        self.setMinimumSize(1094, 618)

        self.ui.z_axis_slider.setRange(-300, 300)
        self.ui.z_axis_slider.setValue(0)

        self._scan_paused = False

        self.drawPanelXY = PositionDrawer()

        if hasattr(self.ui, 'gridLayoutWidget_6') and self.ui.gridLayoutWidget_6:
            self.ui.gridLayoutWidget_6.layout().addWidget(self.drawPanelXY)
        else:
            raise RuntimeError("gridLayoutWidget_6 not found in the UI")

        self.ui.z_axis_slider.setMinimum(-300)
        self.ui.z_axis_slider.setMaximum(300)
        self.ui.z_axis_slider.setValue(0)

        self.scan_order = PluginSettingString("Scan Order", "XY")
        self.x_dim = PluginSettingFloat("X Dimension (mm)", 50.0, value_max=600)
        self.y_dim = PluginSettingFloat("Y Dimension (mm)", 50.0, value_max=600)
        self.x_step = PluginSettingFloat("X Step (mm)", 10.0)
        self.y_step = PluginSettingFloat("Y Step (mm)", 10.0)
        self.start_position = "Center"
        self.zoom_level = 1.0
        self.zoom_center = (0, 0)
        self.target_position = (0, 0)
        self.is_moving_state = False
        self.is_dragging = False
        self.last_mouse_pos = None
        self.last_positions = (0.0, 0.0, 0.0)
        self.plot_update_pending = False
        self.scan_data = []

        self.setup_configuration_area()

        self.scanner = ScannerQt()
        if hasattr(self.scanner.scanner.motion_controller, '_driver'):
            self.scanner.scanner.motion_controller._driver.command_map = {
                'get_position': 'G00?',
                'get_status': 'Status?',
                'move_absolute': 'G00',
                'move_relative': 'G01'
            }
        if self.scanner.scanner.probe_controller._probe is None:
            self.scanner.scanner.probe_controller._probe = ProbeSimulator()

        self.ui.xy_move_amount.setValue(10.0)

        self.setup_data_visualization()
        self.setup_scan_table_graph()

        self.plot_updater = PlotUpdater(self.update_table_plot)
        self.plot_updater.update_signal.connect(self._update_table_plot_handler)
        self.plot_updater.start()
        
        self.target_update_timer = QTimer()
        self.target_update_timer.setInterval(10)  
        self.target_update_timer.timeout.connect(self.update_target_plot)
        self.pending_target = None

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_motion_position)
        self.position_timer.start(20)  

        self.setup_connections()

        self.ui.xy_move_amount.valueChanged.emit(self.ui.xy_move_amount.value())
        self.ui.z_move_amount.valueChanged.emit(self.ui.z_move_amount.value())

        self.update_connection_status()

        self.show()
        QTimer.singleShot(100, lambda: self.update_table_plot(0, initial=True))

    def setup_configuration_area(self):
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.config_container = QWidget()
        self.config_layout = QVBoxLayout(self.config_container)

        if hasattr(self.ui, 'config_layout'):
            parent = self.ui.config_layout.parent()
            if parent and hasattr(parent, 'layout'):
                parent.layout().replaceWidget(self.ui.config_layout, self.config_scroll)
                self.ui.config_layout.deleteLater()

        self.config_scroll.setWidget(self.config_container)

    def setup_data_visualization(self):
        self.data_canvas = FigureCanvas(Figure(figsize=(6, 4), dpi=100))
        self.data_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.data_canvas.setMinimumSize(400, 300)  

        if self.ui.data_visualization.layout():
            QWidget().setLayout(self.ui.data_visualization.layout())  

        layout = QVBoxLayout(self.ui.data_visualization)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.data_canvas)
        self.ui.data_visualization.setLayout(layout)

        self.ui.main_layout.setColumnStretch(3, 2) 
        self.ui.main_layout.setColumnStretch(4, 2)  
        self.ui.main_layout.setRowStretch(0, 3)  

    def setup_scan_table_graph(self):
        if self.ui.scan_table_graph.layout():
            while self.ui.scan_table_graph.layout().count():
                item = self.ui.scan_table_graph.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        layout = QVBoxLayout(self.ui.scan_table_graph)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        fig = Figure(facecolor='none', figsize=(5, 5), dpi=100)
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        self.table_canvas = FigureCanvas(fig)
        self.table_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.table_canvas)
        self.ui.scan_table_graph.setVisible(True)

        self.table_canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table_canvas.setMouseTracking(True)
        self.table_canvas.mousePressEvent = self.table_mouse_press
        self.table_canvas.mouseMoveEvent = self.table_mouse_move
        self.table_canvas.mouseReleaseEvent = self.table_mouse_release
        self.table_canvas.wheelEvent = self.table_wheel_event

        self.ax = fig.add_subplot(111)
        self.ax.set_aspect('equal', adjustable='box')
        boundary_limit = 300
        self.default_xlim = (-boundary_limit, boundary_limit)
        self.default_ylim = (-boundary_limit, boundary_limit)

        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        self.ax.grid(False)

        boundary_x = [-boundary_limit, boundary_limit, boundary_limit, -boundary_limit, -boundary_limit]
        boundary_y = [-boundary_limit, -boundary_limit, boundary_limit, boundary_limit, -boundary_limit]
        self.boundary_line, = self.ax.plot(boundary_x, boundary_y, 'k-', linewidth=2, alpha=1)

        if self.start_position == "Center":
            rect_x = [-self.x_dim.value/2, self.x_dim.value/2, 
                      self.x_dim.value/2, -self.x_dim.value/2, -self.x_dim.value/2]
            rect_y = [-self.y_dim.value/2, -self.y_dim.value/2, 
                      self.y_dim.value/2, self.y_dim.value/2, -self.y_dim.value/2]
        else:
            rect_x = [0, self.x_dim.value, self.x_dim.value, 0, 0]
            rect_y = [0, 0, self.y_dim.value, self.y_dim.value, 0]
        self.scan_area_line, = self.ax.plot(rect_x, rect_y, 'r--', linewidth=1.5)

        self.current_pos_line, = self.ax.plot([], [], 'bo', markersize=5)
        self.target_pos_line, = self.ax.plot([], [], 'ko', markersize=8, fillstyle='none', alpha=0.7)

    def setup_connections(self):
        self.ui.xy_move_amount.valueChanged.connect(self.scanner.set_xy_move)
        self.ui.z_move_amount.valueChanged.connect(self.scanner.set_z_move)

        self.ui.x_plus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_x_plus))
        self.ui.x_minus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_x_minus))
        self.ui.y_plus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_y_plus))
        self.ui.y_minus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_y_minus))
        self.ui.z_plus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_z_plus))
        self.ui.z_minus_button.clicked.connect(lambda: self.handle_movement(self.scanner.clicked_move_z_minus))

        self.ui.home_x_button.clicked.connect(lambda: self.home_axis(0))
        self.ui.home_y_button.clicked.connect(lambda: self.home_axis(1))
        self.ui.home_z_button.clicked.connect(lambda: self.home_axis(2))

        self.ui.z_axis_slider.valueChanged.connect(self.handle_z_slider_move)

        self.ui.configure_motion_button.clicked.connect(self.configure_motion)
        self.ui.configure_probe_button.clicked.connect(self.configure_probe)
        self.ui.configure_pattern_button.clicked.connect(self.configure_pattern)
        self.ui.configure_file_button.clicked.connect(self.configure_file)

        self.ui.start_scan_button.clicked.connect(self.start_scan)
        self.ui.pause_scan_button.clicked.connect(self.toggle_scan_pause)

    def update_motion_position(self):
        try:
            motion_ctrl = self.scanner.scanner.motion_controller
            if motion_ctrl.is_connected():
                is_moving = motion_ctrl.is_moving()
                pos = motion_ctrl.get_current_positions()
                if pos:
                    self.handle_motion_update(is_moving, *pos[:3])
        except Exception:
            pass

    def toggle_scan_pause(self):
        if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
            if self._scan_paused:
                self.scan_thread.resume()
                self.ui.pause_scan_button.setText("Pause")
            else:
                self.scan_thread.pause()
                self.ui.pause_scan_button.setText("Resume")
            self._scan_paused = not self._scan_paused

    @Slot()
    def debounce_plot_update(self):
        try:
            self.plot_update_pending = False
            self.update_table_plot(0, initial=False)
            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except Exception as e:
            pass

    @Slot(bool, float, float, float)
    def handle_motion_update(self, is_moving, pos_x, pos_y, pos_z):
        try:
            self.is_moving_state = is_moving
            if self.last_positions == (pos_x, pos_y, pos_z):
                return
            self.last_positions = (pos_x, pos_y, pos_z)

            new_x_norm = (pos_x + 300) / 600
            new_y_norm = (1 - (pos_y + 300) / 600)
            if (abs(new_x_norm - self.drawPanelXY.currentX_norm) > 1e-6 or
                abs(new_y_norm - self.drawPanelXY.currentY_norm) > 1e-6):
                self.drawPanelXY.currentX_norm = new_x_norm
                self.drawPanelXY.currentY_norm = new_y_norm
                self.drawPanelXY.update()

            if self.ui.z_axis_slider.value() != int(pos_z):
                self.ui.z_axis_slider.blockSignals(True)
                self.ui.z_axis_slider.setValue(int(pos_z))
                self.ui.z_axis_slider.blockSignals(False)

            target_positions = self.scanner.scanner.motion_controller.get_target_positions()
            target_x = target_positions[0] if len(target_positions) > 0 else 0
            target_y = target_positions[1] if len(target_positions) > 1 else 0
            self.target_position = (target_x, target_y)

            self.update_table_plot(0, initial=False)

        except (ConnectionError, TimeoutError, ValueError):
            pass
        except Exception:
            pass


    def handle_movement(self, movement_function):
        try:
            if not self.scanner.scanner.motion_controller.is_connected():
                raise ConnectionError("Motion controller not connected")
            
            movement_function()  # Call the respective movement function first

            target_positions = self.scanner.scanner.motion_controller.get_target_positions()
            target_x = target_positions[0] if len(target_positions) > 0 else 0
            target_y = target_positions[1] if len(target_positions) > 1 else 0
            self.target_position = (target_x, target_y)

            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except (ConnectionError, TimeoutError, ValueError) as e:
            QMessageBox.warning(self, "Error", f"Movement error: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Movement error: {str(e)}")

    def handle_z_slider_move(self, value):
        try:
            if not self.scanner.scanner.motion_controller.is_connected():
                raise ConnectionError("Motion controller not connected")
            
            z_pos = float(value)
            self.scanner.scanner.motion_controller.move_absolute({2: z_pos})
            target_positions = self.scanner.scanner.motion_controller.get_target_positions()
            self.target_position = (target_positions[0], target_positions[1])
            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except (ConnectionError, TimeoutError, ValueError) as e:
            QMessageBox.warning(self, "Error", f"Z slider move error: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Z slider move error: {str(e)}")

    def table_mouse_press(self, event: QMouseEvent):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.last_mouse_pos = (event.position().x(), event.position().y())
                self.table_canvas.grabMouse()
        except Exception as e:
            pass

    def table_mouse_move(self, event: QMouseEvent):
        try:
            if self.is_dragging and self.last_mouse_pos:
                ax = self.ax
                current_pos = (event.position().x(), event.position().y())
                dx = current_pos[0] - self.last_mouse_pos[0]
                dy = current_pos[1] - self.last_mouse_pos[1]
                
                transform = ax.transData.inverted()
                data_dx, data_dy = transform.transform((dx, dy)) - transform.transform((0, 0))
                
                self.zoom_center = (self.zoom_center[0] - data_dx, self.zoom_center[1] - data_dy)
                
                self.last_mouse_pos = current_pos
                self.update_table_plot(0, initial=False)
        except Exception as e:
            pass

    def table_mouse_release(self, event: QMouseEvent):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = False
                self.last_mouse_pos = None
                self.table_canvas.releaseMouse()
        except Exception as e:
            pass

    def table_wheel_event(self, event: QWheelEvent):
        try:
            zoom_factor = 1.1
            if event.angleDelta().y() > 0:
                self.zoom_level *= zoom_factor 
            else:
                self.zoom_level /= zoom_factor  
            self.zoom_level = max(0.5, min(10.0, self.zoom_level))
            self.update_table_plot(0, initial=False)
            event.accept()
        except Exception as e:
            pass

    def update_table_plot(self, value, initial=False):
        try:
            if not hasattr(self.scanner.scanner.motion_controller, '_driver') or self.scanner.scanner.motion_controller._driver is None:
                return
                
            if self.start_position == "Center":
                rect_x = [-self.x_dim.value/2, self.x_dim.value/2, 
                          self.x_dim.value/2, -self.x_dim.value/2, -self.x_dim.value/2]
                rect_y = [-self.y_dim.value/2, -self.y_dim.value/2, 
                          self.y_dim.value/2, self.y_dim.value/2, -self.y_dim.value/2]
            else:
                rect_x = [0, self.x_dim.value, self.x_dim.value, 0, 0]
                rect_y = [0, 0, self.y_dim.value, self.y_dim.value, 0]
            self.scan_area_line.set_data(rect_x, rect_y)
            
            if self.scanner.scanner.motion_controller.is_connected():
                pos_x, pos_y, pos_z = self.last_positions
                self.current_pos_line.set_data([pos_x], [pos_y])
                self.target_pos_line.set_data([self.target_position[0]], [self.target_position[1]])
                self.table_canvas.draw_idle()
                
                if initial:
                    self.zoom_center = (pos_x, pos_y)
            else:
                self.current_pos_line.set_data([], [])
                self.target_pos_line.set_data([self.target_position[0]], [self.target_position[1]])
            
            if self.zoom_level != 1.0:
                zoom_width = (self.default_xlim[1] - self.default_xlim[0]) / self.zoom_level
                zoom_height = (self.default_ylim[1] - self.default_ylim[0]) / self.zoom_level
                x_min = self.zoom_center[0] - zoom_width / 2
                x_max = self.zoom_center[0] + zoom_width / 2
                y_min = self.zoom_center[1] - zoom_height / 2
                y_max = self.zoom_center[1] + zoom_height / 2
                self.ax.set_xlim(x_min, x_max)
                self.ax.set_ylim(y_min, y_max)
            else:
                self.ax.set_xlim(self.default_xlim)
                self.ax.set_ylim(self.default_ylim)

            if self.plot_update_pending:
                return
            self.plot_update_pending = True
            QTimer.singleShot(30, self.debounce_plot_update)

            self.table_canvas.draw_idle()
        except Exception as e:
            pass

    def _update_table_plot_handler(self, value, initial):
        try:
            self.update_table_plot(value, initial)
        except Exception as e:
            pass

    def update_target_position(self, x, y):
        try:
            self.pending_target = (float(x), float(y))
            if not self.target_update_timer.isActive():
                self.target_update_timer.start()
        except Exception as e:
            pass

    def configure_motion(self):
        try:
            self.clear_config_layout()
            controller = self.scanner.scanner.motion_controller
            driver = controller._driver
            
            if hasattr(driver, 'number_of_axes') and driver.number_of_axes.value == 0:
                driver.number_of_axes.value = 3
            
            if hasattr(driver, 'port') and driver.port.value < 1024:
                driver.port.value = 5555
            
            self.set_configuration_settings(
                driver,
                controller.is_connected(),
                self.connect_motion,
                self.disconnect_motion
            )
        except (AttributeError, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Motion config error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Motion config error: {str(e)}")

    def configure_probe(self):
        try:
            self.clear_config_layout()
            controller = self.scanner.scanner.probe_controller
            probe = controller._probe
            
            if not hasattr(probe, 'settings_pre_connect'):
                probe.settings_pre_connect = []
            if not hasattr(probe, 'settings_post_connect'):
                probe.settings_post_connect = []
            
            self.set_configuration_settings(
                probe,
                controller.is_connected(),
                self.connect_probe,
                self.disconnect_probe
            )
        except (AttributeError, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Probe config error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Probe config error: {str(e)}")

    def configure_pattern(self):
        try:
            self.clear_config_layout()
            
            group_box = QGroupBox("Scan Pattern Settings")
            layout = QFormLayout()

            self.x_dim_edit = QDoubleSpinBox()
            self.x_dim_edit.setValue(self.x_dim.value)
            self.x_dim_edit.setRange(0.1, 600)
            self.x_dim_edit.valueChanged.connect(self.update_scan_dimensions)
            layout.addRow("X Dimension (mm):", self.x_dim_edit)
            
            self.y_dim_edit = QDoubleSpinBox()
            self.y_dim_edit.setValue(self.y_dim.value)
            self.y_dim_edit.setRange(0.1, 600)
            self.y_dim_edit.valueChanged.connect(self.update_scan_dimensions)
            layout.addRow("Y Dimension (mm):", self.y_dim_edit)
            
            self.x_step_edit = QDoubleSpinBox()
            self.x_step_edit.setValue(self.x_step.value)
            self.x_step_edit.setRange(0.1, 100)
            self.x_step_edit.valueChanged.connect(self.update_scan_dimensions)
            layout.addRow("X Step (mm):", self.x_step_edit)
            
            self.y_step_edit = QDoubleSpinBox()
            self.y_step_edit.setValue(self.y_step.value)
            self.y_step_edit.setRange(0.1, 100)
            self.y_step_edit.valueChanged.connect(self.update_scan_dimensions)
            layout.addRow("Y Step (mm):", self.y_step_edit)
            
            self.scan_order_combo = QComboBox()
            self.scan_order_combo.addItems(["XY", "YX"])
            self.scan_order_combo.setCurrentText(self.scan_order.value)
            self.scan_order_combo.currentTextChanged.connect(self.update_scan_dimensions)
            layout.addRow("Scan Order:", self.scan_order_combo)

            self.start_pos_combo = QComboBox()
            self.start_pos_combo.addItems(["Center", "Corner"])
            self.start_pos_combo.setCurrentText(self.start_position)
            self.start_pos_combo.currentTextChanged.connect(self.update_start_position)
            layout.addRow("Starting Position:", self.start_pos_combo)
            
            group_box.setLayout(layout)
            self.config_layout.addWidget(group_box)
            self.config_layout.addStretch()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Pattern config error: {str(e)}")

    def update_scan_dimensions(self):
        try:
            self.x_dim.value = self.x_dim_edit.value()
            self.y_dim.value = self.y_dim_edit.value()
            self.x_step.value = self.x_step_edit.value()
            self.y_step.value = self.y_step_edit.value()
            self.scan_order.value = self.scan_order_combo.currentText()
            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except Exception as e:
            pass

    def update_start_position(self, position):
        try:
            self.start_position = position
            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except Exception as e:
            pass

    def update_target_plot(self):
        if self.pending_target is not None:
            self.target_position = self.pending_target
            self.update_table_plot(0, initial=False)
            self.pending_target = None
        if not self.target_update_timer.isActive():
            self.target_update_timer.start()
        self.target_update_timer.stop()

    def configure_file(self):
        try:
            self.clear_config_layout()
            QMessageBox.information(self, "Info", "File configuration placeholder")
        except Exception as e:
            pass

    def set_configuration_settings(self, plugin, connected, connect_func, disconnect_func):
        try:
            if not hasattr(plugin, 'settings_pre_connect'):
                plugin.settings_pre_connect = []
            if not hasattr(plugin, 'settings_post_connect'):
                plugin.settings_post_connect = []
                
            group = QGroupBox("Configuration Settings")
            form = QFormLayout()
            
            settings = plugin.settings_post_connect if connected else plugin.settings_pre_connect
            
            for setting in settings:
                if isinstance(setting, PluginSettingInteger) and setting.display_label == "Port Number":
                    widget = QSpinBox()
                    widget.setRange(1024, 65535)
                    widget.setValue(setting.value)
                    widget.valueChanged.connect(lambda value: setattr(setting, 'value', value))
                else:
                    widget = QPluginSetting(setting)
                form.addRow(setting.display_label, widget)
            
            btn = QPushButton("Disconnect" if connected else "Connect")
            btn.clicked.connect(disconnect_func if connected else connect_func)
            form.addRow(btn)
            
            group.setLayout(form)
            self.config_layout.addWidget(group)
            self.config_layout.addStretch()
        except Exception as e:
            pass

    def clear_config_layout(self):
        try:
            while self.config_layout.count():
                item = self.config_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        except Exception as e:
            pass

    def connect_motion(self):
        try:
            self.connect_thread = ConnectThread(self.scanner.scanner.motion_controller, max_retries=3, controller_type="motion")
            self.connect_thread.connect_finished.connect(self.handle_connect_finished)
            self.connect_thread.connect_error.connect(self.handle_connect_error)
            self.connect_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Motion connect error: {str(e)}")

    def disconnect_motion(self):
        try:
            self.scanner.scanner.motion_controller.disconnect()
            self.update_connection_status()
            self.configure_motion()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Disconnect motion error: {str(e)}")

    def connect_probe(self):
        try:
            self.connect_thread = ConnectThread(self.scanner.scanner.probe_controller, max_retries=3, controller_type="probe")
            self.connect_thread.connect_finished.connect(self.handle_connect_finished)
            self.connect_thread.connect_error.connect(self.handle_connect_error)
            self.connect_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Probe connect error: {str(e)}")

    def disconnect_probe(self):
        try:
            self.scanner.scanner.probe_controller.disconnect()
            self.update_connection_status()
            self.configure_probe()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Disconnect probe error: {str(e)}")

    @Slot(bool)
    def handle_connect_finished(self, success):
        try:
            if success:
                self.update_connection_status()
                if self.connect_thread.controller_type == "motion":
                    self.configure_motion()
                else:
                    self.configure_probe()
                self.ui.z_axis_slider.setValue(0)
                self.plot_updater.value = 0
                self.plot_updater.initial = False
            else:
                QMessageBox.critical(self, "Error", f"{ self.connect_thread.controller_type.capitalize()} connect failed unexpectedly")
        except Exception as e:
            pass

    @Slot(str)
    def handle_connect_error(self, error_message):
        try:
            QMessageBox.critical(self, "Error", f"{self.connect_thread.controller_type.capitalize()} connect error: {error_message}")
        except Exception as e:
            pass

    def update_connection_status(self):
        try:
            motion_connected = self.scanner.scanner.motion_controller.is_connected()
            probe_connected = self.scanner.scanner.probe_controller.is_connected()
            
            self.ui.motion_connected_checkbox.setChecked(motion_connected)
            self.ui.checkBox.setChecked(probe_connected)
        except Exception as e:
            pass

    def home_axis(self, axis):
        try:
            if not self.scanner.scanner.motion_controller.is_connected():
                raise ConnectionError("Motion controller not connected")
            
            self.scanner.scanner.motion_controller.home([axis])
            if axis == 0:
                self.target_position = (0, self.target_position[1] if self.target_position else 0)
            elif axis == 1:
                self.target_position = (self.target_position[0] if self.target_position else 0, 0)
            self.plot_updater.value = 0
            self.plot_updater.initial = False
        except (ConnectionError, TimeoutError, ValueError) as e:
            QMessageBox.warning(self, "Error", f"Homing error: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Homing error: {str(e)}")

    def start_scan(self):
        try:
            if not self.scanner.scanner.motion_controller.is_connected():
                raise ConnectionError("Motion controller not connected")
            if not self.scanner.scanner.probe_controller.is_connected():
                raise ConnectionError("Probe controller not connected")
            
            self.ui.start_scan_button.setEnabled(False)
            self.scan_data = []
            self.data_canvas.figure.clear()
            self.data_canvas.draw_idle()
            
            self.scan_thread = ScanThread(
                self.scanner.scanner,
                self.scan_order.value,
                self.x_dim.value,
                self.y_dim.value,
                self.x_step.value,
                self.y_step.value,
                self.start_position
            )
            self.scan_thread.scan_finished.connect(self.handle_scan_finished, Qt.ConnectionType.QueuedConnection)
            self.scan_thread.scan_error.connect(self.handle_scan_error, Qt.ConnectionType.QueuedConnection)
            self.scan_thread.update_target.connect(self.update_target_position, Qt.ConnectionType.QueuedConnection)
            self.scan_thread.update_data.connect(self.update_data_plot, Qt.ConnectionType.QueuedConnection)
            self.scanner.scanner.set_update_target_callback(self.update_target_position)
            self.scanner.scanner.set_update_data_callback(self.emit_scan_data)
            self.scan_thread.start()
        except (ConnectionError, TimeoutError, ValueError) as e:
            self.ui.start_scan_button.setEnabled(False)
            QMessageBox.critical(self, "Error", f"Scan start error: {str(e)}")
        except Exception as e:
            self.ui.start_scan_button.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Scan start error: {str(e)}")

    def emit_scan_data(self, index, position, data):
        try:
            self.scan_thread.update_data.emit(index, position, data)
        except Exception as e:
            pass

    @Slot(int, tuple, list)
    @Slot(int, tuple, list)
    def update_data_plot(self, index, position, data):
        try:
            if data:
                self.scan_data.append((position, data))
            
            fig = self.data_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            fig.subplots_adjust(left=0.15, right=0.75, top=0.9, bottom=0.25)
            
            probe = self.scanner.scanner.probe_controller._probe
            if hasattr(probe, 'get_xaxis_coords'):
                freqs = probe.get_xaxis_coords()
                for pos, data_point in self.scan_data:
                    for i, channel_data in enumerate(data_point):
                        ax.plot(freqs, channel_data, linewidth=0.8)

                ax.set_xlabel("") 
                ax.set_ylabel("") 
                
                ax.tick_params(axis='both', labelsize=6)  
            
            self.data_canvas.draw_idle()
        except Exception as e:
            pass

    @Slot()
    def handle_scan_finished(self):
        try:
            self.ui.start_scan_button.setEnabled(True)
        except Exception as e:
            pass

    @Slot(str)
    def handle_scan_error(self, error_message):
        try:
            self.ui.start_scan_button.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to run scan: {error_message}")
        except Exception as e:
            pass

    def plot_data(self):
        try:
            fig = self.data_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            fig.subplots_adjust(left=0.3, right=0.95, top=0.95, bottom=0.25)
            
            probe = self.scanner.scanner.probe_controller._probe
            if hasattr(probe, 'get_xaxis_coords'):
                freqs = probe.get_xaxis_coords()
                data = probe.scan_read_measurement(0, (0, 0))
                if data:
                    for i, channel_data in enumerate(data):
                        ax.plot(freqs, channel_data, label=f"Channel {i+1}")
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
                    ax.set_xlabel(f"Frequency ({probe.get_xaxis_units()})")
                    ax.set_ylabel("Amplitude")
            self.data_canvas.draw_idle()
        except Exception as e:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self.plot_updater.stop()
            if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
                self.scan_thread.quit()
                self.scan_thread.wait()
            if hasattr(self, 'connect_thread') and self.connect_thread.isRunning():
                self.connect_thread.quit()
                self.connect_thread.wait()
            self.scanner.close()
            super().closeEvent(event)
        except Exception as e:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())