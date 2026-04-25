param(
    [string]$ZmkRoot = "C:\Daten\GIT\zmk",
    [string]$ConfigRepo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ToolchainPython = "C:\ncs\toolchains\fd21892d0f\opt\bin\python.exe",
    [ValidateSet("both", "left", "right")][string]$Target = "both",
    [switch]$NoDfuZip
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Convert-ToCMakePath {
    param([string]$PathValue)
    return $PathValue.Replace('\', '/')
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$What
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$What failed (exit code $LASTEXITCODE)"
    }
}

function Invoke-InDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][scriptblock]$Script
    )

    Push-Location $Path
    try {
        & $Script
    }
    finally {
        Pop-Location
    }
}

function Resolve-ToolchainPython {
    param([string]$PreferredPath)

    if ($PreferredPath -and (Test-Path $PreferredPath)) {
        return $PreferredPath
    }

    $candidates = Get-ChildItem "C:\ncs\toolchains\*\opt\bin\python.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending

    if ($candidates.Count -gt 0) {
        return $candidates[0].FullName
    }

    throw "No nRF toolchain Python found. Pass -ToolchainPython explicitly."
}

function Assert-ZephyrEnvNotMixed {
    $vars = @("ZEPHYR_BASE", "ZEPHYR_TOOLCHAIN_VARIANT", "ZEPHYR_SDK_INSTALL_DIR")
    foreach ($name in $vars) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $lower = $value.ToLowerInvariant()
            if ($lower.Contains("c:\\ncs") -and $lower.Contains("zephyr")) {
                throw "Environment variable $name points to NCS Zephyr ($value). Open a clean shell or unset ZEPHYR_* variables."
            }
        }
    }
}

function Invoke-ZmkBuild {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string]$ZmkApp,
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string]$ModulesPath,
        [Parameter(Mandatory = $true)][string]$TargetName,
        [Parameter(Mandatory = $true)][string]$Shield,
        [Parameter(Mandatory = $true)][string]$Board,
        [string]$Snippet = ""
    )

    $buildDir = Join-Path $ZmkApp "build\$TargetName"
    $moduleDirs = @()
    if (Test-Path $ModulesPath) {
        $moduleDirs = @(Get-ChildItem -Directory $ModulesPath | ForEach-Object { $_.FullName })
    }

    $configPathCMake = Convert-ToCMakePath $ConfigPath
    $westArgs = @("-m", "west", "build", "-p", "-d", $buildDir, "-b", $Board)
    if (-not [string]::IsNullOrWhiteSpace($Snippet)) {
        $westArgs += @("-S", $Snippet)
    }
    $westArgs += @("--", "-DSHIELD=$Shield", "-DZMK_CONFIG=$configPathCMake")
    if ($moduleDirs.Count -gt 0) {
        $extraModules = ($moduleDirs | ForEach-Object { Convert-ToCMakePath $_ }) -join ";"
        $westArgs += "-DZMK_EXTRA_MODULES=$extraModules"
    }

    Write-Host "=== Building $TargetName ===" -ForegroundColor Yellow
    Invoke-InDirectory -Path $ZmkApp -Script {
        Invoke-Checked -FilePath $Python -Arguments $westArgs -What "west build $TargetName"
    }
}

function New-DfuZip {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigRepo,
        [Parameter(Mandatory = $true)][string]$TargetName,
        [Parameter(Mandatory = $true)][string]$BuildDir
    )

    $venvPython = Join-Path $ConfigRepo ".venv-tools\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "venv python not found: $venvPython"
    }

    $hexPath = Join-Path $BuildDir "zephyr\zmk.hex"
    if (-not (Test-Path $hexPath)) {
        throw "HEX not found for DFU package: $hexPath"
    }

    $outZip = Join-Path (Join-Path $ConfigRepo "scripts") "$TargetName-zmk-dfu.zip"

    $args = @(
        "-I", "-m", "nordicsemi", "dfu", "genpkg",
        "--dev-type", "0x0052",
        "--application", $hexPath,
        $outZip
    )

    Invoke-Checked -FilePath $venvPython -Arguments $args -What "dfu package generation for $TargetName"
    Write-Host "DFU zip: $outZip" -ForegroundColor Green
}

$zmkApp = Join-Path $ZmkRoot "app"
$configPath = Join-Path $ConfigRepo "config"
$modulesPath = Join-Path $ConfigRepo "modules"
$westDir = Join-Path $ZmkRoot ".west"

if (-not (Test-Path $zmkApp)) { throw "ZMK app path not found: $zmkApp" }
if (-not (Test-Path $configPath)) { throw "Config path not found: $configPath" }
if (-not (Test-Path $westDir)) { throw "West workspace not initialized at $ZmkRoot. Run scripts/setup-build-env.ps1 first." }

Assert-ZephyrEnvNotMixed

$python = Resolve-ToolchainPython -PreferredPath $ToolchainPython
Write-Host "Using toolchain python: $python" -ForegroundColor Cyan
Invoke-Checked -FilePath $python -Arguments @("-m", "west", "--version") -What "west availability check"

$toolchainBin = Split-Path -Parent $python
$env:Path = "$toolchainBin;$($env:Path)"
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { throw "cmake not found in PATH after adding toolchain bin" }
if (-not (Get-Command ninja -ErrorAction SilentlyContinue)) { throw "ninja not found in PATH after adding toolchain bin" }

$targets = @()
if ($Target -eq "both" -or $Target -eq "left") {
    $targets += [pscustomobject]@{ TargetName = "hillside_view_left-nice_nano_nrf52840_zmk"; Shield = "hillside_view_left nice_view"; Board = "nice_nano/nrf52840/zmk"; Snippet = "zmk-usb-logging" }
}
if ($Target -eq "both" -or $Target -eq "right") {
    $targets += [pscustomobject]@{ TargetName = "hillside_view_right-nice_nano_nrf52840_zmk"; Shield = "hillside_view_right nice_view"; Board = "nice_nano/nrf52840/zmk"; Snippet = "" }
}

foreach ($t in $targets) {
    Invoke-ZmkBuild -Python $python -ZmkApp $zmkApp -ConfigPath $configPath -ModulesPath $modulesPath -TargetName $t.TargetName -Shield $t.Shield -Board $t.Board -Snippet $t.Snippet
    if (-not $NoDfuZip) {
        $buildDir = Join-Path $zmkApp "build\$($t.TargetName)"
        New-DfuZip -ConfigRepo $ConfigRepo -TargetName $t.TargetName -BuildDir $buildDir
    }
}

Write-Host "Done." -ForegroundColor Green
