#---------------------------------CONFIGURABLE VARIABLES---------------------------------
param (
    [string]$port,
    [int]$baudrate
)

$board = "esp32:esp32:esp32wrover"
$sketch = "E:\NULP\4course\1sm\APKS\TicTacToe\csad2425ki406Shevchuk25\server\server.ino"
$deployFolder = "E:\NULP\4course\1sm\APKS\TicTacToe\csad2425ki406Shevchuk25\deploy"
# ---------------------------------------------------------------------------------------

function CheckArduinoCLI
{
    if (-not (Get-Command arduino-cli -ErrorAction SilentlyContinue))
    {
        Write-Output "Arduino-cli not found."
        exit 1
    }

    $version = & arduino-cli version
    Write-Output "Arduino-cli version: $version"
}

function CompileSketch
{
    Write-Output "Sketch compilation..."
    if (-not (Test-Path $deployFolder))
    {
        New-Item -ItemType Directory -Path $deployFolder
    }

    & arduino-cli compile --fqbn $board $sketch --output-dir $deployFolder

    if ($LASTEXITCODE -ne 0)
    {
        Write-Output "Error during compilation."
        exit 1
    }
    Write-Output "Compilated successfull."
}

function UploadSketch
{
    Write-Output "Uploading sketch to esp32 through $port..."
    & arduino-cli upload -p $port --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0)
    {
        Write-Output "Error during uploading."
        exit 1
    }
    Write-Output "Uploaded successfull."
}

function RunTests
{
    Write-Output "Running tests..."
    python -m pytest --junitxml=test-reports/results.xml client/tests.py

    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "Tests passed successfully."
    }
    else
    {
        Write-Host "Tests failed. Check logs for details."
        exit 1
    }
}

CheckArduinoCLI
CompileSketch
UploadSketch
RunTests