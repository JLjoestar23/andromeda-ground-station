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
import receive


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Initialize the main window and set up UI elements.
    """

    def __init__(self):
        # initializing GUI window
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # setting up variables
        self.connect = 0
        self.status = "Disconnected"
        self.collect_data = 0
        self.log_message = ""
        self.autosave = 0
        self.autosave_text = ""
        self.output = None
        self.converted = None
        self.data_dict = {}

        # initializing timer object
        self.status_timer = QtCore.QTimer()


        # setting icon
        self.icon_path = os.path.join(
            os.path.dirname(__file__), "images", "meatball.png"
        )
        self.setWindowIcon(QtGui.QIcon("telepy.png"))

        # setting window name
        self.setWindowTitle("Andromeda Ground Station")
        pg.setConfigOptions(antialias=True)

        # setting up plot legends
        plot_LUT = {
            "bar_alt": ["Plot1", "m"],
            "kf_alt": ["Plot1", "g"],
            #"trigger_alt": ["Plot1", "b"],
            "kf_vel": ["Plot2", "b"],
            #"Int_vel": ["Plot2", "r"],
            #"trigger_vel": ["Plot2", "g"],
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
        self.ui.connect_toggle.clicked.connect(self.connect_toggle)
        self.ui.mission_start_toggle.clicked.connect(self.toggle_record_data)
        self.ui.save_data.clicked.connect(self.save_recorded_data)
        self.ui.autosave_toggle.clicked.connect(self.toggle_autosave)

        # loop timer for display updates
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.fetch_data) # Update plots every 200 milliseconds
        self.update_timer.start(200)  # Check every 200 milliseconds 
        

    # button functions
    # connect_toggle handles basic connectivity logic, needs a lot of improvement
    def connect_toggle(self):
        """Toggle the WebSocket connection."""
        if self.connect == 0:  # If not connected, attempt to connect
            self.status = receive.connect_websocket()
            if self.status == "Connected":
                self.connect = 1  # Update the connection state
                self.ui.connect_toggle.setText("Disconnect")
            self.ui.log_entry.appendPlainText(self.status)
        elif self.connect == 1:  # If connected, disconnect
            self.status = receive.disconnect_websocket()
            self.connect = 0  # Update the connection state
            self.ui.connect_toggle.setText("Connect")
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
        Fetches data from the WebSocket server and formats it into a dictionary
        where the values can be displayed in the GUI each update tick.
        """
        # Retrieve the latest data from the WebSocket
        self.raw_data = receive.get_data()
        
        if self.raw_data is not None and isinstance(self.raw_data, dict):
            self.data_dict = self.raw_data  # Store the data in the class variable
            #self.ui.log_entry.appendPlainText(f"Received data: {self.data_dict}")
            #print(f"Received data: {self.data_dict}")
        # else:
        #     self.ui.log_entry.appendPlainText("No valid data received.")
            #print("No valid data received.")

    def update_display(self):
        """
        Updates every element of the GUI.
        """
        
    def update_plots(self):
        """
        Updates selected plot on the GUI.
        """

        self.data_dict = self.fetch_data()

        new_data = {
            "bar_alt": self.data_dict["message"],
            # "kf_alt": self.data_point,
            # "trigger_alt": self.data_point,
            # "kf_vel": self.data_point,
            # "Int_vel": self.data_point,
            # "trigger_vel": self.data_point,
            # "x_accel": self.data_point,
            # "y_accel": self.data_point,
            # "z_accel": self.data_point,
            # "x_gyr": self.data_point,
            # "y_gyr": self.data_point,
            # "z_gyr": self.data_point,
            # "x_ang": self.data_point,
            # "y_ang": self.data_point,
            # "z_ang": self.data_point,
            # "temp": self.data_point, 
        }

        # Maximum number of points to keep in the plot
        max_points = 50

        # Update each plot with the new data
        for self.data_dict, value in new_data.items():
            plot_item = getattr(self.ui, self.data_dict, None)
            if plot_item:
                # Append new data to the plot
                x_data, y_data = plot_item.getData()
                if x_data is None or y_data is None:
                    x_data, y_data = [], []
                x_data = list(x_data) + [time.time()]  # Use time as x-axis
                y_data = list(y_data) + [value]

                # Keep only the last max_points points
                x_data = x_data[-max_points:]
                y_data = y_data[-max_points:]

                # Update the plot with the trimmed data
                plot_item.setData(x=x_data, y=y_data)

    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
