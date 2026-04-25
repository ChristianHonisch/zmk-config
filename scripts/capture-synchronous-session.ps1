param(
    [string]$LeftComPort = "COM5",
    [string]$RightComPort = "COM3",
    [int]$BaudRate = 115200,
    [string]$OutputDir = ".\logs",
    [string]$ProfilePath = ".\BluetoothStack.wprp"
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

$RepoRoot = Split-Path $PSScriptRoot -Parent
$PythonExe = Join-Path $RepoRoot ".venv-tools\Scripts\python.exe"
$SerialScript = Join-Path $PSScriptRoot "capture-ht-log-both.py"

if (-not (Test-Path $PythonExe)) {
    throw "Python not found: $PythonExe"
}

if (-not (Test-Path $SerialScript)) {
    throw "Serial capture script not found: $SerialScript"
}

if (-not (Get-Command wpr.exe -ErrorAction SilentlyContinue)) {
    throw "wpr.exe not found. Install Windows Performance Toolkit."
}

if (-not (Test-IsAdministrator)) {
    $argList = @(
        "-ExecutionPolicy", "Bypass",
        "-File", ('"' + $PSCommandPath + '"'),
        "-LeftComPort", $LeftComPort,
        "-RightComPort", $RightComPort,
        "-BaudRate", "$BaudRate",
        "-OutputDir", ('"' + $OutputDir + '"'),
        "-ProfilePath", ('"' + $ProfilePath + '"')
    )
    Write-Host "Requesting elevation for ETW capture..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList $argList
    exit 0
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$keyboardLog = Join-Path $OutputDir "synchronous-log-$timestamp.log"
$etlPath = Join-Path $OutputDir "synchronous-log-$timestamp.etl"
$stopFile = Join-Path $OutputDir "synchronous-log-$timestamp.stop"

if (-not (Test-Path $ProfilePath)) {
    Write-Host "Downloading Bluetooth tracing profile..."
    Invoke-WebRequest `
        -Uri "https://github.com/Microsoft/busiotools/raw/master/bluetooth/tracing/BluetoothStack.wprp" `
        -OutFile $ProfilePath
}

$pythonArgs = @(
    $SerialScript,
    "--left", $LeftComPort,
    "--right", $RightComPort,
    "--baud", "$BaudRate",
    "--output-file", $keyboardLog,
    "--stop-file", $stopFile
)

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = New-Object System.Diagnostics.ProcessStartInfo
$proc.StartInfo.FileName = $PythonExe
$proc.StartInfo.Arguments = [string]::Join(' ', ($pythonArgs | ForEach-Object {
    if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
}))
$proc.StartInfo.UseShellExecute = $false
$proc.StartInfo.RedirectStandardOutput = $false
$proc.StartInfo.RedirectStandardError = $false

Write-Host "Starting synchronized capture..." -ForegroundColor Yellow
Write-Host "  Keyboard log: $keyboardLog"
Write-Host "  ETW trace:    $etlPath"
Write-Host "  Left port:    $LeftComPort"
Write-Host "  Right port:   $RightComPort"

$null = $proc.Start()

try {
    Write-Host "Starting Bluetooth ETW trace..." -ForegroundColor Yellow
    wpr.exe -start "$ProfilePath!BluetoothStack" -filemode | Out-Null

    Write-Host ""
    Write-Host "Capture is running. Reproduce the issue now." -ForegroundColor Green
    Write-Host "Press Enter to stop both captures."
    [void][System.Console]::ReadLine()
}
finally {
    Write-Host "Stopping Bluetooth ETW trace..." -ForegroundColor Yellow
    wpr.exe -stop $etlPath | Out-Null

    New-Item -ItemType File -Path $stopFile -Force | Out-Null
    if (-not $proc.WaitForExit(5000)) {
        Stop-Process -Id $proc.Id -Force
    }

    Remove-Item -Path $stopFile -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Saved synchronized session:" -ForegroundColor Green
    Write-Host "  Keyboard log: $keyboardLog"
    Write-Host "  ETW trace:    $etlPath"
}
