param(
    [string]$Port = "COM5",
    [int]$DurationSeconds = 45
)

$maxRetries = 3
$serial = $null

for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $serial = New-Object System.IO.Ports.SerialPort $Port, 115200, "None", 8, "One"
        $serial.ReadTimeout = 2000
        $serial.DtrEnable = $true
        $serial.Open()
        Write-Host "Opened $Port successfully." -ForegroundColor Green
        break
    } catch {
        Write-Host "Attempt $($i+1): Failed to open $Port - $_" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        if ($serial) { $serial.Dispose(); $serial = $null }
    }
}

if (-not $serial -or -not $serial.IsOpen) {
    Write-Host "ERROR: Could not open $Port after $maxRetries attempts." -ForegroundColor Red
    exit 1
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$output = @()

Write-Host "Capturing from $Port for $DurationSeconds seconds..." -ForegroundColor Cyan

try {
    while ($stopwatch.Elapsed.TotalSeconds -lt $DurationSeconds) {
        try {
            $line = $serial.ReadLine()
            $ts = $stopwatch.Elapsed.ToString("mm\:ss\.fff")
            Write-Host "[$ts] $line"
            $output += $line
        } catch [System.TimeoutException] {
            # no data yet
        } catch {
            Write-Host "Read error: $_" -ForegroundColor Red
            break
        }
    }
} finally {
    $serial.Close()
    $serial.Dispose()
}

Write-Host "--- END OF CAPTURE ($($output.Count) lines) ---" -ForegroundColor Yellow

# Save to file
$outFile = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "serial-capture.log"
$output | Out-File -FilePath $outFile -Encoding utf8
Write-Host "Saved to $outFile" -ForegroundColor Green
