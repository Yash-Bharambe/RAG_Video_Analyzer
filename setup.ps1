param([switch]$ConfigureOnly)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if ([IO.Path]::GetPathRoot($projectRoot) -eq 'C:\') {
    throw 'Keep this project on a drive other than C: before running setup.'
}

# Set these before starting Python: tempfile caches its chosen directory.
$storagePaths = @{
    TEMP = Join-Path $projectRoot '.tmp'
    TMP = Join-Path $projectRoot '.tmp'
    TMPDIR = Join-Path $projectRoot '.tmp'
    PIP_CACHE_DIR = Join-Path $projectRoot '.cache\pip'
    UV_CACHE_DIR = Join-Path $projectRoot '.cache\uv'
    UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.cache\uv-python'
    UV_TOOL_DIR = Join-Path $projectRoot '.cache\uv-tools'
    UV_TOOL_BIN_DIR = Join-Path $projectRoot '.cache\uv-bin'
    XDG_CACHE_HOME = Join-Path $projectRoot '.cache'
    HF_HOME = Join-Path $projectRoot '.cache\huggingface'
    HF_HUB_CACHE = Join-Path $projectRoot '.cache\huggingface\hub'
    HF_XET_CACHE = Join-Path $projectRoot '.cache\huggingface\xet'
    SENTENCE_TRANSFORMERS_HOME = Join-Path $projectRoot '.cache\sentence-transformers'
    TORCH_HOME = Join-Path $projectRoot '.cache\torch'
    TIKTOKEN_CACHE_DIR = Join-Path $projectRoot '.cache\tiktoken'
    NUMBA_CACHE_DIR = Join-Path $projectRoot '.cache\numba'
}
foreach ($entry in $storagePaths.GetEnumerator()) {
    New-Item -ItemType Directory -Path $entry.Value -Force | Out-Null
    [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, 'Process')
}
# Prevent inherited pip settings from redirecting installation outside the venv.
$env:PIP_CONFIG_FILE = 'NUL'
$env:PIP_USER = '0'
Remove-Item Env:PIP_TARGET -ErrorAction SilentlyContinue
Remove-Item Env:PIP_PREFIX -ErrorAction SilentlyContinue
$env:PYTHONNOUSERSITE = '1'
$env:UV_PYTHON_DOWNLOADS = 'never'
$env:UV_NO_CONFIG = '1'
Remove-Item Env:UV_TARGET -ErrorAction SilentlyContinue
Remove-Item Env:UV_PREFIX -ErrorAction SilentlyContinue
$env:UV_LINK_MODE = 'copy'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv is required. Install uv before running this script.'
}
$venvRoot = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & uv venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the project virtual environment.' }
}
$env:VIRTUAL_ENV = $venvRoot
$env:PATH = "$(Join-Path $venvRoot 'Scripts');$env:PATH"
$ffmpegBin = Join-Path ([IO.Path]::GetPathRoot($projectRoot)) 'Tools\ffmpeg\bin'
if (Test-Path -LiteralPath (Join-Path $ffmpegBin 'ffmpeg.exe')) {
    $env:PATH = "$ffmpegBin;$env:PATH"
}

& $venvPython -c "import sys,tempfile; print('Python:',sys.executable); print('Packages:',sys.prefix); print('Temporary files:',tempfile.gettempdir())"
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment verification failed.' }
& uv cache dir
if ($LASTEXITCODE -ne 0) { throw 'uv verification failed.' }

if (-not $ConfigureOnly) {
    & uv pip install --python $venvPython -r (Join-Path $projectRoot 'Requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; see uv output above.' }
    & uv pip check --python $venvPython
    if ($LASTEXITCODE -ne 0) { throw 'Installed dependencies failed compatibility checks.' }
}
