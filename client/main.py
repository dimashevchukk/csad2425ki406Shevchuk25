import serial
import serial.tools.list_ports
import time


class ESP32_Communication:
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

    def send_message(self, message):
        if not self.ser or not self.ser.is_open:
            return "Port not opened or connection lost."

        try:
            self.ser.write((message + "\n").encode())
            return f"Sent: {message}."
        except serial.SerialException as e:
            return f"Connection lost: {e}"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode().strip()
                if response:
                    return response
            except Exception as e:
                return f"Error: {e}."
        return "Port not opened."

    def communication(self):
        status = self.connect()
        print(status)

        if status == f"Connected to {self.port}.":
            while True:
                user_input = input("Enter a message or exit: ")
                if user_input == "exit":
                    break

                status = server.send_message(user_input)
                print(status)

                status = server.receive_message()
                print(f"Recieved: {status}")


if __name__ == "__main__":
    server = ESP32_Communication()
    server.communication()