#include <tinyxml2.h>

String gameMode;
char board[3][3];

void handleModeRequest(tinyxml2::XMLElement* root);
void handlePVPRequest(tinyxml2::XMLElement* root);
void handlePVBotRequest(tinyxml2::XMLElement* root);
void startBotVBot();

std::pair<int, int> randomBotMove();
String checkWin();
void cleanBoard();

void setup()
{
  Serial.begin(115200);
  while (!Serial)
  {
    delay(100);
  } 

  for (int i = 0; i < 3; i++) 
  {
    for (int j = 0; j < 3; j++) 
    {
      board[i][j] = ' ';
    }
  } 
}

void loop()
{
  if (Serial.available() > 0)
  {
    String xmlData = Serial.readStringUntil('\n');
    tinyxml2::XMLDocument doc;
    doc.Parse(xmlData.c_str());

    tinyxml2::XMLElement* root = doc.FirstChildElement("request");
    if (root)
    {
      const char* type = root->Attribute("type");
      if (type)
      {
        if (strcmp(type, "move") == 0)
        {
          if (gameMode == "pvp") handlePVPRequest(root);              
          else if (gameMode == "pvbot") handlePVBotRequest(root);                                
        }
        else if (strcmp(type, "mode") == 0)
        { 
          cleanBoard();         
          handleModeRequest(root);          
        }
        else
        {
          Serial.println("Unknown request type");
        }
      }
    }
  }
}

void handleModeRequest(tinyxml2::XMLElement* root)
{
  tinyxml2::XMLElement* mode = root->FirstChildElement("mode");
  if (mode)
  {
    const char* modeName = mode->Attribute("name");
    if (modeName)
    {       
      gameMode = String(modeName);      

      tinyxml2::XMLDocument responseDoc;
      tinyxml2::XMLElement* responseRoot = responseDoc.NewElement("response");
      responseRoot->SetAttribute("type", "mode");
      responseDoc.InsertFirstChild(responseRoot);

      tinyxml2::XMLElement* responseMode = responseDoc.NewElement("mode");
      responseMode->SetAttribute("name", gameMode.c_str());
      responseRoot->InsertEndChild(responseMode);

      tinyxml2::XMLPrinter printer;
      responseDoc.Print(&printer);
      Serial.println(printer.CStr());
      
      if (gameMode == "botvbot")
      {
        startBotVBot();
      }
    }
  }
}

void handlePVPRequest(tinyxml2::XMLElement* root)
{
  tinyxml2::XMLElement* player = root->FirstChildElement("player");
  if (player)
  {
    const char* playerName = player->Attribute("name");
    tinyxml2::XMLElement* move = root->FirstChildElement("move");
    if (move)
    {
      const char* x_str = move->Attribute("x");
      const char* y_str = move->Attribute("y");
      
      int x = atoi(x_str);
      int y = atoi(y_str);

      board[x][y] = playerName[0];  
      String gameStatus = checkWin();

      tinyxml2::XMLDocument responseDoc;
      tinyxml2::XMLElement* responseRoot = responseDoc.NewElement("response");
      responseRoot->SetAttribute("type", "gameover"); 
      responseDoc.InsertFirstChild(responseRoot);

      tinyxml2::XMLElement* responseStatus = responseDoc.NewElement("status");
      responseStatus->SetAttribute("name", gameStatus.c_str());
      responseRoot->InsertEndChild(responseStatus);

      tinyxml2::XMLPrinter printer;
      responseDoc.Print(&printer);
      Serial.println(printer.CStr());
    }
  }
}

void handlePVBotRequest(tinyxml2::XMLElement* root)
{
  tinyxml2::XMLElement* player = root->FirstChildElement("player");
  if (player)
  {
    const char* playerName = player->Attribute("name");
    tinyxml2::XMLElement* move = root->FirstChildElement("move");
    if (move)
    {
      const char* x_str = move->Attribute("x");
      const char* y_str = move->Attribute("y");
      
      int x = atoi(x_str);
      int y = atoi(y_str);

      board[x][y] = playerName[0];  
      String gameStatus = checkWin();

      if (gameStatus == "Continue")
      {
        std::tie(x, y) = randomBotMove();      
        board[x][y] = (playerName[0] == 'X') ? 'O' : 'X';
        gameStatus = checkWin();
      }      
            
      tinyxml2::XMLDocument responseDoc;
      tinyxml2::XMLElement* responseRoot = responseDoc.NewElement("response");
      responseRoot->SetAttribute("type", "move"); 
      responseDoc.InsertFirstChild(responseRoot);

      tinyxml2::XMLElement* responseStatus = responseDoc.NewElement("status");
      responseStatus->SetAttribute("name", gameStatus.c_str());
      responseRoot->InsertEndChild(responseStatus);

      tinyxml2::XMLElement* responseMove = responseDoc.NewElement("move");
      responseMove->SetAttribute("x", x);
      responseMove->SetAttribute("y", y);
      responseRoot->InsertEndChild(responseMove);      

      tinyxml2::XMLPrinter printer;
      responseDoc.Print(&printer);
      Serial.println(printer.CStr());
    }
  }
}

void startBotVBot()
{
  int x, y;
  String gameStatus;
  char currentBot = 'X';

  while(true)
  {
    std::tie(x, y) = randomBotMove();      
    board[x][y] = currentBot;
    currentBot = (currentBot == 'X') ? 'O' : 'X';
    gameStatus = checkWin();

    tinyxml2::XMLDocument responseDoc;
    tinyxml2::XMLElement* responseRoot = responseDoc.NewElement("response");
    responseRoot->SetAttribute("type", "move"); 
    responseDoc.InsertFirstChild(responseRoot);

    tinyxml2::XMLElement* responseStatus = responseDoc.NewElement("status");
    responseStatus->SetAttribute("name", gameStatus.c_str());
    responseRoot->InsertEndChild(responseStatus);

    tinyxml2::XMLElement* responseMove = responseDoc.NewElement("move");
    responseMove->SetAttribute("x", x);
    responseMove->SetAttribute("y", y);
    responseRoot->InsertEndChild(responseMove);      

    tinyxml2::XMLPrinter printer;
    responseDoc.Print(&printer);
    Serial.println(printer.CStr());

    if (gameStatus != "Continue") break;    
  }
}

std::pair<int, int> randomBotMove()
{
  int x, y;
    do 
    {
      x = rand() % 3;
      y = rand() % 3;
    } 
    while (board[x][y] != ' ');

    return {x, y};
}

String checkWin() 
{
  //Rows
  for (int i = 0; i < 3; i++) 
  {
    if (board[i][0] != ' ' && board[i][0] == board[i][1] && board[i][1] == board[i][2]) 
    {
      return String(board[i][0]);
    }
  }

  //Cols
  for (int i = 0; i < 3; i++) 
  {
    if (board[0][i] != ' ' && board[0][i] == board[1][i] && board[1][i] == board[2][i]) 
    {
      return String(board[0][i]);
    }
  }

  //Diagonals
  if (board[0][0] != ' ' && board[0][0] == board[1][1] && board[1][1] == board[2][2]) 
  {
    return String(board[0][0]);
  }

  if (board[0][2] != ' ' && board[0][2] == board[1][1] && board[1][1] == board[2][0]) 
  {
    return String(board[0][2]);
  }

  //Draw
  bool isDraw = true;
  for (int i = 0; i < 3; i++) 
  {
    for (int j = 0; j < 3; j++) 
    {
      if (board[i][j] == ' ') 
      {
        isDraw = false;
        break;
      }
    }
    if (!isDraw) 
    {
      break;
    }
  }

  if (isDraw) 
  {
    return "Draw";  
  }

  return "Continue";
}

void cleanBoard()
{
  for (int i = 0; i < 3; i++) 
  {
    for (int j = 0; j < 3; j++) 
    {
      board[i][j] = ' ';
    }
  } 
}
