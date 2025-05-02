import sys
import os
import time
import numpy as np
import pandas as pd
from PyQt6 import QtCore, QtWidgets, QtGui
from gsmw import Ui_MainWindow
import pyqtgraph as pg
import receive
from datetime import datetime

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Existing variables
        self.connect = 0
        self.status = "Disconnected"
        self.collect_data = 0
        self.log_message = ""
        self.autosave = 0
        self.autosave_text = ""
        self.output = None
        self.converted = None
        self.data_dict = {}

        # Initialize plots and data structures
        self.setup_plots()
        self.max_points = 1000
        self.initialize_data_structures()

        # Timer setup
        self.data_timer = QtCore.QTimer()
        self.data_timer.timeout.connect(self.fetch_data)
        self.data_timer.start(200)  # Data fetch every 200ms

        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(50)  # Plot updates every 50ms (20 FPS)

        # Rest of your existing __init__ code (buttons, etc.)...

    def setup_plots(self):
        """Configure all plot widgets with proper settings"""
        self.plot_config = {
            'Plot1': {
                'title': 'Altitude',
                'vars': ['Baro_Alt', 'KF_Z'],
                'colors': ['m', 'g'],
                'unit': 'm'
            },
            'Plot2': {
                'title': 'Velocity',
                'vars': ['KF_VZ'],
                'colors': ['b'],
                'unit': 'm/s'
            },
            'Plot3': {
                'title': 'Temperature',
                'vars': ['Temp'],
                'colors': ['y'],
                'unit': '°C'
            },
            'Plot4': {
                'title': 'Linear Acceleration',
                'vars': ['Accel_X', 'Accel_Y', 'Accel_Z'],
                'colors': ['r', 'g', 'b'],
                'unit': 'm/s²'
            },
            'Plot5': {
                'title': 'Angular Velocity',
                'vars': ['Gyro_X', 'Gyro_Y', 'Gyro_Z'],
                'colors': ['r', 'g', 'b'],
                'unit': 'rad/s'
            },
            'Plot6': {
                'title': 'Orientation',
                'vars': ['Euler_X', 'Euler_Y', 'Euler_Z'],
                'colors': ['r', 'g', 'b'],
                'unit': 'deg'
            }
        }

        for plot_name, config in self.plot_config.items():
            plot_widget = getattr(self.ui, plot_name)
            plot_widget.clear()
            plot_widget.setTitle(f"{config['title']} ({config['unit']})", color='w', size='12pt')
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

    def fetch_data(self):
        """Fetch new data and update buffers"""
        self.raw_data = receive.get_data()
        
        if self.raw_data is not None and self.collect_data:
            # Store in DataFrame
            new_row = pd.DataFrame([self.raw_data])
            self.recorded_data = pd.concat([self.recorded_data, new_row], ignore_index=True)
            
            # Update plot buffers
            self.update_plot_buffers(self.raw_data)
            
            # Trim DataFrame if needed
            if len(self.recorded_data) > 10000:
                self.recorded_data = self.recorded_data.iloc[-10000:]

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

    def update_plots(self):
        """Update all plots with current data"""
        for plot_name, plot_info in self.plot_history.items():
            ptr = plot_info['ptr']
            config = self.plot_config[plot_name]
            
            if ptr == 0:
                x_data = plot_info['time']
                y_data = {var: plot_info['data'][var] for var in config['vars']}
            else:
                x_data = plot_info['time'][:ptr]
                y_data = {var: plot_info['data'][var][:ptr] for var in config['vars']}
            
            for i, var in enumerate(config['vars']):
                config['curves'][i].setData(x_data, y_data[var])
            
            self.auto_range_plot(plot_name, x_data, y_data)

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

    # Keep all your existing button functions (connect_toggle, etc.) exactly as they are
    # ...

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())