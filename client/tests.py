import serial
import unittest
from unittest.mock import patch, MagicMock
from main import ESP32_Communication


class TestESP32Communication(unittest.TestCase):

    @patch('serial.tools.list_ports.comports')
    def test_find_ports(self, mock_comports):
        mock_comports.return_value = [MagicMock(device="COM3"), MagicMock(device="COM4")]
        server = ESP32_Communication()
        ports = server.find_ports()
        self.assertEqual(ports, ["COM3", "COM4"])

    @patch('serial.tools.list_ports.comports')
    def test_find_no_ports(self, mock_comports):
        mock_comports.return_value = []
        server = ESP32_Communication()
        ports = server.find_ports()
        self.assertEqual(ports, [])

    @patch('serial.Serial')
    @patch('builtins.input', side_effect=["1", "1"])  # COM3 & 9600
    @patch('serial.tools.list_ports.comports')
    def test_connect_success(self, mock_comports, mock_input, mock_serial):
        mock_comports.return_value = [MagicMock(device="COM3")]
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance

        server = ESP32_Communication()
        result = server.connect()
        self.assertEqual(result, "Connected to COM3")
        mock_serial.assert_called_once_with("COM3", 9600, timeout=1)

    @patch('serial.tools.list_ports.comports')
    def test_connect_no_ports(self, mock_comports):
        mock_comports.return_value = []
        server = ESP32_Communication()
        status = server.connect()
        self.assertEqual(status, "No serial ports found")

    @patch('serial.Serial')
    def test_send_message_success(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        server = ESP32_Communication()
        server.ser = mock_serial_instance

        result = server.send_message("Hello ESP32")
        self.assertEqual(result, "Sent: Hello ESP32")
        mock_serial_instance.write.assert_called_once_with(b"Hello ESP32\n")

    @patch('serial.Serial')
    def test_send_message_no_port(self, mock_serial):
        server = ESP32_Communication()
        result = server.send_message("Hello ESP32")
        self.assertEqual(result, "Port not opened")

    @patch('serial.Serial')
    def test_receive_message_success(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial_instance.is_open = True
        mock_serial_instance.readline.return_value = b"Response from ESP32\n"
        mock_serial.return_value = mock_serial_instance

        server = ESP32_Communication()
        server.ser = mock_serial_instance

        result = server.receive_message()
        self.assertEqual(result, "Response from ESP32")
        mock_serial_instance.readline.assert_called_once()

    @patch('serial.Serial')
    def test_receive_message_no_port(self, mock_serial):
        server = ESP32_Communication()
        result = server.receive_message()
        self.assertEqual(result, "Port not opened")

if __name__ == "__main__":
    unittest.main()