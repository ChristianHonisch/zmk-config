param(
    [string]$LeftComPort = "COM27",
    [string]$RightComPort = "COM6",
    [int]$BaudRate = 115200,
    [int]$Touch = 1200,
    [switch]$NoTouch
)

$ErrorActionPreference = "Stop"

$LeftZip = "hillside_view_left-nice_nano-zmk-dfu.zip"
$RightZip = "hillside_view_right-nice_nano-zmk-dfu.zip"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$NrfUtil = Join-Path $RepoRoot ".venv-tools\Scripts\adafruit-nrfutil.exe"
if (-not (Test-Path $NrfUtil)) {
    throw "adafruit-nrfutil not found in repo venv: $NrfUtil"
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
        "--verbose", "dfu", "serial",
        "--package", "$zipPath",
        "-p", $ComPort,
        "-b", "$BaudRate",
        "--singlebank"
    )

    if (-not $NoTouch) {
        $args += @("--touch", "$Touch")
    }

    & $NrfUtil @args

    if ($LASTEXITCODE -ne 0) {
        throw "Flashing failed for $ComPort"
    }
}

Write-Host "== Firmware flash ==" -ForegroundColor Yellow
Write-Host "Using ports: left=$LeftComPort right=$RightComPort" -ForegroundColor Yellow
Invoke-DfuFlash -ComPort $LeftComPort -ZipFile $LeftZip
Start-Sleep -Seconds 2
Invoke-DfuFlash -ComPort $RightComPort -ZipFile $RightZip
Write-Host "Done. Left/right firmware flashed." -ForegroundColor Green
