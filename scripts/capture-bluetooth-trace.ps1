param(
    [string]$ProfilePath = ".\BluetoothStack.wprp",
    [string]$OutputPath = ".\BthTrace.etl"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command wpr.exe -ErrorAction SilentlyContinue)) {
    throw "wpr.exe not found. Install Windows Performance Toolkit."
}

if (-not (Test-Path $ProfilePath)) {
    Write-Host "Downloading Bluetooth tracing profile..."
    Invoke-WebRequest `
        -Uri "https://github.com/Microsoft/busiotools/raw/master/bluetooth/tracing/BluetoothStack.wprp" `
        -OutFile $ProfilePath
}

Write-Host "Starting Bluetooth ETW trace..."
wpr.exe -start "$ProfilePath!BluetoothStack" -filemode

Write-Host ""
Write-Host "Reproduce the disconnect storm now."
Write-Host "Press Enter to stop tracing."
[void][System.Console]::ReadLine()

Write-Host "Stopping trace..."
wpr.exe -stop $OutputPath

Write-Host ""
Write-Host "Trace saved to: $OutputPath"
Write-Host "Open it in Windows Performance Analyzer (WPA)."
