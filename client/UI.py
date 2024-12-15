##
# @file
# @brief UI and logic for TicTacToe game
# @author Dmytro Shevchuk KI-406
# @version 4

import tkinter as tk
import xml.etree.ElementTree as ET
from esp32_communication import esp32

##
# @class TicTacToe
# @brief A class for managing the Tic Tac Toe game, including game logic, UI, and communication with ESP32.
class TicTacToe:
    ##
    # @brief Initializes the TicTacToe class.
    # Sets up the game variables, UI elements, and ESP32 communication object.
    def __init__(self):
        self.esp = esp32()

        self.root = tk.Tk()
        self.root.geometry('500x600')
        self.root.title('TicTacToe')
        self.root.resizable(False, False)
        self.root.config(bg='black')

        ## @param game_mode: Stores the current game mode (e.g., "pvp", "pvbot", "botvbot").
        self.game_mode = None
        ## @param gameover: Indicates whether the game has ended.
        self.gameover = None
        ## @param game_result: Stores the result of the game.
        self.game_result = None
        ## @param file_name: Path to the XML file for saving/loading game state.
        self.file_name = "game_state.xml"
        ## @param current_player: The current player ('X' or 'O').
        self.current_player = 'X'
        ## @param buttons: UI buttons for the game board.
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        ## @param board: The game board state.
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        ## @param info_label: Label to display current player information.
        self.info_label = None

    ##
    # @brief Starts the main loop of the game.
    # Configures the starting setup and displays the main menu.
    def start(self):
        self.start_config()
        self.create_main_menu()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    ##
    # @brief Configures the game by connecting to ESP32.
    # Offers the user a choice to input settings manually or load them from a file.
    def start_config(self):
        while True:
            choice = int(input("Start by\n1) Input\n2) Settings txt file\n"))
            if choice == 1:
                status = self.esp.connect()
                print(status)
                break
            elif choice == 2:
                status = self.esp.connect_from_file("connection_settings.txt")
                print(status)
                break
            else:
                print("Invalid choice")

    ##
    # @brief Creates the main menu of the game.
    # Adds buttons for different game modes and the option to load a saved game.
    def create_main_menu(self):
        title_label = tk.Label(self.root, text="Tic Tac Toe", font=("Arial", 24), bg="black", fg="white")
        title_label.pack(pady=20)

        pvp_button = tk.Button(self.root, text="Player VS Player", font=("Arial", 16), width=20, command=lambda: self.start_game("pvp"))
        pvp_button.pack(pady=10)

        pvbot_button = tk.Button(self.root, text="Player VS Bot", font=("Arial", 16), width=20, command=lambda: self.start_game("pvbot"))
        pvbot_button.pack(pady=10)

        botvbot_button = tk.Button(self.root, text="Bot VS Bot", font=("Arial", 16), width=20, command=lambda: self.start_game("botvbot"))
        botvbot_button.pack(pady=10)

        load_game_button = tk.Button(self.root, text="Load Game", font=("Arial", 16), width=20, command=self.load_game)
        load_game_button.pack(pady=120)

    ##
    # @brief Starts a new game in the specified mode.
    # @param game_mode The game mode to start (e.g., "pvp", "pvbot", "botvbot").
    def start_game(self, game_mode):
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.gameover = False
        self.game_result = " "
        self.game_mode = game_mode

        root = ET.Element("request", type="mode")
        mode = ET.SubElement(root, "mode", name=game_mode)
        xml_data = ET.tostring(root, encoding="utf-8", method="xml")

        status = self.esp.send_message(xml_data + b'\n')
        print(status)
        response = self.esp.receive_message()
        print(f"Received: {response}")

        self.create_board()
        self.handle_response(response)

    ##
    # @brief Creates the UI board for the game.
    # Sets up buttons for each cell of the board and displays the current player's turn.
    def create_board(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True)

        for row in range(3):
            row_frame = tk.Frame(frame, bg="black")
            row_frame.pack(pady=2)
            for col in range(3):
                button_frame = tk.Frame(row_frame, width=100, height=100)
                button_frame.grid(row=row, column=col, padx=5, pady=5)
                button_frame.grid_propagate(False)

                button = tk.Button(
                    button_frame,
                    width=5, height=2,
                    text=self.board[row][col],
                    font=("Arial", 56),
                    state="disabled" if self.board[row][col] != " " else "normal",
                    command=lambda r=row, c=col: self.make_move(r, c)
                )
                button.place(relx=0, rely=0, relwidth=1, relheight=1)
                self.buttons[row][col] = button

        self.info_label = tk.Label(frame, text=f"Current player: {self.current_player}", font=("Arial", 20), bg="black", fg="white")
        self.info_label.pack(pady=20)

        self.back_button = tk.Button(self.root, text="Back to Menu", font=("Arial", 14), command=self.back_to_menu, bg="white", fg="black")
        self.back_button.place(x=20, y=20)

    ##
    # @brief Saves the current game state to txt file.
    # Creates an XML structure to save the current game state, including the board,
    # current player, game result, and game mode. The XML is then written to a file.
    def save_game(self):
        root = ET.Element("GameState")
        board_element = ET.SubElement(root, "Board")

        for row in self.board:
            row_element = ET.SubElement(board_element, "Row")
            row_element.text = ",".join(row)

        current_player_element = ET.SubElement(root, "CurrentPlayer")
        current_player_element.text = self.current_player

        game_results_element = ET.SubElement(root, "GameResult")
        game_results_element.text = self.game_result

        game_mode_element = ET.SubElement(root, "GameMode")
        game_mode_element.text = self.game_mode

        tree = ET.ElementTree(root)
        tree.write(self.file_name, encoding="utf-8", xml_declaration=True)
        print(f"Game saved to {self.file_name}")

    ##
    # @brief Loads the current game state from txt file.
    # Load a previously saved game state from an XML file. The board,
    # current player, and game mode are restored. If the game is over,
    # it updates the UI to reflect the game result. Handles errors for missing or corrupted files.
    def load_game(self):
        try:
            tree = ET.parse(self.file_name)
            root = tree.getroot()

            board_element = root.find("Board")
            self.board = [row.text.split(",") for row in board_element.findall("Row")]
            current_player_element = root.find("CurrentPlayer")
            self.current_player = current_player_element.text
            game_mode_element = root.find("GameMode")
            self.game_mode = game_mode_element.text

            self.create_board()

            game_results_element = root.find("GameResult")
            if game_results_element.text != " ":
                self.disable_all_buttons()
                self.info_label.config(text=game_results_element.text)

            print(f"Game loaded from {self.file_name}")
        except FileNotFoundError:
            print(f"Error: File {self.file_name} not found.")
        except ET.ParseError:
            print(f"Error: Failed to parse the XML file {self.file_name}.")

    ##
    # @brief Loads the current game state from txt file.
    # Load a previously saved game state from an XML file. The board,
    # current player, and game mode are restored. If the game is over,
    # it updates the UI to reflect the game result. Handles errors for missing or corrupted files.
    def back_to_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.save_game()
        self.create_main_menu()

    ##
    # @brief Makes a move from current player.
    # Updates the board with the current player's move, sends the move to the server,
    # and switches to the next player if the game is not over.
    # @param row: The row index of the move.
    # @param col: The column index of the move.
    def make_move(self, row, col):
        self.board[row][col] = self.current_player
        self.buttons[row][col].config(text=self.current_player, state="disabled")
        self.send_move(row, col)

        if not self.gameover:
            self.change_player()

    ##
    # @brief Sends a move to the server.
    # Creates an XML message to send the current player's move to the server.
    # The move is then transmitted and the response is handled.
    # @param row: The row index of the move.
    # @param col: The column index of the move.#
    def send_move(self, row, col):
        root = ET.Element("request", type="move")
        player = ET.SubElement(root, "player", name=self.current_player)
        move = ET.SubElement(root, "move", x=str(row), y=str(col))
        tree = ET.ElementTree(root)
        xml_data = ET.tostring(root, encoding="utf-8", method="xml")

        status = self.esp.send_message(xml_data + b'\n')
        print(status)
        response = self.esp.receive_message()
        print(f"Received: {response}")
        self.handle_response(response)

    ##
    # @brief Handles the response received from the server.
    # Handles the server's response after a move is sent.
    # It processes different response types, such as "mode", "move", "gameover"
    # and "error". Based on the response, it triggers corresponding actions.
    # @param response: The XML response from the server.
    def handle_response(self, response):
        try:
            root = ET.fromstring(response)
            if root.tag == "response":
                response_type = root.attrib.get("type")
                if response_type == "mode":
                    mode = root.find("mode").attrib.get("name")
                    if mode == "botvbot":
                        self.handle_bot_v_bot()

                elif response_type == "move":
                    self.handle_move(root)
                elif response_type == "gameover":
                    self.game_over(root)
                elif response_type == "error":
                    error_message = root.text.strip() if root.text else "Unknown error"
                    print(f"Error: {error_message}")
            else:
                print("Error parsing XML response")
        except ET.ParseError:
            print("Error parsing XML response")

    ##
    # @brief Handles the move received from the server.
    # Processes the move information from the server's response, updating the board
    # and switching the player. If game status is not continue, it ends the game.
    # @param root: The parsed XML root element containing the move data.
    def handle_move(self, root):
        status = root.find("status").attrib.get("name")
        move = root.find("move")
        x = int(move.attrib["x"])
        y = int(move.attrib["y"])

        if self.board[x][y] == " ":
            self.change_player()
            self.board[x][y] = self.current_player
            self.buttons[x][y].config(text=self.current_player, state="disabled")

        if status != "Continue":
            self.game_over(root)

    ##
    # @brief Handles the botvbot move received from the server.
    # Disables the game board buttons and the back button, then starts processing the
    # bot's move in a "Bot VS Bot" game mode.
    def handle_bot_v_bot(self):
        self.disable_all_buttons()
        self.back_button.config(state="disabled")
        self.process_bot_move()

    ##
    # @brief Processes the botvbot move received from the server.
    # Processes a move from the bot by receiving the response from the server,
    # updating the board with the bot's move, and checking if the game is over.
    # If the game is not over, it waits before processing the next bot move.
    def process_bot_move(self):
        response = self.esp.receive_message()
        print(f"Received: {response}")

        root = ET.fromstring(response)
        status = root.find("status").attrib.get("name")
        move = root.find("move")
        x = int(move.attrib["x"])
        y = int(move.attrib["y"])

        if self.board[x][y] == " ":
            self.board[x][y] = self.current_player
            self.buttons[x][y].config(text=self.current_player, state="disabled")
            self.change_player()

        if status != "Continue":
            self.game_over(root)
            self.back_button.config(state="active")
        else:
            self.root.after(1000, self.process_bot_move)

    ##
    # @brief Handles the game over.
    # Handles the end of the game based on the server's response.
    # It checks the game status and updates the game result (win, draw) and the UI accordingly.
    # Status X means player X won, as well Y.
    def game_over(self, root):
        status = root.find("status").attrib.get("name")
        if status == "X" or status == "O":
            self.gameover = True
            self.game_result = f"Player {status} won"
            self.info_label.config(text=self.game_result)
            self.disable_all_buttons()
        elif status == "Draw":
            self.gameover = True
            self.game_result = "Draw"
            self.info_label.config(text=self.game_result)
            self.disable_all_buttons()

    ##
    # @brief Disables all buttons.
    # Disables all the game buttons, preventing further moves.
    def disable_all_buttons(self):
        for row in self.buttons:
            for button in row:
                button.config(state="disabled")

    ##
    # @brief Changes the player'
    # Switches the current player between 'X' and 'O', and updates the displayed player in the UI.
    def change_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.info_label.config(text=f"Current player: {self.current_player}")

    ##
    # @brief Handles the close button.
    # Saves the current game state and quits the game when the window is closed.
    # Closes connection with server.
    def on_close(self):
        self.save_game()
        self.root.quit()
        self.esp.close_connection()
        print("Game closed")