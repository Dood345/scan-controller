# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_scanner.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGridLayout, QLabel, QLayout,
    QLineEdit, QMainWindow, QMenuBar, QProgressBar,
    QPushButton, QSizePolicy, QSlider, QStatusBar,
    QTabWidget, QTextEdit, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1094, 618)
        MainWindow.setAnimated(False)
        MainWindow.setDocumentMode(True)
        MainWindow.setTabShape(QTabWidget.TabShape.Triangular)
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName(u"central_widget")
        self.gridLayoutWidget_6 = QWidget(self.central_widget)
        self.gridLayoutWidget_6.setObjectName(u"gridLayoutWidget_6")
        self.gridLayoutWidget_6.setGeometry(QRect(10, 10, 1061, 561))
        self.main_layout = QGridLayout(self.gridLayoutWidget_6)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.line_3 = QFrame(self.gridLayoutWidget_6)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_3, 4, 2, 1, 1)

        self.scan_layout = QGridLayout()
        self.scan_layout.setSpacing(6)
        self.scan_layout.setObjectName(u"scan_layout")
        self.scan_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.scan_layout.setProperty(u"minimumSize", QSize(500, 200))
        self.time_elapsed_box = QLineEdit(self.gridLayoutWidget_6)
        self.time_elapsed_box.setObjectName(u"time_elapsed_box")
        self.time_elapsed_box.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.time_elapsed_box.sizePolicy().hasHeightForWidth())
        self.time_elapsed_box.setSizePolicy(sizePolicy)
        self.time_elapsed_box.setMinimumSize(QSize(100, 0))
        self.time_elapsed_box.setReadOnly(True)

        self.scan_layout.addWidget(self.time_elapsed_box, 2, 1, 1, 1)

        self.time_remaining_label = QLabel(self.gridLayoutWidget_6)
        self.time_remaining_label.setObjectName(u"time_remaining_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.time_remaining_label.sizePolicy().hasHeightForWidth())
        self.time_remaining_label.setSizePolicy(sizePolicy1)

        self.scan_layout.addWidget(self.time_remaining_label, 4, 0, 1, 1)

        self.start_scan_button = QPushButton(self.gridLayoutWidget_6)
        self.start_scan_button.setObjectName(u"start_scan_button")
        sizePolicy1.setHeightForWidth(self.start_scan_button.sizePolicy().hasHeightForWidth())
        self.start_scan_button.setSizePolicy(sizePolicy1)

        self.scan_layout.addWidget(self.start_scan_button, 0, 0, 1, 1)

        self.time_remaining_box = QLineEdit(self.gridLayoutWidget_6)
        self.time_remaining_box.setObjectName(u"time_remaining_box")
        sizePolicy.setHeightForWidth(self.time_remaining_box.sizePolicy().hasHeightForWidth())
        self.time_remaining_box.setSizePolicy(sizePolicy)
        self.time_remaining_box.setMinimumSize(QSize(100, 0))
        self.time_remaining_box.setReadOnly(True)

        self.scan_layout.addWidget(self.time_remaining_box, 4, 1, 1, 1)

        self.scan_description_box = QTextEdit(self.gridLayoutWidget_6)
        self.scan_description_box.setObjectName(u"scan_description_box")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.scan_description_box.sizePolicy().hasHeightForWidth())
        self.scan_description_box.setSizePolicy(sizePolicy2)
        self.scan_description_box.setMinimumSize(QSize(200, 50))

        self.scan_layout.addWidget(self.scan_description_box, 0, 1, 1, 1)

        self.scan_progress_bar = QProgressBar(self.gridLayoutWidget_6)
        self.scan_progress_bar.setObjectName(u"scan_progress_bar")
        sizePolicy.setHeightForWidth(self.scan_progress_bar.sizePolicy().hasHeightForWidth())
        self.scan_progress_bar.setSizePolicy(sizePolicy)
        self.scan_progress_bar.setMaximumSize(QSize(300, 16777215))
        self.scan_progress_bar.setValue(50)

        self.scan_layout.addWidget(self.scan_progress_bar, 1, 1, 1, 1)

        self.time_elapsed_label = QLabel(self.gridLayoutWidget_6)
        self.time_elapsed_label.setObjectName(u"time_elapsed_label")
        sizePolicy1.setHeightForWidth(self.time_elapsed_label.sizePolicy().hasHeightForWidth())
        self.time_elapsed_label.setSizePolicy(sizePolicy1)

        self.scan_layout.addWidget(self.time_elapsed_label, 2, 0, 1, 1)

        self.pause_scan_button = QPushButton(self.gridLayoutWidget_6)
        self.pause_scan_button.setObjectName(u"pause_scan_button")

        self.scan_layout.addWidget(self.pause_scan_button, 1, 0, 1, 1)


        self.main_layout.addLayout(self.scan_layout, 0, 6, 1, 1)

        self.z_move_layout = QGridLayout()
        self.z_move_layout.setObjectName(u"z_move_layout")
        self.z_move_layout.setProperty(u"minimumSize", QSize(150, 200))
        self.z_axis_slider = QSlider(self.gridLayoutWidget_6)
        self.z_axis_slider.setObjectName(u"z_axis_slider")
        self.z_axis_slider.setMinimumSize(QSize(20, 80))
        self.z_axis_slider.setMinimum(-300)
        self.z_axis_slider.setMaximum(300)
        self.z_axis_slider.setOrientation(Qt.Orientation.Vertical)
        self.z_axis_slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.z_axis_slider.setTickInterval(50000)

        self.z_move_layout.addWidget(self.z_axis_slider, 1, 1, 3, 1)

        self.z_axis_select = QComboBox(self.gridLayoutWidget_6)
        self.z_axis_select.setObjectName(u"z_axis_select")
        sizePolicy1.setHeightForWidth(self.z_axis_select.sizePolicy().hasHeightForWidth())
        self.z_axis_select.setSizePolicy(sizePolicy1)
        self.z_axis_select.setMinimumSize(QSize(80, 0))

        self.z_move_layout.addWidget(self.z_axis_select, 0, 0, 1, 1)

        self.z_move_amount = QDoubleSpinBox(self.gridLayoutWidget_6)
        self.z_move_amount.setObjectName(u"z_move_amount")
        sizePolicy1.setHeightForWidth(self.z_move_amount.sizePolicy().hasHeightForWidth())
        self.z_move_amount.setSizePolicy(sizePolicy1)
        self.z_move_amount.setMinimumSize(QSize(10, 20))
        self.z_move_amount.setMaximumSize(QSize(80, 16777215))
        self.z_move_amount.setDecimals(5)
        self.z_move_amount.setMinimum(-100000000000000000.000000000000000)
        self.z_move_amount.setMaximum(100000000000000000.000000000000000)
        self.z_move_amount.setValue(10.000000000000000)

        self.z_move_layout.addWidget(self.z_move_amount, 2, 0, 1, 1)

        self.z_plus_button = QPushButton(self.gridLayoutWidget_6)
        self.z_plus_button.setObjectName(u"z_plus_button")
        sizePolicy1.setHeightForWidth(self.z_plus_button.sizePolicy().hasHeightForWidth())
        self.z_plus_button.setSizePolicy(sizePolicy1)
        self.z_plus_button.setMaximumSize(QSize(80, 16777215))

        self.z_move_layout.addWidget(self.z_plus_button, 1, 0, 1, 1)

        self.z_minus_button = QPushButton(self.gridLayoutWidget_6)
        self.z_minus_button.setObjectName(u"z_minus_button")
        sizePolicy1.setHeightForWidth(self.z_minus_button.sizePolicy().hasHeightForWidth())
        self.z_minus_button.setSizePolicy(sizePolicy1)
        self.z_minus_button.setMaximumSize(QSize(80, 16777215))

        self.z_move_layout.addWidget(self.z_minus_button, 3, 0, 1, 1)

        self.home_z_button = QPushButton(self.gridLayoutWidget_6)
        self.home_z_button.setObjectName(u"home_z_button")
        self.home_z_button.setMaximumSize(QSize(80, 16777215))

        self.z_move_layout.addWidget(self.home_z_button, 4, 0, 1, 1)


        self.main_layout.addLayout(self.z_move_layout, 0, 1, 1, 1)

        self.xy_move_layout = QGridLayout()
        self.xy_move_layout.setObjectName(u"xy_move_layout")
        self.xy_move_layout.setProperty(u"minimumSize", QSize(350, 200))
        self.y_minus_button = QPushButton(self.gridLayoutWidget_6)
        self.y_minus_button.setObjectName(u"y_minus_button")
        sizePolicy1.setHeightForWidth(self.y_minus_button.sizePolicy().hasHeightForWidth())
        self.y_minus_button.setSizePolicy(sizePolicy1)
        self.y_minus_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.y_minus_button, 2, 1, 1, 1)

        self.xy_move_amount = QDoubleSpinBox(self.gridLayoutWidget_6)
        self.xy_move_amount.setObjectName(u"xy_move_amount")
        self.xy_move_amount.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.xy_move_amount.sizePolicy().hasHeightForWidth())
        self.xy_move_amount.setSizePolicy(sizePolicy1)
        self.xy_move_amount.setMinimumSize(QSize(10, 20))
        self.xy_move_amount.setMaximumSize(QSize(80, 16777215))
        self.xy_move_amount.setDecimals(5)
        self.xy_move_amount.setMinimum(-1000000000000000.000000000000000)
        self.xy_move_amount.setMaximum(1000000000000000.000000000000000)
        self.xy_move_amount.setValue(10.000000000000000)

        self.xy_move_layout.addWidget(self.xy_move_amount, 1, 1, 1, 1)

        self.home_y_button = QPushButton(self.gridLayoutWidget_6)
        self.home_y_button.setObjectName(u"home_y_button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.home_y_button.sizePolicy().hasHeightForWidth())
        self.home_y_button.setSizePolicy(sizePolicy3)
        self.home_y_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.home_y_button, 2, 2, 1, 1)

        self.y_plus_button = QPushButton(self.gridLayoutWidget_6)
        self.y_plus_button.setObjectName(u"y_plus_button")
        sizePolicy1.setHeightForWidth(self.y_plus_button.sizePolicy().hasHeightForWidth())
        self.y_plus_button.setSizePolicy(sizePolicy1)
        self.y_plus_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.y_plus_button, 0, 1, 1, 1)

        self.x_plus_button = QPushButton(self.gridLayoutWidget_6)
        self.x_plus_button.setObjectName(u"x_plus_button")
        self.x_plus_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.x_plus_button, 1, 2, 1, 1)

        self.home_x_button = QPushButton(self.gridLayoutWidget_6)
        self.home_x_button.setObjectName(u"home_x_button")
        self.home_x_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.home_x_button, 2, 0, 1, 1)

        self.x_minus_button = QPushButton(self.gridLayoutWidget_6)
        self.x_minus_button.setObjectName(u"x_minus_button")
        self.x_minus_button.setMaximumSize(QSize(80, 16777215))

        self.xy_move_layout.addWidget(self.x_minus_button, 1, 0, 1, 1)


        self.main_layout.addLayout(self.xy_move_layout, 0, 0, 1, 1)

        self.line_7 = QFrame(self.gridLayoutWidget_6)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.Shape.HLine)
        self.line_7.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_7, 3, 1, 1, 1)

        self.line_4 = QFrame(self.gridLayoutWidget_6)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_4, 4, 5, 1, 1)

        self.line_6 = QFrame(self.gridLayoutWidget_6)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.Shape.HLine)
        self.line_6.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_6, 3, 3, 1, 2)

        self.line_8 = QFrame(self.gridLayoutWidget_6)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.Shape.HLine)
        self.line_8.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_8, 3, 6, 1, 1)

        self.line_2 = QFrame(self.gridLayoutWidget_6)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_2, 0, 2, 1, 1)

        self.line = QFrame(self.gridLayoutWidget_6)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line, 3, 0, 1, 1)

        self.line_5 = QFrame(self.gridLayoutWidget_6)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.Shape.VLine)
        self.line_5.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout.addWidget(self.line_5, 0, 5, 1, 1)

        self.data_visualization = QWidget(self.gridLayoutWidget_6)
        self.data_visualization.setObjectName(u"data_visualization")
        sizePolicy3.setHeightForWidth(self.data_visualization.sizePolicy().hasHeightForWidth())
        self.data_visualization.setSizePolicy(sizePolicy3)
        self.data_visualization.setMinimumSize(QSize(150, 100))

        self.main_layout.addWidget(self.data_visualization, 0, 3, 1, 2)

        self.config_layout = QWidget(self.gridLayoutWidget_6)
        self.config_layout.setObjectName(u"config_layout")

        self.main_layout.addWidget(self.config_layout, 4, 3, 1, 2)

        self.settings_layout = QGridLayout()
        self.settings_layout.setObjectName(u"settings_layout")
        self.settings_layout.setProperty(u"minimumSize", QSize(150, 400))
        self.configure_file_button = QPushButton(self.gridLayoutWidget_6)
        self.configure_file_button.setObjectName(u"configure_file_button")
        self.configure_file_button.setCheckable(True)

        self.settings_layout.addWidget(self.configure_file_button, 3, 2, 1, 1)

        self.configure_motion_label = QLabel(self.gridLayoutWidget_6)
        self.configure_motion_label.setObjectName(u"configure_motion_label")
        sizePolicy3.setHeightForWidth(self.configure_motion_label.sizePolicy().hasHeightForWidth())
        self.configure_motion_label.setSizePolicy(sizePolicy3)
        self.configure_motion_label.setMinimumSize(QSize(80, 30))

        self.settings_layout.addWidget(self.configure_motion_label, 0, 0, 1, 1)

        self.configure_motion_button = QPushButton(self.gridLayoutWidget_6)
        self.configure_motion_button.setObjectName(u"configure_motion_button")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.configure_motion_button.sizePolicy().hasHeightForWidth())
        self.configure_motion_button.setSizePolicy(sizePolicy4)
        self.configure_motion_button.setCheckable(True)

        self.settings_layout.addWidget(self.configure_motion_button, 0, 2, 1, 1)

        self.configure_file_label = QLabel(self.gridLayoutWidget_6)
        self.configure_file_label.setObjectName(u"configure_file_label")
        self.configure_file_label.setMinimumSize(QSize(80, 30))
        self.configure_file_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.settings_layout.addWidget(self.configure_file_label, 3, 0, 1, 1)

        self.configure_probe_label = QLabel(self.gridLayoutWidget_6)
        self.configure_probe_label.setObjectName(u"configure_probe_label")
        self.configure_probe_label.setMinimumSize(QSize(80, 30))

        self.settings_layout.addWidget(self.configure_probe_label, 1, 0, 1, 1)

        self.configure_pattern_label = QLabel(self.gridLayoutWidget_6)
        self.configure_pattern_label.setObjectName(u"configure_pattern_label")
        self.configure_pattern_label.setMinimumSize(QSize(80, 30))

        self.settings_layout.addWidget(self.configure_pattern_label, 2, 0, 1, 1)

        self.configure_probe_button = QPushButton(self.gridLayoutWidget_6)
        self.configure_probe_button.setObjectName(u"configure_probe_button")
        self.configure_probe_button.setCheckable(True)

        self.settings_layout.addWidget(self.configure_probe_button, 1, 2, 1, 1)

        self.configure_pattern_button = QPushButton(self.gridLayoutWidget_6)
        self.configure_pattern_button.setObjectName(u"configure_pattern_button")
        self.configure_pattern_button.setCheckable(True)

        self.settings_layout.addWidget(self.configure_pattern_button, 2, 2, 1, 1)

        self.checkBox = QCheckBox(self.gridLayoutWidget_6)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setCheckable(False)

        self.settings_layout.addWidget(self.checkBox, 1, 1, 1, 1)

        self.motion_connected_checkbox = QCheckBox(self.gridLayoutWidget_6)
        self.motion_connected_checkbox.setObjectName(u"motion_connected_checkbox")
        sizePolicy4.setHeightForWidth(self.motion_connected_checkbox.sizePolicy().hasHeightForWidth())
        self.motion_connected_checkbox.setSizePolicy(sizePolicy4)
        self.motion_connected_checkbox.setCheckable(False)

        self.settings_layout.addWidget(self.motion_connected_checkbox, 0, 1, 1, 1)


        self.main_layout.addLayout(self.settings_layout, 4, 0, 1, 2)

        self.scan_table_graph = QWidget(self.gridLayoutWidget_6)
        self.scan_table_graph.setObjectName(u"scan_table_graph")

        self.main_layout.addWidget(self.scan_table_graph, 4, 6, 1, 1)

        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(4, 2)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(3, 2)
        self.main_layout.setColumnStretch(4, 2)
        self.main_layout.setColumnStretch(6, 4)
        MainWindow.setCentralWidget(self.central_widget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1094, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.time_remaining_label.setText(QCoreApplication.translate("MainWindow", u"Time Remaining", None))
        self.start_scan_button.setText(QCoreApplication.translate("MainWindow", u"Start Scan", None))
        self.time_elapsed_label.setText(QCoreApplication.translate("MainWindow", u"Time Elapsed", None))
        self.pause_scan_button.setText(QCoreApplication.translate("MainWindow", u"Pause", None))
        self.z_plus_button.setText(QCoreApplication.translate("MainWindow", u"Z+", None))
        self.z_minus_button.setText(QCoreApplication.translate("MainWindow", u"Z-", None))
        self.home_z_button.setText(QCoreApplication.translate("MainWindow", u"Z Home", None))
        self.y_minus_button.setText(QCoreApplication.translate("MainWindow", u"Y-", None))
        self.home_y_button.setText(QCoreApplication.translate("MainWindow", u"Y Home", None))
        self.y_plus_button.setText(QCoreApplication.translate("MainWindow", u"Y+", None))
        self.x_plus_button.setText(QCoreApplication.translate("MainWindow", u"X+", None))
        self.home_x_button.setText(QCoreApplication.translate("MainWindow", u"X Home", None))
        self.x_minus_button.setText(QCoreApplication.translate("MainWindow", u"X-", None))
        self.configure_file_button.setText(QCoreApplication.translate("MainWindow", u"Configure", None))
        self.configure_motion_label.setText(QCoreApplication.translate("MainWindow", u"Motion Control", None))
        self.configure_motion_button.setText(QCoreApplication.translate("MainWindow", u"Configure", None))
        self.configure_file_label.setText(QCoreApplication.translate("MainWindow", u"Scan File", None))
        self.configure_probe_label.setText(QCoreApplication.translate("MainWindow", u"Probe", None))
        self.configure_pattern_label.setText(QCoreApplication.translate("MainWindow", u"Scan Pattern", None))
        self.configure_probe_button.setText(QCoreApplication.translate("MainWindow", u"Configure", None))
        self.configure_pattern_button.setText(QCoreApplication.translate("MainWindow", u"Configure", None))
        self.checkBox.setText(QCoreApplication.translate("MainWindow", u"Connected", None))
        self.motion_connected_checkbox.setText(QCoreApplication.translate("MainWindow", u"Connected", None))
    # retranslateUi

