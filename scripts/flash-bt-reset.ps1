param(
    [string]$LeftComPort = "COM27",
    [string]$RightComPort = "COM6",
    [int]$BaudRate = 115200
)

$ErrorActionPreference = "Stop"

$ResetZip = "settings_reset-nice_nano-zmk-dfu.zip"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$VenvPython = Join-Path $RepoRoot ".venv-tools\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "venv python not found: $VenvPython"
}

function Invoke-DfuFlash {
    param(
        [Parameter(Mandatory = $true)][string]$ComPort,
        [Parameter(Mandatory = $true)][string]$ZipFile
    )

    $zipPath = Join-Path $PSScriptRoot $ZipFile
    if (-not (Test-Path $zipPath)) {
        throw "ZIP not found: $zipPath"
    }

    Write-Host "Flashing $ZipFile -> $ComPort" -ForegroundColor Cyan
    $args = @(
        "-I", "-m", "nordicsemi",
        "dfu", "serial",
        "-pkg", "$zipPath",
        "-p", $ComPort,
        "-b", "$BaudRate"
    )

    & $VenvPython @args

    if ($LASTEXITCODE -ne 0) {
        throw "Flashing failed for $ComPort"
    }
}

Write-Host "== Bluetooth reset flash ==" -ForegroundColor Yellow
Write-Host "Using ports: left=$LeftComPort right=$RightComPort" -ForegroundColor Yellow
Invoke-DfuFlash -ComPort $LeftComPort -ZipFile $ResetZip
Start-Sleep -Seconds 2
Invoke-DfuFlash -ComPort $RightComPort -ZipFile $ResetZip
Write-Host "Done. Both halves flashed with settings_reset." -ForegroundColor Green
