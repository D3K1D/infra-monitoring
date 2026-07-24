[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$PauseOnExit
)

$ErrorActionPreference = "Stop"

function Exit-AgentLauncher {
    param(
        [string]$Message,
        [int]$ExitCode = 1
    )

    Write-Host ""
    Write-Host $Message -ForegroundColor Red
    if ($PauseOnExit) {
        [void](Read-Host "Press Enter to close")
    }
    exit $ExitCode
}

$agentDirectory = $PSScriptRoot
$projectDirectory = Split-Path -Parent $agentDirectory
$agentPath = Join-Path $agentDirectory "agent.py"
$configPath = Join-Path $agentDirectory "agent.config"

if (-not (Test-Path -LiteralPath $agentPath -PathType Leaf)) {
    Exit-AgentLauncher "Agent program not found: $agentPath"
}

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    Exit-AgentLauncher (
        "agent.config was not found. Copy agent.config.example to " +
        "agent.config and add this computer's server URL and API key."
    )
}

# Windows development originally reused the backend environment. A dedicated
# agent environment is also supported, so this launcher works on both existing
# Windows installations without changing their setup.
$pythonCandidates = @(
    (Join-Path $agentDirectory "venv\Scripts\python.exe"),
    (Join-Path $projectDirectory "backend\venv\Scripts\python.exe")
)

$pythonPath = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $pythonPath = $candidate
        break
    }
}

if ($null -eq $pythonPath) {
    Exit-AgentLauncher (
        "No project Python environment was found. Create agent\venv or " +
        "backend\venv and install the project's requirements first."
    )
}

& $pythonPath -c "import psutil, requests"
if ($LASTEXITCODE -ne 0) {
    Exit-AgentLauncher (
        "The selected Python environment is missing the agent dependencies. " +
        "Install agent\requirements.txt into that environment and try again."
    )
}

Write-Host "Infrastructure Monitoring Agent" -ForegroundColor Cyan
Write-Host "Computer: $env:COMPUTERNAME"
Write-Host "Python:   $pythonPath"

if ($ValidateOnly) {
    Write-Host "Launcher validation passed." -ForegroundColor Green
    exit 0
}

Write-Host "Press Ctrl+C to stop the agent."
Write-Host ""

Push-Location -LiteralPath $agentDirectory
try {
    & $pythonPath $agentPath
    $agentExitCode = $LASTEXITCODE
}
catch {
    Exit-AgentLauncher "The agent could not start: $($_.Exception.Message)"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Agent stopped with exit code $agentExitCode."
if ($PauseOnExit) {
    [void](Read-Host "Press Enter to close")
}
exit $agentExitCode
