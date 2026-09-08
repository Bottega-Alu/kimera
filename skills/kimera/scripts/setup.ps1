<#
.SYNOPSIS
    Creates (or refreshes) the dedicated Kimera 2.0 Python runtime.

.DESCRIPTION
    Kimera renders documents with Python-Markdown + nh3 + Playwright (Chromium)
    + PyMuPDF. Those live in one dedicated virtualenv that is shared by every
    installation of the skill, so the dependencies are installed once and
    reused. The absolute path of the resulting interpreter is written to
    python.txt in the skill root; render.py reads it to bootstrap itself.

    Run this once. It is idempotent: re-running it only re-checks the pins.

.PARAMETER Python
    Base interpreter used to create the virtualenv. Either an absolute path to
    a python.exe, or a py-launcher spec such as "-3.11" / "-3.12".
    Default: the first of "-3.12", "-3.11", "-3.10", "-3" that resolves.

.PARAMETER VenvPath
    Where the virtualenv lives. Default: $env:LOCALAPPDATA\kimera\venv

.PARAMETER Force
    Delete and recreate the virtualenv from scratch.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
#>
[CmdletBinding()]
param(
    [string]$Python = '',
    [string]$VenvPath = '',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Fail([string]$Message, [int]$Code = 1) {
    Write-Host ''
    Write-Host "SETUP FAILED: $Message" -ForegroundColor Red
    exit $Code
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Split-Path -Parent $scriptDir
$requirements = Join-Path $scriptDir 'requirements.txt'
if (-not (Test-Path -LiteralPath $requirements)) { Fail "requirements.txt not found next to setup.ps1 ($requirements)" }

if ([string]::IsNullOrWhiteSpace($VenvPath)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { Fail 'LOCALAPPDATA is not set; pass -VenvPath explicitly.' }
    $VenvPath = Join-Path $env:LOCALAPPDATA 'kimera\venv'
}

Write-Host 'Kimera 2.0 - runtime setup'
Write-Host "  skill root : $skillRoot"
Write-Host "  venv       : $VenvPath"

# ---------------------------------------------------------------- base python
function Resolve-BasePython([string]$Spec) {
    if (-not [string]::IsNullOrWhiteSpace($Spec)) {
        if (Test-Path -LiteralPath $Spec) { return @($Spec) }
        if ($Spec -match '^-') { return @('py', $Spec) }
        $cmd = Get-Command $Spec -ErrorAction SilentlyContinue
        if ($cmd) { return @($cmd.Source) }
        Fail "-Python '$Spec' is neither an existing file nor a resolvable command."
    }
    if (Get-Command 'py' -ErrorAction SilentlyContinue) {
        foreach ($v in @('-3.12', '-3.11', '-3.10', '-3')) {
            & py $v -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return @('py', $v) }
        }
    }
    $cmd = Get-Command 'python' -ErrorAction SilentlyContinue
    if ($cmd) {
        & $cmd.Source -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { return @($cmd.Source) }
    }
    Fail 'No Python 3.10+ found. Install Python 3.11 from https://www.python.org/downloads/ and re-run.'
}

$base = Resolve-BasePython $Python
$baseExe = $base[0]
$baseArgs = @()
if ($base.Count -gt 1) { $baseArgs = $base[1..($base.Count - 1)] }
$baseVersion = & $baseExe @baseArgs -c 'import sys; print(sys.version.split()[0])'
if ($LASTEXITCODE -ne 0) { Fail "base interpreter '$baseExe $baseArgs' is not runnable." }
Write-Host "  base python: $baseExe $baseArgs ($baseVersion)"

# ----------------------------------------------------------------------- venv
$venvPython = Join-Path $VenvPath 'Scripts\python.exe'
if ($Force -and (Test-Path -LiteralPath $VenvPath)) {
    Write-Host '  removing existing venv (-Force)'
    Remove-Item -LiteralPath $VenvPath -Recurse -Force
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host '  creating virtualenv...'
    $parent = Split-Path -Parent $VenvPath
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    & $baseExe @baseArgs -m venv $VenvPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) { Fail "could not create a virtualenv at $VenvPath" }
} else {
    Write-Host '  virtualenv already present'
}

# ------------------------------------------------------------------- packages
Write-Host '  installing pinned dependencies...'
& $venvPython -m pip install --disable-pip-version-check --require-virtualenv -r $requirements
if ($LASTEXITCODE -ne 0) { Fail 'pip install failed (see output above).' }

Write-Host '  ensuring Chromium is available to Playwright...'
& $venvPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) { Fail 'playwright install chromium failed (see output above).' }

# ---------------------------------------------------------------- self-checks
Write-Host '  verifying imports and Chromium version...'
$probe = @'
import json, sys
import markdown, nh3, fitz
from playwright.sync_api import sync_playwright
info = {
    "python": sys.executable,
    "python_version": sys.version.split()[0],
    "markdown": markdown.__version__,
    "nh3": getattr(nh3, "__version__", "unknown"),
    "pymupdf": fitz.__doc__.strip().splitlines()[0] if fitz.__doc__ else fitz.VersionBind,
}
with sync_playwright() as p:
    b = p.chromium.launch()
    info["chromium"] = b.version
    b.close()
print(json.dumps(info, indent=2))
major = int(info["chromium"].split(".")[0])
sys.exit(0 if major >= 131 else 9)
'@
$probe | & $venvPython -
$probeExit = $LASTEXITCODE
if ($probeExit -eq 9) { Fail 'Chromium is older than 131; run this script with -Force to reinstall.' 9 }
if ($probeExit -ne 0) { Fail 'the runtime self-check failed (see output above).' }

# ------------------------------------------------------------------ python.txt
$pythonTxt = Join-Path $skillRoot 'python.txt'
[System.IO.File]::WriteAllText($pythonTxt, $venvPython, (New-Object System.Text.UTF8Encoding($false)))
Write-Host ''
Write-Host 'Kimera 2.0 runtime ready.' -ForegroundColor Green
Write-Host "  interpreter : $venvPython"
Write-Host "  recorded in : $pythonTxt"
Write-Host ''
Write-Host 'Render a document with:'
Write-Host "  `"$venvPython`" `"$(Join-Path $scriptDir 'render.py')`" DOC.md --verify"
exit 0
