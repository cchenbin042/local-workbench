param([ValidateRange(1, 65535)][int]$Port = 8765)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvironmentPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $EnvironmentPython)) {
    throw "请先运行 scripts\setup-backend.ps1。"
}
& $EnvironmentPython -m workbench --host 127.0.0.1 --port $Port --app-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "后端退出，退出码：$LASTEXITCODE" }
