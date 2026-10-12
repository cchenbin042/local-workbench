param([string]$Python = "python")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvironmentRoot = Join-Path $ProjectRoot ".venv"
$EnvironmentPython = Join-Path $EnvironmentRoot "Scripts\python.exe"
$LockPath = Join-Path $ProjectRoot "backend\requirements.lock.txt"
$BackendPath = Join-Path $ProjectRoot "backend"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "需要 uv；安装后重新运行。"
}
if (-not (Test-Path -LiteralPath $EnvironmentPython)) {
    & uv venv --python $Python $EnvironmentRoot
    if ($LASTEXITCODE -ne 0) { throw "创建项目虚拟环境失败。" }
}
& $EnvironmentPython -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)'
if ($LASTEXITCODE -ne 0) { throw "项目虚拟环境需要 Python 3.13。" }
& uv pip sync --link-mode=copy --python $EnvironmentPython $LockPath
if ($LASTEXITCODE -ne 0) { throw "安装锁定依赖失败。" }
& uv pip install --link-mode=copy --python $EnvironmentPython --no-deps --editable $BackendPath
if ($LASTEXITCODE -ne 0) { throw "安装后端包失败。" }
Write-Output "后端环境已准备：$EnvironmentPython"
