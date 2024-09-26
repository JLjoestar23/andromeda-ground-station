import socket
from itertools import islice
import ast

class DataHandler:
    def __init__(self):
        self.data = None
        self.buffer = [] # Initialize a buffer so that self.data doesn't get overwritten when updating. This accumulates data packets
        self.HOST = '0.0.0.0'
        self.PORT = 4210

    def socket_to_receive_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow the socket to reuse the address
            s.bind((self.HOST, self.PORT))
            s.settimeout(30)
            while True: # while the connection is ongoing
                try: 
                    self.data, addr = s.recvfrom(1024) # _ = addr which we don't care about
                    print(self.data, addr)
                    if not self.data: print('There is no data coming through') ### THIS IS A SCAFFHOLD - WHAT IS PROPER EXIT CONDITION?
                    self.buffer.append(self.data)
                except socket.timeout:
                    print('Timeout: No data received in last 10 seconds.')

    def process_data(self):
        with open('logfile.txt', 'ab') as file:
            for data_packet in self.buffer: # Need to ensure that we're
                file.write(data_packet + b'\n')
            self.buffer.clear()
    
    def split_data_list(self):
        output = []
        # self.buffer is a list so we need to loop through it to get individual strings
        for data_packet in self.buffer:
            decoded_string = data_packet.decode('utf-8') # because we're receiving a byte string we need to decode with a format
            actual_list = ast.literal_eval(decoded_string) # evaluate the string so it becomes a list of this decoded string
            length_to_split = [1] * len(actual_list) # split the input array at each data point
            iter_input = iter(actual_list) 
            # Takes an iterator and number (elem) and returns an iterator (list) that has elem # of elements in it
            sublist = [list(islice(iter_input, 1)) for _ in length_to_split]
            output.extend(sublist)
        return output
    
    # We pass the output from split_data_list and convert these values to a float
    def convert_to_float(self, output):
        # When we pass output to this function it's a 2D list
        flatten_list = [flat for item in output for flat in item] # return only the string in the flattened list
        converted_values = list()
        # the equivalent would be taking in data
        for item in flatten_list: 
            converted_values.append(float(item))
        return converted_values

# Instantiate class
handler = DataHandler()
handler.socket_to_receive_data() # this function has no "return" value so no need to assign it to a variable
handler.process_data() # this function has no "return" value so no need to assign it to a variable
begin_split = handler.split_data_list()
float_conversion = handler.convert_to_float(begin_split) # pass the list from above

# creating a separate function for dictionary because it's dependent on the class being called
def float_to_dict(float_list):
    # This function contains the dictionary of array values from the ESP32 which will get passed into visualuzation
    # In order to access the values use syntax dictviz['Key']. Use these to plot
    dictviz = {
        'Current Time' : float_list[0],
        'Accelerometer X Direction' : float_list[1],
        'Accelerometer Y Direction' : float_list[2],
        'Accelerometer Z Direction' : float_list[3],
        'Gyroscope X Direction' : float_list[4],
        'Gyroscope Y Direction' : float_list[5],
        'Gyroscope Z Direction' : float_list[6],
        'Temperature' : float_list[7],
        'Euler X' : float_list[8],
        'Euler Y' : float_list[9],
        'Euler Z' : float_list[10],
        'Barometric Altitude' : float_list[11], # confirm correct key
        'Longitude' : float_list[12],
        'Latitude' : float_list[13],
        'GPS Altitude' : float_list[14],
        'Flight Phase' : float_list[15], 
        'Continuity' : float_list[16],
        'Voltage' : float_list[17],
        'Link' : float_list[18],
        'Kalman Filter X' : float_list[19],
        'Kalman Filter Y' : float_list[20],
        'Kalman Filter Z' : float_list[21],
        'Kalman Filter Vx' : float_list[22],
        'Kalman Filter Vy' : float_list[23], 
        'Kalman Filter Vz' : float_list[24], 
        'Kalman Filter Draf' : float_list[25],
        '' : float_list[26], # confirm
        'Diag Msg' : float_list[27], # confirm
    }

    return dictviz

# Call the float_to_dict function
floatdict = float_to_dict(float_conversion)
print(floatdict)