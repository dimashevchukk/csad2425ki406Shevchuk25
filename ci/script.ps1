#---------------------------------CONFIGURABLE VARIABLES---------------------------------
param (
    [string]$port,
    [int]$baudrate
)

$board = "esp32:esp32:esp32wrover"
$sketch = "server/server.ino"
$deployFolder = "deploy"
$libFolder = "lib"
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

function CheckLibraries
{
    Write-Output "Checking libraries..."
    if (-not (Test-Path $libFolder))
    {
        New-Item -ItemType Directory -Path $libFolder
    }

    if (-not (Test-Path "$libFolder/tinyxml2"))
    {
        Write-Output "Cloning tinyxml2 library..."
        & git clone https://github.com/leethomason/tinyxml2.git "$libFolder/tinyxml2"
        if ($LASTEXITCODE -ne 0)
        {
            Write-Output "Error cloning tinyxml2."
            exit 1
        }
    }
    Write-Output "Libraries prepared."
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
    if ($env:GITHUB_ACTIONS -eq $true) # Check if running in GitHub Actions
    {
        Write-Output "Running in GitHub Actions - skipping device upload."
        return
    }

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
CheckLibraries
CompileSketch
UploadSketch
RunTests