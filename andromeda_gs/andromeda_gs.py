import sys
import os
import re
import time
import numpy as np
import pandas as pd
import matplotlib as mpl
from PyQt6 import QtCore, QtWidgets, QtGui
from gsmw import Ui_MainWindow
import pyqtgraph as pg
import deserialize


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Initialize the main window and set up UI elements.
    """

    def __init__(self):
        # initializing GUI window
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # initializing DataHandler class from deserialize.py
        self.handler = deserialize.DataHandler()

        # setting up variables
        self.connect = 0
        self.status = ""
        self.collect_data = 0
        self.log_message = ""
        self.autosave = 0
        self.autosave_text = ""
        self.output = None
        self.converted = None
        self.data_dict = {}

        # setting icon
        self.icon_path = os.path.join(
            os.path.dirname(__file__), "images", "meatball.png"
        )
        self.setWindowIcon(QtGui.QIcon("telepy.png"))

        # setting window name
        self.setWindowTitle("Andromeda Ground Station")
        pg.setConfigOptions(antialias=True)

        # setting up plots
        plot_LUT = {
            "bar_alt": ["Plot1", "m"],
            "kf_alt": ["Plot1", "g"],
            "trigger_alt": ["Plot1", "b"],
            "kf_vel": ["Plot2", "b"],
            "Int_vel": ["Plot2", "r"],
            "trigger_vel": ["Plot2", "g"],
            "x_accel": ["Plot4", "y"],
            "y_accel": ["Plot4", "r"],
            "z_accel": ["Plot4", "m"],
            "x_gyr": ["Plot5", "y"],
            "y_gyr": ["Plot5", "r"],
            "z_gyr": ["Plot5", "m"],
            "x_ang": ["Plot6", "y"],
            "y_ang": ["Plot6", "r"],
            "z_ang": ["Plot6", "m"],
            "temp": ["Plot3", "y"],
        }

        self.ui.Plot1.addLegend()
        self.ui.Plot1.setTitle("Altitude", color=[85, 170, 255], size="12pt")
        self.ui.Plot2.addLegend()
        self.ui.Plot2.setTitle("Velocity", color=[85, 170, 255], size="12pt")
        self.ui.Plot3.addLegend()
        self.ui.Plot3.setTitle("Temperature", color=[85, 170, 255], size="12pt")
        self.ui.Plot4.addLegend()
        self.ui.Plot4.setTitle("Linear Accel", color=[85, 170, 255], size="12pt")
        self.ui.Plot5.addLegend()
        self.ui.Plot5.setTitle("Angular Accel", color=[85, 170, 255], size="12pt")
        self.ui.Plot6.addLegend()
        self.ui.Plot6.setTitle("Orientation", color=[85, 170, 255], size="12pt")

        for i in range(len(plot_LUT)):
            data_series = list(plot_LUT.keys())[i]
            plot_widget = plot_LUT[data_series][0]
            series_color = pg.mkPen(color=plot_LUT[data_series][1], width=5)

            setattr(
                self.ui,
                data_series,
                getattr(self.ui, plot_widget).plot(name=data_series, pen=series_color),
            )

        # button color changes when hovering!
        self.ui.connect_toggle.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.ui.connect_toggle.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(100,100,100);
                border-radius: 5px;
                padding: 1px;
                color: white;
                font-size: 8 px;
            }

            QPushButton:hover {
                background-color: rgb(150,150,150);
            }
            """
        )

        self.ui.mission_start_toggle.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.ui.mission_start_toggle.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(100,100,100);
                border-radius: 5px;
                padding: 1px;
                color: white;
                font-size: 8 px;
            }
            
            QPushButton:hover {
                background-color: rgb(150,150,150);
            }
            """
        )

        self.ui.save_data.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.ui.save_data.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(100,100,100);
                border-radius: 5px;
                padding: 1px;
                color: white;
                font-size: 8 px;
            }
            
            QPushButton:hover {
                background-color: rgb(150,150,150);
            }
            """
        )

        self.ui.clear_data.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.ui.clear_data.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(100,100,100);
                border-radius: 5px;
                padding: 1px;
                color: white;
                font-size: 8 px;
            }
            
            QPushButton:hover {
                background-color: rgb(150,150,150);
            }
            """
        )

        self.ui.autosave_toggle.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.ui.autosave_toggle.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(100,100,100);
                border-radius: 5px;
                padding: 1px;
                color: white;
                font-size: 8 px;
            }
            
            QPushButton:hover {
                background-color: rgb(150,150,150);
            }
            """
        )

        # once button is clicked...
        self.ui.connect_toggle.clicked.connect(self.connect_to_server)
        self.ui.mission_start_toggle.clicked.connect(self.toggle_record_data)

        self.ui.autosave_toggle.clicked.connect(self.toggle_autosave)

    # button functions
    def connect_to_server(self):
        if self.connect == 0:
            self.status = self.handler.establish_connection()
            if (
                self.status == "Connected"
                or self.status == "Connected (no initial data)"
            ):
                self.connect = 1
                self.ui.log_entry.appendPlainText(self.status)
                self.ui.connect_toggle.setText("Disconnect")
            else:
                self.ui.log_entry.appendPlainText(self.status)
        elif self.connect == 1:
            self.status = self.handler.disconnect()
            if self.status == "Disconnected":
                self.connect = 0
                self.ui.log_entry.appendPlainText(self.status)
                self.ui.connect_toggle.setText("Connect")
            else:
                self.ui.log_entry.appendPlainText(self.status)

    def toggle_record_data(self):
        if self.collect_data == 0 and self.connect == 1:
            self.log_message = "Data collection started"
            self.collect_data = 1
            self.ui.log_entry.appendPlainText(self.log_message)
            self.ui.mission_start_toggle.setText("Stop Recording")
        elif self.collect_data == 0 and self.connect == 0:
            self.log_message = "No connection established"
            self.ui.log_entry.appendPlainText(self.log_message)
        else:
            self.log_message = "Data collection stopped"
            self.collect_data = 0
            self.ui.log_entry.appendPlainText(self.log_message)
            self.ui.mission_start_toggle.setText("Start Recording")

    def toggle_autosave(self):
        if self.autosave == 0:
            self.autosave = 1
            self.ui.autosave_toggle.setText("Auto Save: On")
        else:
            self.autosave = 0
            self.ui.autosave_toggle.setText("Auto Save: Off")

    def save_recorded_data(self):
        pass

    def clear_recorded_data(self):
        pass

    def fetch_data(self):
        """
        Receives data packet and formats it into a dictionary where the values
        can be displayed in the GUI each update tick.
        """
        self.handler.receive_data()
        self.output = self.handler.split_data_list()
        self.converted = self.handler.convert_to_float(self.output)
        self.data_dict = deserialize.float_to_dict(self.converted)

    def updated_display(self):
        """
        Updates every element of the GUI.
        """
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
