##
# @file Tests
# Written for UI and esp32_communication files.

import serial
import unittest

from unittest.mock import patch, MagicMock, mock_open
from xml.etree import ElementTree as ET

from esp32_communication import esp32


##
# @class TestESP32Communication
# @brief Test communication by mocking board, ports, parameters.
class TestESP32Communication(unittest.TestCase):
    ##
    # @brief Test that `find_ports` returns a list of available COM ports.
    # Mocking the COM ports to simulate two available ports: COM3 and COM4.
    @patch('serial.tools.list_ports.comports')
    def test_find_ports_success(self, mock_comports):
        mock_comports.return_value = [MagicMock(device="COM3"), MagicMock(device="COM4")]
        server = esp32()
        ports = server.find_ports()
        self.assertEqual(ports, ["COM3", "COM4"])

    ##
    # @brief Test that `find_ports` returns an empty list when no COM ports are available.
    @patch('serial.tools.list_ports.comports')
    def test_find_ports_no_ports(self, mock_comports):
        mock_comports.return_value = []
        server = esp32()
        ports = server.find_ports()
        self.assertEqual(ports, [])

    ##
    # @brief Test the `connect` method successfully connects to a valid COM port with baudrate.
    # Mocking user input to select COM3 and baudrate 9600.
    @patch('serial.Serial')
    @patch('builtins.input', side_effect=["1", "1"])  # COM3 & 9600
    @patch('serial.tools.list_ports.comports')
    def test_connect_success(self, mock_comports, mock_input, mock_serial):
        mock_comports.return_value = [MagicMock(device="COM3")]
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance

        server = esp32()
        result = server.connect()
        self.assertEqual(result, "Connected to COM3.")
        mock_serial.assert_called_once_with("COM3", 9600, timeout=1)

    ##
    # @brief Test the `connect` method handles the case when no COM ports are available.
    @patch('serial.tools.list_ports.comports')
    def test_connect_no_ports(self, mock_comports):
        mock_comports.return_value = []
        server = esp32()
        status = server.connect()
        self.assertEqual(status, "No serial ports found.")

    ##
    # @brief Test `connect_from_file` successfully connects using valid configuration.
    # Mocking a configuration file with COM3 and baudrate 115200.
    @patch("builtins.open", new_callable=mock_open, read_data="COM3\n115200")
    @patch("serial.Serial")
    @patch.object(esp32, "find_ports", return_value=["COM3", "COM4"])
    def test_connect_from_file_success(self, mock_find_ports, mock_serial, mock_file):
        server = esp32()
        result = server.connect_from_file("config.txt")
        self.assertEqual(result, "Connected to COM3 using settings from config.txt.")
        mock_serial.assert_called_once_with("COM3", 115200, timeout=1)

    ##
    # @brief Test `connect_from_file` handles missing configuration file gracefully.
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_connect_from_file_file_not_found(self, mock_file):
        server = esp32()
        result = server.connect_from_file("missing_config.txt")
        self.assertEqual(result, "Error: Configuration file missing_config.txt not found.")

    ##
    # @brief Test `connect_from_file` handles invalid baudrate in the configuration file.
    @patch("builtins.open", new_callable=mock_open, read_data="COM3\ninvalid_baudrate")
    def test_connect_from_file_invalid_baudrate(self, mock_file):
        server = esp32()
        result = server.connect_from_file("invalid_config.txt")
        self.assertEqual(result, "Error: Invalid configuration format in invalid_config.txt.")

    ##
    # @brief Test `connect_from_file` handles SerialException when trying to connect.
    @patch("builtins.open", new_callable=mock_open, read_data="COM3\n115200")
    @patch("serial.Serial", side_effect=serial.SerialException("Test error"))
    @patch.object(esp32, "find_ports", return_value=["COM3", "COM4"])
    def test_connect_from_file_serial_exception(self, mock_find_ports, mock_serial, mock_file):
        server = esp32()
        result = server.connect_from_file("config.txt")
        self.assertEqual(result, "Error connecting to COM3: Test error.")

    ##
    # @brief Test `connect_from_file` handles invalid COM port in the configuration file.
    @patch("builtins.open", new_callable=mock_open, read_data="COM99\n115200")
    @patch.object(esp32, "find_ports", return_value=["COM3", "COM4"])
    def test_connect_from_file_invalid_port(self, mock_find_ports, mock_file):
        server = esp32()
        result = server.connect_from_file("config.txt")
        self.assertEqual(result, "Error: Port COM99 is not available.")

    ##
    # @brief Test that `send_message` sends a message successfully when the port is open.
    @patch('serial.Serial')
    def test_send_message_success(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        server = esp32()
        server.ser = mock_serial_instance # Simulating an open serial connection

        result = server.send_message("Hello ESP32")
        self.assertEqual(result, "Sent: Hello ESP32.")

    ##
    # @brief Test that `send_message` returns an error when no serial port is open.
    @patch('serial.Serial')
    def test_send_message_no_port(self, mock_serial):
        server = esp32() # No serial connection initialized
        result = server.send_message("Hello ESP32")
        self.assertEqual(result, "Port not opened or connection lost.")

    ##
    # @brief Tests receive message.
    # Test that `receive_message` reads multiple lines from the serial port and combines them correctly.
    # Mocking the serial port to simulate receiving a multi-line message.
    @patch('serial.Serial')
    def test_receive_message_success(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial_instance.is_open = True
        mock_serial_instance.readline.side_effect = [
            b"<response>Part 1\n",
            b"Part 2\n",
            b"Part 3</response>\n"
        ]
        mock_serial.return_value = mock_serial_instance
        server = esp32()
        server.ser = mock_serial_instance # Simulating an open serial connection

        result = server.receive_message()
        self.assertEqual(result, "<response>Part 1Part 2Part 3</response>")
        self.assertEqual(mock_serial_instance.readline.call_count, 3)

    ##
    # @brief Test that `receive_message` returns an error when no serial port is open.
    @patch('serial.Serial')
    def test_receive_message_no_port(self, mock_serial):
        server = esp32() # No serial connection initialized
        result = server.receive_message()
        self.assertEqual(result, "Port not opened or connection lost.")


##
# @class TestESP32Server
# @brief Tests logic of server.
class TestESP32Server(unittest.TestCase):
    ##
    # @brief Mock serial port.
    @classmethod
    def setUpClass(cls):
        cls.serial_port = MagicMock()

    ##
    # @brief Close serial port.
    @classmethod
    def tearDownClass(cls):
        cls.serial_port.close()

    ##
    # @brief Encode and send XML request.
    def send_request(self, xml_request):
        self.serial_port.write((xml_request + '\n').encode())

    ##
    # @brief Collect XML response in string and return it.
    def recieve_response(self):
        response_data = []
        while True:
            line = self.serial_port.readline().decode().strip()
            if line:
                response_data.append(line)
            if line.endswith("</response>"):
                break
        response = "".join(response_data)
        return response

    ##
    # @brief Parse XML response.
    def parse_response(self, response):
        return ET.fromstring(response)

    ##
    # @brief Test setting the game mode to "pvp".
    # This test simulates sending a request to set the game mode to "pvp" and verifies:
    # The request is correctly sent over the serial port.
    # The received response is well-formed XML.
    # The response contains the correct mode information ("pvp").
    # It uses mocked methods for `write` and `readline` to simulate serial port communication.
    def test_set_mode_pvp(self):
        with patch.object(self.serial_port, 'write') as mock_write, \
                patch.object(self.serial_port, 'readline', side_effect=[
                    """<response type="mode"><mode name="pvp"/></response>\n""".encode()
                ]) as mock_readline:
            request = """<request type="mode"><mode name="pvp"/></request>"""
            self.send_request(request)
            response = self.recieve_response()
            root = self.parse_response(response)

            self.assertEqual(root.tag, "response")
            self.assertEqual(root.attrib["type"], "mode")

            mode_element = root.find("mode")
            self.assertIsNotNone(mode_element)
            self.assertEqual(mode_element.attrib["name"], "pvp")

            mock_write.assert_called_once_with((request + '\n').encode())
            mock_readline.assert_called()

    ##
    # @brief Test setting the game mode to "pvbot".
    # This test simulates sending a request to set the game mode to "pvbot" and verifies:
    # The request is correctly sent over the serial port.
    # The received response is well-formed XML.
    # The response contains the correct mode information ("pvbot").
    # It uses mocked methods for `write` and `readline` to simulate serial port communication.
    def test_set_mode_pvbot(self):
        with patch.object(self.serial_port, 'write') as mock_write, \
             patch.object(self.serial_port, 'readline', side_effect=[
                 """<response type="mode"><mode name="pvbot"/></response>\n""".encode()
             ]) as mock_readline:

            request = """<request type="mode"><mode name="pvbot"/></request>"""
            self.send_request(request)
            response = self.recieve_response()
            root = self.parse_response(response)

            self.assertEqual(root.tag, "response")
            self.assertEqual(root.attrib["type"], "mode")

            mode_element = root.find("mode")
            self.assertIsNotNone(mode_element)
            self.assertEqual(mode_element.attrib["name"], "pvbot")

            mock_write.assert_called_once_with((request + '\n').encode())
            mock_readline.assert_called()

    ##
    # @brief Test setting the game mode to "pvp".
    # This test simulates the following:
    # Setting the game mode to "pvp".
    # Sending a move request for player "X" to place a mark at coordinates (0, 0).
    # The test verifies:
    # The move request is correctly sent over the serial port.
    # The received response is well-formed XML.
    # The response indicates the game is ongoing with status "Continue".
    # It uses mocked methods for `write` and `readline` to simulate serial port communication.
    def test_move_pvp(self):
        with patch.object(self.serial_port, 'write') as mock_write, \
             patch.object(self.serial_port, 'readline', side_effect=[
                 """<response type="gameover"><status name="Continue"/></response>\n""".encode()
             ]) as mock_readline:

            self.test_set_mode_pvp()
            request = """<request type="move"><player name="X"/><move x="0" y="0"/></request>"""
            self.send_request(request)
            response = self.recieve_response()
            root = self.parse_response(response)

            self.assertEqual(root.tag, "response")
            self.assertEqual(root.attrib["type"], "gameover")

            status_element = root.find("status")
            self.assertIsNotNone(status_element)
            self.assertEqual(status_element.attrib["name"], "Continue")

            mock_write.assert_any_call((request + '\n').encode())
            mock_readline.assert_called()

    ##
    # @brief Test making a move in "pvbot" mode.
    # This test simulates the following:
    # Setting the game mode to "pvbot".
    # Sending a move request for player "X" to place a mark at coordinates (0, 0).
    # The test verifies:
    # The move request is correctly sent over the serial port.
    # The received response is well-formed XML.
    # The response contains the game continuation status ("Continue") and move coordinates.
    # It uses mocked methods for `write` and `readline` to simulate serial port communication.
    def test_move_pvbot(self):
        with patch.object(self.serial_port, 'write') as mock_write, \
             patch.object(self.serial_port, 'readline', side_effect=[
                 """<response type="move"><status name="Continue"/><move x="1" y="1"/></response>\n""".encode()
             ]) as mock_readline:

            self.test_set_mode_pvbot()
            request = """<request type="move"><player name="X"/><move x="0" y="0"/></request>"""
            self.send_request(request)
            response = self.recieve_response()
            root = self.parse_response(response)

            self.assertEqual(root.tag, "response")
            self.assertEqual(root.attrib["type"], "move")

            status_element = root.find("status")
            self.assertIsNotNone(status_element)
            self.assertEqual(status_element.attrib["name"], "Continue")

            move_element = root.find("move")
            self.assertIsNotNone(move_element)

            mock_write.assert_any_call((request + '\n').encode())
            mock_readline.assert_called()

    ##
    # @brief Test running a full game in "botvbot" mode.
    # This test simulates the following:
    # Setting the game mode to "botvbot".
    # Simulating multiple moves from two bots until a winner is determined.
    # The test verifies:
    # The initial mode is correctly set to "botvbot".
    # Each move request is processed correctly, and responses contain valid XML with continuation status.
    # The game eventually ends with one of the players ("X") declared as the winner.
    # It uses mocked methods for `write` and `readline` to simulate serial port communication.
    def test_botvbot(self):
        with patch.object(self.serial_port, 'write') as mock_write, \
             patch.object(self.serial_port, 'readline', side_effect=[
                 """<response type="mode"><mode name="botvbot"/></response>\n""".encode(),
                 """<response type="move"><status name="Continue"/><move x="0" y="0"/></response>\n""".encode(),
                 """<response type="move"><status name="Continue"/><move x="1" y="1"/></response>\n""".encode(),
                 """<response type="move"><status name="X"/><move x="2" y="2"/></response>\n""".encode()
             ]) as mock_readline:

            request = """<request type="mode"><mode name="botvbot"/></request>"""
            self.send_request(request)
            response = self.recieve_response()
            root = self.parse_response(response)

            self.assertEqual(root.tag, "response")
            self.assertEqual(root.attrib["type"], "mode")

            mode_element = root.find("mode")
            self.assertIsNotNone(mode_element)
            self.assertEqual(mode_element.attrib["name"], "botvbot")

            for _ in range(9):
                response = self.recieve_response()
                if response:
                    root = self.parse_response(response)
                    if root.attrib["type"] == "move":
                        status = root.find("status").attrib["name"]
                        if status != "Continue":
                            break

            self.assertIn(status, "X")

            mock_write.assert_any_call((request + '\n').encode())
            mock_readline.assert_called()

##
# @brief Run all tests.
if __name__ == "__main__":
    unittest.main()