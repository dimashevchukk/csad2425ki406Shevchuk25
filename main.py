import serial
import time

ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(1)

message = "Msg from client"
ser.write((message + "\n").encode())
print(f"Request: {message}")

esp32_data = ser.readline().decode().strip()
print(f"Response: {esp32_data}")
ser.close()