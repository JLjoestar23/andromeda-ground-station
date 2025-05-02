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
from datetime import datetime


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
        

        # setting icons
        self.icon_path = os.path.join(
            os.path.dirname(__file__), "images", "meatball.png"
        )
        self.setWindowIcon(QtGui.QIcon(self.icon_path))

        # setting window name
        self.setWindowTitle("Andromeda Ground Station")
        pg.setConfigOptions(antialias=True)

        self.ui.log_entry.setReadOnly(True)  # Make the log entry read-only
        self.setup_plots()
        self.initialize_data_structures()
        
        

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
        self.ui.clear_data.clicked.connect(self.clear_recorded_data)

        # Initializing timer object
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.main_loop) # Update plots every 200 milliseconds
        self.update_timer.start(200)  # Check every 200 milliseconds 
        
    # general functions
    def main_loop(self): # need to figure out the exact architecture of this function
        # only fetch data if connected
        if self.connect == 1:
            self.fetch_data()
        
        # update the plots and display elements
        self.update_display()

        # autosave data to CSV file if autosave is enabled every 250 data points
        # clears the recorded data after saving
        if self.autosave == 1 and len(self.recorded_data) > 250:
            self.save_recorded_data()
            self.recorded_data = pd.DataFrame(columns=[
                'time', 'Accel_X', 'Accel_Y', 'Accel_Z', 
                'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temp',
                'Euler_X', 'Euler_Y', 'Euler_Z', 'Baro_Alt',
                'Longitude', 'Latitude', 'GPS_Alt', 'Phase',
                'Continuity', 'Voltage', 'Link_Strength',
                'KF_X', 'KF_Y', 'KF_Z', 'KF_VX', 'KF_VY', 'KF_VZ',
                'KF_Drag', 'Diagnostic_Message'
            ])

        
    def setup_plots(self):
        """Configure all plot widgets with proper settings"""
        color1 = (25,150,207) # Shade of Olin blue
        color2 = (207, 102, 25) # Orange for contrast
        color3 = (207, 25, 150) # Magenta for contrast

        self.plot_config = {
            'Plot1': {
                'title': 'Altitude',
                'vars': ['KF_Z'],
                'colors': [color1],
                'unit': 'm'
            },
            'Plot2': {
                'title': 'Velocity',
                'vars': ['KF_VX', 'KF_VY', 'KF_VZ'],
                'colors': [color1, color2, color3],
                'unit': 'm/s'
            },
            'Plot3': {
                'title': 'Orientation',
                'vars': ['Euler_X', 'Euler_Y', 'Euler_Z'],
                'colors': [color1, color2, color3],
                'unit': 'deg'
            },

            'Plot4': {
                'title': 'Linear Acceleration',
                'vars': ['Accel_X', 'Accel_Y', 'Accel_Z'],
                'colors': [color1, color2, color3],
                'unit': 'm/s²'
            },
            'Plot5': {
                'title': 'Angular Velocity',
                'vars': ['Gyro_X', 'Gyro_Y', 'Gyro_Z'],
                'colors': [color1, color2, color3],
                'unit': 'rad/s'
            },
            'Plot6': {
                'title': 'Temperature',
                'vars': ['Temp'],
                'colors': [color1],
                'unit': '°C'
            }
        }

        for plot_name, config in self.plot_config.items():
            plot_widget = getattr(self.ui, plot_name)
            plot_widget.clear()
            plot_widget.setTitle(f"{config['title']} ({config['unit']})", color=(214,230,237), size='12pt')
            plot_widget.addLegend()
            plot_widget.showGrid(x=True, y=True)
            
            config['curves'] = []
            for var, color in zip(config['vars'], config['colors']):
                curve = plot_widget.plot(pen=pg.mkPen(color, width=2), name=var)
                config['curves'].append(curve)

    def initialize_data_structures(self):
        """Initialize data storage structures"""

        # Initialize a Pandas DataFrame to store and save data for later use
        # This will be used to save data to a CSV file, *not for plotting*
        self.recorded_data = pd.DataFrame(columns=[
            'time', 'Accel_X', 'Accel_Y', 'Accel_Z', 
            'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temp',
            'Euler_X', 'Euler_Y', 'Euler_Z', 'Baro_Alt',
            'Longitude', 'Latitude', 'GPS_Alt', 'Phase',
            'Continuity', 'Voltage', 'Link_Strength',
            'KF_X', 'KF_Y', 'KF_Z', 'KF_VX', 'KF_VY', 'KF_VZ',
            'KF_Drag', 'Diagnostic_Message'
        ])

        self.idx = 0 # Index for plot testing
        # example arrays for testing
        self.time = []
        self.Ax = []
        self.Ay = []
        self.Az = []
        self.Gx = []
        self.Gy = []
        self.Gz = []
        self.Vx = []
        self.Vy = []
        self.Vz = []
        self.KFz = []
        self.T = []
        self.Ex = []
        self.Ey = []
        self.Ez = []


        self.max_points = 50 # Max number of data points to display in the plot

        # create empty arrays for each data variable that *will be plotted*
        # stored in a dictionary for easy access
        self.plot_data_dict = {key: [] for key in [
            'time', 'Accel_X', 'Accel_Y', 'Accel_Z', 
            'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temp',
            'Euler_X', 'Euler_Y', 'Euler_Z', 'Baro_Alt',
            'Longitude', 'Latitude', 'GPS_Alt', 'Phase',
            'Continuity', 'Voltage', 'Link_Strength',
            'KF_X', 'KF_Y', 'KF_Z', 'KF_VX', 'KF_VY', 'KF_VZ',
            'KF_Drag', 'Diagnostic_Message'
        ]}
        
        # Initialize flight phase labels and colors
        self.phase_labels = ["IDLE", "ARMED", "ASCENT", "APOGEE", "DECENT"]
        self.phase_colors = ["85, 156, 242", "232, 21, 21", "224, 104, 29", "214, 61, 217", "61, 217, 82"]

    def fetch_data(self):
        """Fetch new data and update buffers"""
        self.raw_data = receive.get_data()
        #print(self.raw_data)

        if self.raw_data is not None and self.collect_data:
            # Store in DataFrame if data is received
            new_row = pd.DataFrame([self.raw_data])
            self.recorded_data = pd.concat([self.recorded_data, new_row], ignore_index=True)

            # Append new data from raw_data to plot_data_dict
            for data in self.raw_data.keys():
                self.plot_data_dict[data].append(self.raw_data[data])
                self.plot_data_dict[data] = self.plot_data_dict[data][-self.max_points:]

    def update_plots(self, plot_name, x, y_dict):
        """
        Update a plot with multiple variables.
        """
        config = self.plot_config[plot_name]
        for i, var in enumerate(config['vars']):
            config['curves'][i].setData(x, y_dict[var])  # Update each curve with new data

    def update_display(self):
        """
        Updates every element of the GUI.
        """
        max_points = 50

        # TEST
        # Simulated data for testing
        self.time.append(self.idx)
        self.Ax.append(np.random.uniform(-10, 10))  
        self.Ay.append(np.random.uniform(-10, 10))
        self.Az.append(np.random.uniform(-10, 10))
        self.Gx.append(np.random.uniform(-10, 10))
        self.Gy.append(np.random.uniform(-10, 10))
        self.Gz.append(np.random.uniform(-10, 10))
        self.Vx.append(np.random.uniform(-10, 10))
        self.Vy.append(np.random.uniform(-10, 10))
        self.Vz.append(np.random.uniform(-10, 10))
        self.KFz.append(np.random.uniform(-10, 10))
        self.T.append(np.random.uniform(-10, 10))
        self.Ex.append(np.random.uniform(-10, 10))
        self.Ey.append(np.random.uniform(-10, 10))
        self.Ez.append(np.random.uniform(-10, 10))

        # Limit the number of points to display in the plot
        self.time = self.time[-max_points:]
        self.Ax = self.Ax[-max_points:]
        self.Ay = self.Ay[-max_points:]
        self.Az = self.Az[-max_points:]
        self.Gx = self.Gx[-max_points:]
        self.Gy = self.Gy[-max_points:]
        self.Gz = self.Gz[-max_points:]
        self.Vx = self.Vx[-max_points:]
        self.Vy = self.Vy[-max_points:]
        self.Vz = self.Vz[-max_points:]
        self.KFz = self.KFz[-max_points:]
        self.T = self.T[-max_points:]
        self.Ex = self.Ex[-max_points:]
        self.Ey = self.Ey[-max_points:]
        self.Ez = self.Ez[-max_points:]

        # Update the plots for acceleration (too lazy to do a for loop)
        self.update_plots('Plot1', self.time[-max_points:], {"KF_Z": self.KFz[-max_points:]})
        self.update_plots('Plot2', self.time[-max_points:], {"KF_VX": self.Vx[-max_points:], "KF_VY": self.Vy[-max_points:], "KF_VZ": self.Vz[-max_points:]})
        self.update_plots('Plot3', self.time[-max_points:], {"Euler_X": self.Ex[-max_points:], "Euler_Y": self.Ey[-max_points:], "Euler_Z": self.Ez[-max_points:]})
        self.update_plots('Plot4', self.time[-max_points:], {"Accel_X": self.Ax[-max_points:], "Accel_Y": self.Ay[-max_points:], "Accel_Z": self.Az[-max_points:]})
        self.update_plots('Plot5', self.time[-max_points:], {"Gyro_X": self.Gx[-max_points:], "Gyro_Y": self.Gy[-max_points:], "Gyro_Z": self.Gz[-max_points:]})
        self.update_plots('Plot6', self.time[-max_points:], {"Temp": self.T[-max_points:]})

        self.idx += 1 # Increment the index for testing
        # END TEST

        # REAL
        # comment out the test data above and uncomment this to use real data
        # Update the plots for acceleration (too lazy to do a for loop)
        # self.update_plots('Plot1', self.plot_data_dict["time"], {"KF_Z": self.plot_data_dict["KF_Z"]})
        # self.update_plots('Plot2', self.plot_data_dict["time"], {"KF_VX": self.plot_data_dict["KF_VX"], "KF_VY": self.plot_data_dict["KF_VY"], "KF_VZ": self.plot_data_dict["KF_VZ"]})
        # self.update_plots('Plot3', self.plot_data_dict["time"], {"Euler_X": self.plot_data_dict["Euler_X"], "Euler_Y": self.plot_data_dict["Euler_Y"], "Euler_Z": self.plot_data_dict["Euler_Z"]})
        # self.update_plots('Plot4', self.plot_data_dict["time"], {"Accel_X": self.plot_data_dict["Accel_X"], "Accel_Y": self.plot_data_dict["Accel_Y"], "Accel_Z": self.plot_data_dict["Accel_Z"]})
        # self.update_plots('Plot5', self.plot_data_dict["time"], {"Gyro_X": self.plot_data_dict["Gyro_X"], "Gyro_Y": self.plot_data_dict["Gyro_Y"], "Gyro_Z": self.plot_data_dict["Gyro_Z"]})
        # self.update_plots('Plot6', self.plot_data_dict["time"], {"Temp": self.plot_data_dict["Temp"]})
        # END REAL

        # Update the display elements with the latest data
        if self.raw_data is not None:
            self.ui.lat_val.setText(str(self.raw_data["Latitude"]))
            self.ui.lon_val.setText(str(self.raw_data["Longitude"]))
            self.ui.alt_val.setText(str(self.raw_data["GPS_Alt"])) # this value can be replaced entirely, probably with drag?
            self.ui.phase_val.setText(str(self.raw_data["Phase"])) # this needs to be translated into changing an element in the GUI
            self.ui.voltage_val.setText(str(self.raw_data["Voltage"]))
            self.ui.RSSI_val.setText(str(self.raw_data["Link_Strength"]))
            self.ui.diagnostic_message_val.setText(str(self.raw_data["Diagnostic_Message"])) # this needs to be translated into changing an element in the GUI
            self.ui.continuity_val.setText(str(self.raw_data["Continuity"])) # are these the pyros? need to figure out what data is being sent

        
    def closeEvent(self, event):
        '''
        Handle the window close event.
        '''
        # Ask the user for confirmation before closing the application
        reply = QtWidgets.QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )

        # If the user clicks Yes, close the application
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            event.accept()  # Close the application
            sys.exit(0)
        else:
            event.ignore()  # Ignore the close event

    # button functions
    # connect_toggle handles basic connectivity logic, needs a lot of improvement
    def connect_toggle(self):
        '''
        Toggle the WebSocket connection.
        '''
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
        '''
        Toggle the data collection state.
        '''
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
        '''
        Toggle the auto save feature for the recorded data.
        '''
        if self.autosave == 0:
            self.autosave = 1
            self.ui.autosave_toggle.setText("Auto Save: On")
            self.ui.log_entry.appendPlainText("Auto save enabled")
        else:
            self.autosave = 0
            self.ui.autosave_toggle.setText("Auto Save: Off")
            self.ui.log_entry.appendPlainText("Auto save disabled")

    def save_recorded_data(self): # saves data to a CSV file
        '''
        Save the collected data to CSV file.
        '''
        # Generate a filename based on the current date and time
        filename = str(datetime.now().strftime("%Y-%m-%d_%H.%M.%S")) + "_flightdata.csv"

        # Check if the recorded data DataFrame is not empty before saving
        if not self.recorded_data.empty:
            self.recorded_data.to_csv(filename, index=False) # Save the DataFrame to a CSV file
            self.ui.log_entry.appendPlainText(f"Data saved to {filename}") # Log the save action
        else:
            self.ui.log_entry.appendPlainText("No data to save.") # Log if no data is available
   
    def clear_recorded_data(self):
        '''
        Clear all recorded data from the plots and the DataFrame.
        '''

        # Clear all recorded data from the plots
        for config in self.plot_config.items():
            # Reset the data in the curves
            for curve in config['curves']:
                curve.setData([], [])  # Clear the curve data

        # Clear the data to be plotted
        for key in self.plot_data_dict.keys():
            self.plot_data_dict[key] = []

        # Reset the recorded data DataFrame
        self.recorded_data = pd.DataFrame(columns=[
            'time', 'Accel_X', 'Accel_Y', 'Accel_Z', 
            'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temp',
            'Euler_X', 'Euler_Y', 'Euler_Z', 'Baro_Alt',
            'Longitude', 'Latitude', 'GPS_Alt', 'Phase',
            'Continuity', 'Voltage', 'Link_Strength',
            'KF_X', 'KF_Y', 'KF_Z', 'KF_VX', 'KF_VY', 'KF_VZ',
            'KF_Drag', 'Diagnostic_Message'
        ])
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    #window.showMaximized()
    window.show()
    sys.exit(app.exec())
