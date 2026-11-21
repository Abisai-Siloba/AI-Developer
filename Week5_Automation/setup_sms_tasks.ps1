$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $PSScriptRoot "wk5_day5_project_automation_tool.py"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $pythonPath = $venvPython
} else {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
}

& $pythonPath $scriptPath --check
if ($LASTEXITCODE -ne 0) {
    throw "SMS configuration check failed; scheduled tasks were not created."
}

$principal = New-ScheduledTaskPrincipal `
    -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
$tasks = @(
    @{
        Name = "Chama Weekly Meeting SMS"
        Argument = "--meeting"
        Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "8:00AM"
    },
    @{
        Name = "Chama Monthly Contribution SMS"
        Argument = "--contribution"
        Trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 5 -At "8:00AM"
    }
)

foreach ($task in $tasks) {
    $action = New-ScheduledTaskAction `
        -Execute $pythonPath `
        -Argument ('"{0}" {1}' -f $scriptPath, $task.Argument) `
        -WorkingDirectory $projectRoot
    Register-ScheduledTask `
        -TaskName $task.Name `
        -Action $action `
        -Trigger $task.Trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Sends chama member reminders using Africa's Talking." `
        -Force | Out-Null
}

Write-Host "Created or updated both chama SMS reminder tasks."
