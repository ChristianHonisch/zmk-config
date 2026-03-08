param(
    [string]$ZmkRoot = "C:\Daten\GIT\zmk",
    [string]$ConfigRepo = (Get-Location).Path,
    [string]$ToolchainPython = "C:\ncs\toolchains\fd21892d0f\opt\bin\python.exe",
    [ValidateSet("both", "left", "right")][string]$Target = "both",
    [switch]$SkipWestUpdate,
    [switch]$NoDfuZip
)

$setupScript = Join-Path $PSScriptRoot "scripts\setup-build-env.ps1"
$buildScript = Join-Path $PSScriptRoot "scripts\build-firmware.ps1"

& $setupScript -ZmkRoot $ZmkRoot -ConfigRepo $ConfigRepo -ToolchainPython $ToolchainPython -SkipWestUpdate:$SkipWestUpdate
if ($LASTEXITCODE -ne 0) {
    throw "setup-build-env.ps1 failed"
}

& $buildScript -ZmkRoot $ZmkRoot -ConfigRepo $ConfigRepo -ToolchainPython $ToolchainPython -Target $Target -NoDfuZip:$NoDfuZip
if ($LASTEXITCODE -ne 0) {
    throw "build-firmware.ps1 failed"
}
