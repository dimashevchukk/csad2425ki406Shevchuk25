void setup() 
{
  Serial.begin(115200);
  while (!Serial) 
  {
    delay(100); 
  }   
}

void loop() {
  if (Serial.available() > 0) 
  {
    String request = Serial.readStringUntil('\n');
    String response = "SERVER MODIFIED: " + request;
    Serial.println(response);
  }
}