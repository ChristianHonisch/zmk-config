param(
    [string]$Port = "COM5",
    [int]$BaudRate = 115200,
    [int]$DurationSeconds = 45
)

$serial = New-Object System.IO.Ports.SerialPort $Port, $BaudRate, "None", 8, "One"
$serial.ReadTimeout = 2000
$serial.Open()

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$output = @()

Write-Host "Capturing from $Port for $DurationSeconds seconds..." -ForegroundColor Cyan

try {
    while ($stopwatch.Elapsed.TotalSeconds -lt $DurationSeconds) {
        try {
            $line = $serial.ReadLine()
            Write-Host $line
            $output += $line
        } catch [System.TimeoutException] {
            # no data, keep waiting
        }
    }
} finally {
    $serial.Close()
}

Write-Host "--- END OF CAPTURE ($($output.Count) lines) ---" -ForegroundColor Yellow
