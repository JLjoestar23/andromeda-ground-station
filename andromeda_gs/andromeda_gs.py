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
        self.output = None
        self.converted = None
        self.max_points = 50
        self.data_dict = {}

        # setting icons
        self.icon_path = os.path.join(
            os.path.dirname(__file__), "images", "meatball.png"
        )
        self.setWindowIcon(QtGui.QIcon(self.icon_path))

        # setting window name
        self.setWindowTitle("Andromeda Ground Station")
        pg.setConfigOptions(antialias=True)

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

        # Initializing timer object
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.main_loop) # Update plots every 200 milliseconds
        self.update_timer.start(200)  # Check every 200 milliseconds 
        
    # general functions
    def main_loop(self): # need to figure out the exact architecture of this function
        if self.connect == 1:
            self.fetch_data()
        self.update_plots()
        
    def setup_plots(self):
        """Configure all plot widgets with proper settings"""
        color1 = (150,212,236) # light shade of Olin blue
        color2 = (25,150,207) # slightly darker shade of Olin blue
        color3 = (4,93,162) # dark shade of Olin blue

        self.plot_config = {
            'Plot1': {
                'title': 'Altitude',
                'vars': ['KF_Z'],
                'colors': [color1],
                'unit': 'm'
            },
            'Plot2': {
                'title': 'Velocity',
                'vars': ['KF_VZ'],
                'colors': [color1],
                'unit': 'm/s'
            },
            'Plot3': {
                'title': 'Orientation',
                'vars': ['Euler_X', 'Euler_Y', 'Euler_Z'],
                'colors': [color1, color2, color3],
                'unit': 'deg'
            },
            'Plot4': {
                'title': 'Temperature',
                'vars': ['Temp'],
                'colors': [color1],
                'unit': '°C'
            },
            'Plot5': {
                'title': 'Linear Acceleration',
                'vars': ['Accel_X', 'Accel_Y', 'Accel_Z'],
                'colors': [color1, color2, color3],
                'unit': 'm/s²'
            },
            'Plot6': {
                'title': 'Angular Velocity',
                'vars': ['Gyro_X', 'Gyro_Y', 'Gyro_Z'],
                'colors': [color1, color2, color3],
                'unit': 'rad/s'
            }
        }

        for plot_name, config in self.plot_config.items():
            plot_widget = getattr(self.ui, plot_name)
            plot_widget.clear()
            plot_widget.setTitle(f"{config['title']} ({config['unit']})", color=(214,230,237), size='12pt')
            plot_widget.setLabel('left', config['unit'])
            plot_widget.setLabel('bottom', 'Time')
            plot_widget.addLegend()
            plot_widget.showGrid(x=True, y=True)
            
            config['curves'] = []
            for var, color in zip(config['vars'], config['colors']):
                curve = plot_widget.plot(pen=pg.mkPen(color, width=2), name=var)
                config['curves'].append(curve)

    def initialize_data_structures(self):
        """Initialize data storage structures"""
        self.recorded_data = pd.DataFrame(columns=[
            'time', 'Accel_X', 'Accel_Y', 'Accel_Z', 
            'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temp',
            'Euler_X', 'Euler_Y', 'Euler_Z', 'Baro_Alt',
            'Longitude', 'Latitude', 'GPS_Alt', 'Phase',
            'Continuity', 'Voltage', 'Link_Strength',
            'KF_X', 'KF_Y', 'KF_Z', 'KF_VX', 'KF_VY', 'KF_VZ',
            'KF_Drag', 'Diagnostic_Message'
        ])
        
        self.plot_history = {}
        for plot_name, config in self.plot_config.items():
            self.plot_history[plot_name] = {
                'time': np.zeros(self.max_points),
                'data': {var: np.zeros(self.max_points) for var in config['vars']},
                'ptr': 0
            }

    # def update_plots(self):
    #     """Update all plots with current data"""
    #     for plot_name, plot_info in self.plot_history.items():
    #         ptr = plot_info['ptr']
    #         config = self.plot_config[plot_name]
            
    #         if ptr == 0:
    #             x_data = plot_info['time']
    #             y_data = {var: plot_info['data'][var] for var in config['vars']}
    #         else:
    #             x_data = plot_info['time'][:ptr]
    #             y_data = {var: plot_info['data'][var][:ptr] for var in config['vars']}
            
    #         for i, var in enumerate(config['vars']):
    #             config['curves'][i].setData(x_data, y_data[var])
            
    #         self.auto_range_plot(plot_name, x_data, y_data)

    def update_plots(self):
        
    

    def auto_range_plot(self, plot_name, x_data, y_data):
        """Auto-scale plot to fit data"""
        plot_widget = getattr(self.ui, plot_name)
        
        if len(x_data) > 0:
            x_min, x_max = np.min(x_data), np.max(x_data)
            x_padding = max(0.1 * (x_max - x_min), 1.0)
            plot_widget.setXRange(x_min - x_padding, x_max + x_padding)
        
        all_y = np.concatenate([yd for yd in y_data.values()])
        valid_y = all_y[~np.isnan(all_y)]
        if len(valid_y) > 0:
            y_min, y_max = np.min(valid_y), np.max(valid_y)
            y_padding = max(0.1 * (y_max - y_min), 0.1)
            plot_widget.setYRange(y_min - y_padding, y_max + y_padding)

    def fetch_data(self):
        """Fetch new data and update buffers"""
        self.raw_data = receive.get_data()
        print(self.raw_data)

        if self.raw_data is not None and self.collect_data:
            # Store in DataFrame
            new_row = pd.DataFrame([self.raw_data])
            self.recorded_data = pd.concat([self.recorded_data, new_row], ignore_index=True)

            # Update plot buffers
            self.update_plot_buffers(self.raw_data)
            
            # Trim DataFrame if needed
            #if len(self.recorded_data) > 10000:
            #    self.recorded_data = self.recorded_data.iloc[-10000:]
    
    def update_plot_buffers(self, new_data):
        """Update circular buffers with new data"""
        current_time = new_data.get('time', time.time())
        
        for plot_name, plot_info in self.plot_history.items():
            ptr = plot_info['ptr']
            plot_info['time'][ptr] = current_time
            
            for var in plot_info['data'].keys():
                if var in new_data:
                    try:
                        plot_info['data'][var][ptr] = float(new_data[var])
                    except (ValueError, TypeError):
                        plot_info['data'][var][ptr] = np.nan
            
            plot_info['ptr'] = (ptr + 1) % self.max_points

    def update_display(self):
        """
        Updates every element of the GUI.
        """
        
        self.fetch_data() # Fetch the latest data from the WebSocket

        self.update_plots("temp", self.x, self.y)


    def closeEvent(self, event):
        """
        Handle the window close event.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            event.accept()  # Close the application
            sys.exit(0)
        else:
            event.ignore()  # Ignore the close event

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

    def save_recorded_data(self): # saves data to a CSV file
        """Save the collected data to CSV"""
        filename = str(datetime.now().strftime("%Y-%m-%d_%H.%M.%S")) + "_flightdata.csv"
        if not self.recorded_data.empty:
            self.recorded_data.to_csv(filename, index=False)
            self.ui.log_entry.appendPlainText(f"Data saved to {filename}")

    def clear_recorded_data(self):
        pass

    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
