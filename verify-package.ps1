$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$portable = Join-Path $PWD "dist\PalPal\PalPal.exe"
$installer = Join-Path $PWD "dist\PalPal-Setup.exe"
$report = Join-Path $PWD "dist\packaged-smoke.json"
$installReport = Join-Path $PWD "dist\installed-smoke.json"
$installDir = Join-Path $env:TEMP ("PalPal-Verify-" + [guid]::NewGuid().ToString())
function Run-Smoke($executable, $output) {
    $process = Start-Process -FilePath $executable -ArgumentList @('--smoke-report', ('"' + $output + '"')) -PassThru
    if (-not $process.WaitForExit(30000)) { $process.Kill(); throw "Packaged smoke timed out" }
    if ($process.ExitCode -ne 0 -or -not (Test-Path $output)) { throw "Packaged smoke failed" }
    $result = Get-Content $output -Raw | ConvertFrom-Json
    if (-not $result.passed) { throw "Packaged smoke reported failure" }
}
Run-Smoke $portable $report
try {
    $setup = Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',('/DIR="' + $installDir + '"')) -Wait -PassThru
    if ($setup.ExitCode -ne 0) { throw "Silent install failed" }
    Run-Smoke (Join-Path $installDir 'PalPal.exe') $installReport
} finally {
    $uninstaller = Join-Path $installDir 'unins000.exe'
    if (Test-Path $uninstaller) {
        $uninstall = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
        if ($uninstall.ExitCode -ne 0) { throw "Silent uninstall failed" }
    }
    if (Test-Path (Join-Path $installDir 'PalPal.exe')) { throw "Uninstall left the executable behind" }
}
