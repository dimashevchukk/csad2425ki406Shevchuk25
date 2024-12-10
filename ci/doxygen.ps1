#---------------------------------CONFIGURABLE VARIABLES---------------------------------
$doxygenInstallerUrl = "https://doxygen.nl/files/doxygen-1.12.0-setup.exe"
$doxygenInstallerPath = "$env:TEMP\doxygen-setup.exe"
$projectDir = Join-Path -Path $PSScriptRoot -ChildPath ".."
$outputDir = "$projectDir\docs"
$doxyfilePath = "$projectDir\Doxyfile"
# ---------------------------------------------------------------------------------------

function CheckDoxygen
{
    Write-Output "Checking Doxygen..."
    $doxygenPath = (Get-Command "doxygen" -ErrorAction SilentlyContinue).Source

    if (-not $doxygenPath)
    {
        Write-Output "Doxygen not found. Downloading..."
        Invoke-WebRequest -Uri $doxygenInstallerUrl -OutFile $doxygenInstallerPath -UseBasicParsing
        Start-Process -FilePath $doxygenInstallerPath -ArgumentList "/S" -Wait
        $doxygenPath = (Get-Command "doxygen" -ErrorAction SilentlyContinue).Source

        if (-not $doxygenPath)
        {
            Write-Output "Doxygen installation failed."
            exit 1
        }

        $doxygenPath = "C:\Program Files\doxygen\bin"
        [System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$doxygenPath", [System.EnvironmentVariableTarget]::Machine)
    }
    else
    {
        Write-Output "Doxygen is installed."
    }
}

function CreateConfig
{
    if (-not (Test-Path $doxyfilePath))
    {
        Write-Output "Generating Doxygen config..."
        Start-Process -FilePath "doxygen" -ArgumentList "-g $doxyfilePath" -Wait
    }
}

function UpdateConfig
{
    if (-not (Test-Path $outputDir))
    {
        New-Item -ItemType Directory -Path $outputDir
    }

    (Get-Content $doxyfilePath) -replace 'OUTPUT_DIRECTORY.*', "OUTPUT_DIRECTORY = $outputDir" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'INPUT.*', "INPUT = $projectDir" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'RECURSIVE.*', "RECURSIVE = YES" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'EXCLUDE .*', "EXCLUDE = $projectDir\lib" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'FILE_PATTERNS.*', "FILE_PATTERNS = *.cpp *.h *.py *.ino *.c *.cc" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'EXTENSION_MAPPING.*', "EXTENSION_MAPPING = ino=C++" | Set-Content $doxyfilePath
    (Get-Content $doxyfilePath) -replace 'EXTRACT_ALL.*', "EXTRACT_ALL = YES" | Set-Content $doxyfilePath
}

function GenerateDocumentation
{
    Write-Output "Generating documentation..."
    Start-Process -FilePath "doxygen" -ArgumentList "$doxyfilePath" -Wait
    Write-Output "Documentation generation completed."
}

CheckDoxygen
CreateConfig
UpdateConfig
GenerateDocumentation