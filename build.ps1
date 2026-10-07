param([switch]$RequireInstaller)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
py -m venv .build-venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }
& .\.build-venv\Scripts\python.exe -m pip install -r requirements.txt "pyinstaller>=6,<7"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& .\.build-venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
if (Get-Command node -ErrorAction SilentlyContinue) {
    node tests/extension.test.cjs
    if ($LASTEXITCODE -ne 0) { throw "Extension tests failed" }
}
& .\.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name PalPal --paths . --add-data "assets;assets" --add-data "data;data" desktop/launcher.py
if ($LASTEXITCODE -ne 0) { throw "Desktop build failed" }
Compress-Archive -Path dist/PalPal,extension -DestinationPath dist/PalPal-portable.zip -Force
$compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
$compilerPath = if ($compiler) { $compiler.Source } else { Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe" }
if (-not (Test-Path $compilerPath)) {
    if ($RequireInstaller) { throw "Inno Setup compiler missing; installer is required" }
    Write-Host "Portable build ready. Install Inno Setup 6 to compile the installer."
    exit 0
}
& $compilerPath packaging/PalPal.iss
if ($LASTEXITCODE -ne 0) { throw "Installer compilation failed" }
