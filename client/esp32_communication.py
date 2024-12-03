import serial
import serial.tools.list_ports
import time


class esp32:
    def __init__(self):
        self.ser = None
        self.port = None

    def find_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

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

    def send_message(self, message):
        if not self.ser or not self.ser.is_open:
            return "Port not opened or connection lost."

        try:
            self.ser.write(message)
            return f"Sent: {message}."
        except serial.SerialException as e:
            return f"Error: {e}"

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
