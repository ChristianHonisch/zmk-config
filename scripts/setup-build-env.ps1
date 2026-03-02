param(
    [string]$ZmkRoot = "C:\Daten\GIT\zmk",
    [string]$ConfigRepo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ToolchainPython = "C:\ncs\toolchains\fd21892d0f\opt\bin\python.exe",
    [switch]$SkipWestUpdate
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Normalize-YamlScalar {
    param([string]$Value)

    $trimmed = $Value.Trim()
    if (($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) -or
        ($trimmed.StartsWith("'") -and $trimmed.EndsWith("'"))) {
        return $trimmed.Substring(1, $trimmed.Length - 2)
    }
    return $trimmed
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

function Ensure-WestWorkspace {
    param(
        [string]$ZmkRoot,
        [string]$Python,
        [bool]$RunWestUpdate
    )

    $westDir = Join-Path $ZmkRoot ".west"
    if (-not (Test-Path $westDir)) {
        Write-Host "Initializing west workspace in $ZmkRoot" -ForegroundColor Yellow
        Invoke-InDirectory -Path $ZmkRoot -Script {
            Invoke-Checked -FilePath $Python -Arguments @("-m", "west", "init", "-l", "app") -What "west init"
        }
    }

    if ($RunWestUpdate) {
        Write-Host "Updating west workspace" -ForegroundColor Yellow
        Invoke-InDirectory -Path $ZmkRoot -Script {
            Invoke-Checked -FilePath $Python -Arguments @("-m", "west", "update") -What "west update"
        }
    }
}

function Get-ExternalModuleSpecs {
    param([string]$WestYmlPath)

    if (-not (Test-Path $WestYmlPath)) {
        throw "west.yml not found: $WestYmlPath"
    }

    $content = Get-Content -Raw -Path $WestYmlPath

    $remotes = @{}
    $remotePattern = '(?ms)-\s+name:\s*(?<name>[^\r\n#]+)\s*\r?\n\s*url-base:\s*(?<url>[^\r\n#]+)'
    foreach ($m in [regex]::Matches($content, $remotePattern)) {
        $name = Normalize-YamlScalar $m.Groups["name"].Value
        $url = Normalize-YamlScalar $m.Groups["url"].Value
        $remotes[$name] = $url
    }

    $specs = @()
    $projectPattern = '(?ms)-\s+name:\s*(?<name>[^\r\n#]+)\s*\r?\n\s*remote:\s*(?<remote>[^\r\n#]+)\s*\r?\n\s*revision:\s*(?<rev>[^\r\n#]+)'
    foreach ($m in [regex]::Matches($content, $projectPattern)) {
        $name = Normalize-YamlScalar $m.Groups["name"].Value
        if ($name -eq "zmk") {
            continue
        }

        $remote = Normalize-YamlScalar $m.Groups["remote"].Value
        $revision = Normalize-YamlScalar $m.Groups["rev"].Value

        if (-not $remotes.ContainsKey($remote)) {
            throw "Remote '$remote' not found for project '$name'"
        }

        $specs += [pscustomobject]@{
            Name = $name
            UrlBase = $remotes[$remote]
            Revision = $revision
        }
    }

    return $specs
}

function Sync-ExternalModules {
    param(
        [Parameter(Mandatory = $true)][string]$ModulesPath,
        [Parameter(Mandatory = $true)][object[]]$Specs
    )

    New-Item -ItemType Directory -Force -Path $ModulesPath | Out-Null

    foreach ($spec in $Specs) {
        $dst = Join-Path $ModulesPath $spec.Name
        $repoUrl = "$($spec.UrlBase)/$($spec.Name).git"

        if (-not (Test-Path $dst)) {
            Write-Host "Cloning $($spec.Name)" -ForegroundColor Yellow
            Invoke-Checked -FilePath "git" -Arguments @("clone", $repoUrl, $dst) -What "git clone $($spec.Name)"
        }

        Invoke-InDirectory -Path $dst -Script {
            Invoke-Checked -FilePath "git" -Arguments @("fetch", "--all", "--tags") -What "git fetch $($spec.Name)"
            Invoke-Checked -FilePath "git" -Arguments @("checkout", $spec.Revision) -What "git checkout $($spec.Name)"
        }
    }
}

$zmkApp = Join-Path $ZmkRoot "app"
$configPath = Join-Path $ConfigRepo "config"
$modulesPath = Join-Path $ConfigRepo "modules"
$westYml = Join-Path $configPath "west.yml"

if (-not (Test-Path $zmkApp)) { throw "ZMK app path not found: $zmkApp" }
if (-not (Test-Path $configPath)) { throw "Config path not found: $configPath" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git not found in PATH" }

Assert-ZephyrEnvNotMixed

$python = Resolve-ToolchainPython -PreferredPath $ToolchainPython
Write-Host "Using toolchain python: $python" -ForegroundColor Cyan
Invoke-Checked -FilePath $python -Arguments @("-m", "west", "--version") -What "west availability check"

$toolchainBin = Split-Path -Parent $python
$env:Path = "$toolchainBin;$($env:Path)"
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { throw "cmake not found in PATH after adding toolchain bin" }
if (-not (Get-Command ninja -ErrorAction SilentlyContinue)) { throw "ninja not found in PATH after adding toolchain bin" }

Ensure-WestWorkspace -ZmkRoot $ZmkRoot -Python $python -RunWestUpdate (-not $SkipWestUpdate)

$moduleSpecs = Get-ExternalModuleSpecs -WestYmlPath $westYml
Sync-ExternalModules -ModulesPath $modulesPath -Specs $moduleSpecs

Write-Host "Build environment is ready." -ForegroundColor Green
