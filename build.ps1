$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Create .venv with Python 3.10 and install requirements.txt first.'
}
$taskAssets = (Join-Path $taskRoot 'app/assets') + ';assets'
& $taskPython -m PyInstaller --noconfirm --clean --onedir --windowed --name EmailManager --add-data $taskAssets --hidden-import PyQt5.sip --collect-all selenium --distpath (Join-Path $taskRoot 'dist') --workpath (Join-Path $taskRoot 'build') --specpath (Join-Path $taskRoot 'build') (Join-Path $taskRoot 'app/main.py')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
$taskBundle = Join-Path $taskRoot 'dist/EmailManager'
Copy-Item -LiteralPath (Join-Path $taskRoot 'LICENSE') -Destination $taskBundle
Copy-Item -LiteralPath (Join-Path $taskRoot 'README.md') -Destination (Join-Path $taskBundle 'README-RU.md')
Copy-Item -LiteralPath (Join-Path $taskRoot 'README.en.md') -Destination (Join-Path $taskBundle 'README-EN.md')
Compress-Archive -Path $taskBundle -DestinationPath (Join-Path $taskRoot 'dist/EmailManager-Windows-x64.zip') -Force
