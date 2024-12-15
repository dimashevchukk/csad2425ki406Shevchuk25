##
# @file Tests
# Written for UI and esp32_communication files.

import serial
import unittest
import tkinter as tk

from unittest.mock import patch, MagicMock, mock_open
from xml.etree import ElementTree as ET
from esp32_communication import esp32
from UI import TicTacToe


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
# @class TestUI
# @brief Test graphic interface.
class TestUI(unittest.TestCase):
    ##
    # @Brief Set up game and esp
    def setUp(self):
        self.game = TicTacToe()
        self.game.esp = esp32()

    ##
    # @Brief Destroy window root
    def tearDown(self):
        self.game.root.destroy()

    ##
    # @Brief Test that main menu contains all required buttons.
    def test_initial_main_menu_elements(self):
        self.game.create_main_menu()

        button_texts = [
            "Player VS Player",
            "Player VS Bot",
            "Bot VS Bot",
            "Load Game"
        ]

        for text in button_texts:
            found = False
            for widget in self.game.root.winfo_children():
                if isinstance(widget, tk.Button) and widget.cget('text') == text:
                    found = True
                    break
            self.assertTrue(found, f"Button '{text}' not found in main menu")

    ##
    # @Brief Test game mode selection initiates correct game setup.
    def test_game_mode_selection(self):
        game_modes = ["pvp", "pvbot", "botvbot"]

        for mode in game_modes:
            with patch.object(self.game, 'create_board') as mock_create_board:
                # Reset game state
                self.game.board = [[" " for _ in range(3)] for _ in range(3)]
                self.game.start_game(mode)

                # Assert game state is correctly set
                self.assertEqual(self.game.game_mode, mode)
                self.assertEqual(self.game.current_player, 'X')
                self.assertFalse(self.game.gameover)

                # Verify board creation was called
                mock_create_board.assert_called_once()

    ##
    # @Brief Test board creation UI elements.
    def test_board_creation(self):
        self.game.start_game("pvp")
        self.assertEqual(len(self.game.buttons), 3)

        for row in self.game.buttons:
            self.assertEqual(len(row), 3)
            for button in row:
                self.assertIsInstance(button, tk.Button)
                self.assertEqual(button.cget('text'), ' ')

    ##
    # @Brief Test move validation and UI update.
    def test_move_validation(self):
        self.game.start_game("pvp")

        row, col = 1, 1
        self.game.make_move(row, col)

        self.assertEqual(self.game.board[row][col], 'X')
        self.assertEqual(self.game.buttons[row][col].cget('text'), 'X')
        self.assertEqual(self.game.buttons[row][col].cget('state'), 'disabled')

    ##
    # @Brief Test player switching mechanism.
    def test_player_switch(self):
        self.game.start_game("pvp")

        self.assertEqual(self.game.current_player, 'X')
        self.assertTrue('X' in self.game.info_label.cget('text'))

        self.game.make_move(0, 0)
        self.assertEqual(self.game.current_player, 'O')
        self.assertTrue('O' in self.game.info_label.cget('text'))

    ##
    # @Brief Test game saving and loading functionality.
    def test_game_save_and_load(self):
        self.game.start_game("pvp")
        self.game.make_move(0, 0)
        self.game.make_move(1, 1)
        self.game.save_game()

        new_game = TicTacToe()
        new_game.load_game()

        self.assertEqual(new_game.board[0][0], 'X')
        self.assertEqual(new_game.board[1][1], 'O')
        self.assertEqual(new_game.current_player, 'X')

    ##
    # @Brief Test error handling during game loading.
    @patch('xml.etree.ElementTree.parse')
    def test_load_game_error_handling(self, mock_parse):
        mock_parse.side_effect = FileNotFoundError()

        with patch('builtins.print') as mock_print:
            self.game.load_game()
            mock_print.assert_called_with(f"Error: File {self.game.file_name} not found.")

        mock_parse.side_effect = ET.ParseError()

        with patch('builtins.print') as mock_print:
            self.game.load_game()
            mock_print.assert_called_with(f"Error: Failed to parse the XML file {self.game.file_name}.")

    ##
    # @Brief Test starting by choosing manual input
    def test_start_config_manual_input(self):
        # Configure the mock connect method to return a specific value
        self.game.esp.connect = MagicMock(return_value="Connected successfully")

        # Simulate manual input
        with patch('builtins.input', return_value='1'), \
                patch('builtins.print') as mock_print:
            # Call the method
            self.game.start_config()

            # Assert that connect was called
            self.game.esp.connect.assert_called_once()

            # Verify the print output
            mock_print.assert_called_with("Connected successfully")

    ##
    # @Brief Test starting by choosing file input.
    def test_start_config_file_input(self):
        # Configure the mock connect_from_file method to return a specific value
        self.game.esp.connect_from_file = MagicMock(return_value="Loaded from file")

        # Simulate file input
        with patch('builtins.input', return_value='2'), \
                patch('builtins.print') as mock_print:
            # Call the method
            self.game.start_config()

            # Assert that connect_from_file was called with the correct filename
            self.game.esp.connect_from_file.assert_called_once_with("connection_settings.txt")

            # Verify the print output
            mock_print.assert_called_with("Loaded from file")

    ##
    # @Brief Test invalid input while starting.
    def test_invalid_input(self):
        # Test handling of invalid input
        with patch('builtins.input', side_effect=['3', '1']):
            self.game.esp.connect = MagicMock(return_value="Connected successfully")

            with patch('builtins.print') as mock_print:
                self.game.start_config()

                # Verify that "Invalid choice" was printed
                mock_print.assert_any_call("Invalid choice")
                # Verify that connect was eventually called
                self.game.esp.connect.assert_called_once()

    ##
    # @Brief Test returning to menu.
    def test_back_to_menu(self):
        # Setup: Create some widgets to destroy
        tk.Button(self.game.root, text="Test Button").pack()

        # Mock save_game and create_main_menu methods
        with patch.object(self.game, 'save_game'), \
                patch.object(self.game, 'create_main_menu'):
            self.game.back_to_menu()

            # Verify that save_game and create_main_menu were called
            self.game.save_game.assert_called_once()
            self.game.create_main_menu.assert_called_once()

            # Check that all widgets were destroyed
            self.assertEqual(len(self.game.root.winfo_children()), 0)

    ##
    # @Brief Test handling response.
    def test_handle_response_mode(self):
        # XML for bot vs bot mode
        xml_response = '''
        <response type="mode">
            <mode name="botvbot"/>
        </response>
        '''

        # Mock handle_bot_v_bot method
        with patch.object(self.game, 'handle_bot_v_bot') as mock_handle_bot:
            self.game.handle_response(xml_response)
            self.game.handle_bot_v_bot.assert_called_once()

    ##
    # @Brief Test handling response type move.
    def test_handle_response_move(self):
        # XML for a move response
        xml_response = '''
        <response type="move">
            <status name="Continue"/>
            <move x="1" y="2"/>
        </response>
        '''
        # Mock handle_move method
        with patch.object(self.game, 'handle_move') as mock_handle_move:
            self.game.handle_response(xml_response)
            mock_handle_move.assert_called_once()

    ##
    # @Brief Test handling response type gameover.
    def test_handle_response_gameover(self):
        # XML for game over response
        xml_response = '''
        <response type="gameover">
            <status name="X"/>
        </response>
        '''

        # Mock game_over method
        with patch.object(self.game, 'game_over') as mock_game_over:
            self.game.handle_response(xml_response)
            mock_game_over.assert_called_once()

    ##
    # @Brief Test handling response type move.
    def test_handle_move(self):
        # Prepare XML for move
        root = ET.fromstring('''
        <response type="move">
            <status name="Continue"/>
            <move x="1" y="2"/>
        </response>
        ''')

        # Set initial state
        self.game.info_label = MagicMock()
        self.game.board = [[" " for _ in range(3)] for _ in range(3)]
        self.game.buttons = [[MagicMock() for _ in range(3)] for _ in range(3)]

        # Call handle_move
        self.game.handle_move(root)

        # Verify board and player change
        self.assertEqual(self.game.board[1][2], self.game.current_player)
        self.assertEqual(self.game.current_player, 'O')

        # Verify button was updated
        self.game.buttons[1][2].config.assert_called_with(
            text=self.game.current_player,
            state="disabled"
        )

        # Verify info_label was updated
        self.game.info_label.config.assert_called_with(
            text=f"Current player: {self.game.current_player}"
        )

    ##
    # @Brief Test handling response type gameover and player X wins.
    def test_game_over_x_win(self):
        # Prepare game over XML for X win
        root = ET.fromstring('''
        <response type="gameover">
            <status name="X"/>
        </response>
        ''')

        # Mock info_label and disable_all_buttons
        self.game.info_label = MagicMock()
        self.game.disable_all_buttons = MagicMock()

        # Call game_over
        self.game.game_over(root)

        # Verify game state
        self.assertTrue(self.game.gameover)
        self.assertEqual(self.game.game_result, "Player X won")
        self.game.info_label.config.assert_called_with(text="Player X won")
        self.game.disable_all_buttons.assert_called_once()

    ##
    # @Brief Test handling response type gameover and draw.
    def test_game_over_draw(self):
        # Prepare game over XML for draw
        root = ET.fromstring('''
        <response type="gameover">
            <status name="Draw"/>
        </response>
        ''')

        # Mock info_label and disable_all_buttons
        self.game.info_label = MagicMock()
        self.game.disable_all_buttons = MagicMock()

        # Call game_over
        self.game.game_over(root)

        # Verify game state
        self.assertTrue(self.game.gameover)
        self.assertEqual(self.game.game_result, "Draw")
        self.game.info_label.config.assert_called_with(text="Draw")
        self.game.disable_all_buttons.assert_called_once()

    ##
    # @Brief Test disabling buttons.
    def test_disable_all_buttons(self):
        # Create mock buttons
        self.game.buttons = [[MagicMock() for _ in range(3)] for _ in range(3)]

        # Call disable_all_buttons
        self.game.disable_all_buttons()

        # Verify all buttons were disabled
        for row in self.game.buttons:
            for button in row:
                button.config.assert_called_with(state="disabled")

    ##
    # @Brief Test closing game.
    def test_on_close(self):
        # Mock save_game, quit, and close_connection methods
        with patch.object(self.game, 'save_game'), \
                patch.object(self.game.root, 'quit'), \
                patch.object(self.game.esp, 'close_connection'):
            # Capture print output
            with patch('builtins.print') as mock_print:
                self.game.on_close()

                # Verify methods were called
                self.game.save_game.assert_called_once()
                self.game.root.quit.assert_called_once()
                self.game.esp.close_connection.assert_called_once()
                mock_print.assert_called_with("Game closed")

    ##
    # @Brief Test handling response type bot_v_bot.
    def test_handle_bot_v_bot(self):
        # Mock necessary methods
        self.game.disable_all_buttons = MagicMock()
        self.game.back_button = MagicMock()
        self.game.process_bot_move = MagicMock()

        # Call handle_bot_v_bot
        self.game.handle_bot_v_bot()

        # Verify methods were called
        self.game.disable_all_buttons.assert_called_once()
        self.game.back_button.config.assert_called_with(state="disabled")


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