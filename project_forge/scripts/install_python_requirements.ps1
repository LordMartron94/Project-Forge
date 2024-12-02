param(
    [string]$venvPath,
    [string]$projectName
)

& "$venvPath\$projectName\Scripts\activate.ps1"

$requirementsPath = "../requirements.txt"
Write-Host $requirementsPath

pip install -r $requirementsPath