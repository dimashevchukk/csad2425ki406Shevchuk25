import tkinter as tk
from esp32_communication import esp32
import xml.etree.ElementTree as ET


class TicTacToe:
    def __init__(self):
        self.esp = esp32()

        self.root = tk.Tk()
        self.root.geometry('500x600')
        self.root.title('TicTacToe')
        self.root.resizable(False, False)
        self.root.config(bg='black')

        self.game_mode = None
        self.gameover = None
        self.game_result = None
        self.file_name = "game_state.xml"
        self.current_player = 'X'
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.info_label = None

    def start(self):
        self.start_config()
        self.create_main_menu()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

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

    def back_to_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.save_game()
        self.create_main_menu()

    def make_move(self, row, col):
        self.board[row][col] = self.current_player
        self.buttons[row][col].config(text=self.current_player, state="disabled")
        self.send_move(row, col)

        if not self.gameover:
            self.change_player()

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
                elif response_type == "continue":
                    print("Continue")
                elif response_type == "error":
                    error_message = root.text.strip() if root.text else "Unknown error"
                    print(f"Error: {error_message}")
            else:
                print("Error parsing XML response")
        except ET.ParseError:
            print("Error parsing XML response")

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

    def handle_bot_v_bot(self):
        self.disable_all_buttons()
        self.back_button.config(state="disabled")
        self.process_bot_move()

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

    def disable_all_buttons(self):
        for row in self.buttons:
            for button in row:
                button.config(state="disabled")

    def change_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.info_label.config(text=f"Current player: {self.current_player}")

    def on_close(self):
        self.save_game()
        self.root.quit()
        print("Game closed")