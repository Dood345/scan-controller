from PySide6.QtCore import QObject, Slot
from scanner.scanner import Scanner

class ScannerQt(QObject):
    xy_move: float
    z_move: float
    scanner: Scanner

    def __init__(self) -> None:
        super().__init__()
        self.xy_move = 0.0
        self.z_move = 0.0
        self.scanner = Scanner()

    def close(self) -> None:
        print("Closing Qt Scanner Object")
        self.scanner.close()

    @Slot(float)
    def set_xy_move(self, move_amount: float):
        self.xy_move = move_amount

    @Slot(float)
    def set_z_move(self, move_amount: float):
        self.z_move = move_amount

    @Slot()
    def clicked_move_x_plus(self):
        self.scanner.motion_controller.move_relative({0: self.xy_move})

    @Slot()
    def clicked_move_x_minus(self):
        self.scanner.motion_controller.move_relative({0: -self.xy_move})

    @Slot()
    def clicked_move_y_plus(self):
        self.scanner.motion_controller.move_relative({1: self.xy_move})

    @Slot()
    def clicked_move_y_minus(self):
        self.scanner.motion_controller.move_relative({1: -self.xy_move})

    @Slot()
    def clicked_move_z_plus(self):
        self.scanner.motion_controller.move_relative({2: self.z_move})

    @Slot()
    def clicked_move_z_minus(self):
        self.scanner.motion_controller.move_relative({2: -self.z_move})