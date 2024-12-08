### **Tic Tac Toe 3x3**
This repository created for CSAD labs by Shevchuk Dmytro, student of KI-406.

### Task 
My var is 25 - tik-tac-toe 3x3, Congif format - XML

### Project Overview
This project implements a Tic Tac Toe 3x3 game with three different gameplay modes.
The game modes are dynamically managed based on the user's selection in the main menu, with configurations handled in XML format:
1. Player vs Player
2. Player vs Bot
3. Bot vs Bot

### Architecture
1. Client: Python
  UI: Tkinter is used to create an interactive graphical interface where players can select game modes and make moves on the 3x3 grid.  
  Logic: Sends on server player`s choises(game mode, moves, data save).
  UT: Using framework unittest to mock board and test communication and logic.

2. Server: C++ on ESP32
  Hardware: ESP32 CH340 Type-C (WiFi Bluetooth WROOM-32) microcontroller.
  Logic: Receives XML data from the client, processes game logic based on the selected mode, and returns the result in XML format.

4. Configuration Format: XML
The game configuration and data exchange between the client and server are managed in XML format.

### Getting Started
1. Clone the repository:
git clone https://github.com/dimashevchukk/csad2425ki406Shevchuk25.git

2. Set up the environment:
  2.1 Install Python dependencies (client/requirements.txt).
  2.2 Include tinyxml2 (lib/tinyxml2).

3. Flash the ESP32:
Load the server code onto the ESP32 using Arduino IDE.

4. Run the game:
  4.1 Connect ESP32 with loaded code.
  4.2 Start the client by running the main Python script.
  4.3 Input your COM port and baudrate or just write it in client/connection_settings.txt in format:
  <port>
  <baudrate>

Instead of steps 2.2 and 3 you can open PowerShell in root folder and run ci\script.ps1 <COM port> <baudrate>.
Script using arduino-cli so u need to install it manual and add as a system path. 
Script will check arduino-cli, install tinyxml2 to folder "lib" if u hadn`t, compile and upload sketch to board,
build .bin files to folder "deploy" and run tests saving results to folder "test-reports".