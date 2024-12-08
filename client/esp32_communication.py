##
# @file
# @brief Logic for communication with ESP32 server through COM port.

import serial
import serial.tools.list_ports
import time

##
# @class esp32
# @brief Class to communicate with ESP32 server through COM port.
# Class for interacting with a device via serial communication.
# It allows finding available ports, connecting to a selected port,
# sending and receiving messages, and closing the connection.
# @param self.ser: The serial connection object.
# @param self.port: The serial port to connect to.

class esp32:
    ##
    # @brief Initializes the `esp32` class.
    def __init__(self):
        self.ser = None
        self.port = None

    ##
    # @brief Method to find available ports.
    # @return a list of available ports.
    def find_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    ##
    # @brief Method to connect to ESP32 server.
    # Connects to a serial port by selecting the port and baud rate via console input.
    # Reads the available ports and allows the user to select one.
    # The user then selects a baud rate from a predefined list.
    # @return String either connected or exception.
    def connect(self):
        com_list = self.find_ports()
        if len(com_list) == 0:
            return "No serial ports found."

        while True:
            print("Available COM ports:")
            for i, com in enumerate(com_list):
                print(f"{i + 1}: {com}")
            selected_index = int(input("Select a COM port by number: ")) - 1
            if 0 <= selected_index < len(com_list):
                self.port = com_list[selected_index]
                break
            print("Invalid COM port selection.")

        baudrates = [9600, 19200, 38400, 57600, 115200, 230400]

        while True:
            print("Available baudrates:")
            for i, rate in enumerate(baudrates, 1):
                print(f"{i}. {rate}")
            choice = input("Select baudrate by number: ")
            if choice.isdigit() and 1 <= int(choice) <= len(baudrates):
                baudrate = baudrates[int(choice) - 1]
                break
            print("Invalid choice. Please try again.")

        try:
            self.ser = serial.Serial(self.port, baudrate, timeout=1)
            time.sleep(1)
            return f"Connected to {self.port}."
        except serial.SerialException as e:
            self.ser = None
            return f"Error: {e}."


    ##
    # @brief Method to connect to ESP32 server using txt file.
    # Connects to a serial port using settings from a configuration file. (See connection_settings.txt)
    # Reads the port and baud rate from the file and establishes a connection to the device.
    # @return String either connected or exception.
    def connect_from_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                port = lines[0].strip()
                baudrate = int(lines[1].strip())

            if port not in self.find_ports():
                return f"Error: Port {port} is not available."

            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.port = port
            time.sleep(1)
            return f"Connected to {port} using settings from {file_path}."

        except FileNotFoundError:
            return f"Error: Configuration file {file_path} not found."
        except ValueError:
            return f"Error: Invalid configuration format in {file_path}."
        except serial.SerialException as e:
            return f"Error connecting to {port}: {e}."

    ##
    # @brief Method to send a message to the device.
    # @return String either sent or exception.
    def send_message(self, message):
        if not self.ser or not self.ser.is_open:
            return "Port not opened or connection lost."

        try:
            self.ser.write(message)
            return f"Sent: {message}."
        except serial.SerialException as e:
            return f"Error: {e}"

    ##
    # @brief Method to receive a message from the device.
    # Collects the strings from the response in one string and returns it.
    # @return String which is either response or exception.
    def receive_message(self):
        if not self.ser or not self.ser.is_open:
            return "Port not opened or connection lost."

        try:
            response_data = []
            while True:
                line = self.ser.readline().decode().strip()
                if line:
                    response_data.append(line)
                if line.endswith("</response>"):
                    break
            response = "".join(response_data)
            return response
        except Exception as e:
            return f"Error: {e}."

    ##
    # @brief Method to close the connection.
    # If the connection is open, closes the port and prints a message about the closure.
    def close_connection(self):
        if self.ser:
            self.ser.close()
            print("Serial connection closed.")