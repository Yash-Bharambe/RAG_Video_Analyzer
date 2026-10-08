param([string]$Model = 'qwen2.5:1.5b')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'setup.ps1') -ConfigureOnly
$ollamaDir = Join-Path $PSScriptRoot '.tools\ollama'
$ollamaExe = Join-Path $ollamaDir 'ollama.exe'
if (-not (Test-Path -LiteralPath $ollamaExe)) {
    $archive = Join-Path $PSScriptRoot '.tmp\ollama-windows-amd64.zip'
    New-Item -ItemType Directory -Path $ollamaDir -Force | Out-Null
    Write-Host 'Downloading the official Ollama standalone distribution to E:...'
    & curl.exe --fail --location --silent --show-error --retry 3 --output $archive 'https://github.com/ollama/ollama/releases/download/v0.40.1/ollama-windows-amd64.zip'
    if ($LASTEXITCODE -ne 0) { throw 'Ollama download failed.' }
    Write-Host 'Extracting Ollama...'
    Expand-Archive -LiteralPath $archive -DestinationPath $ollamaDir -Force
}
$profileDir = Join-Path $PSScriptRoot '.cache\ollama-profile'
$modelsDir = Join-Path $PSScriptRoot '.cache\ollama-models'
New-Item -ItemType Directory -Path $profileDir,$modelsDir -Force | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = $modelsDir
$env:OLLAMA_NO_CLOUD = '1'
$running = $false
try {
    Invoke-RestMethod 'http://127.0.0.1:11435/api/tags' -TimeoutSec 2 | Out-Null
    $running = $true
} catch {}
if (-not $running) {
    # Override profile paths only for the server child, never for Windows or the shell.
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $ollamaExe
    $startInfo.Arguments = 'serve'
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WorkingDirectory = $ollamaDir
    $startInfo.EnvironmentVariables['USERPROFILE'] = $profileDir
    $startInfo.EnvironmentVariables['LOCALAPPDATA'] = $profileDir
    $startInfo.EnvironmentVariables['APPDATA'] = $profileDir
    $server = [System.Diagnostics.Process]::Start($startInfo)
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        try {
            Invoke-RestMethod 'http://127.0.0.1:11435/api/tags' -TimeoutSec 2 | Out-Null
            $running = $true
            break
        } catch {}
    }
    if (-not $running) { throw 'Ollama server did not start.' }
}
& $ollamaExe pull $Model
if ($LASTEXITCODE -ne 0) { throw 'Local model download failed.' }
& $venvPython -c "from dotenv import set_key; import sys; set_key(sys.argv[1], 'LLM_PROVIDER', 'ollama'); set_key(sys.argv[1], 'OLLAMA_MODEL', sys.argv[2]); set_key(sys.argv[1], 'OLLAMA_BASE_URL', 'http://127.0.0.1:11435')" (Join-Path $PSScriptRoot '.env') $Model
if ($LASTEXITCODE -ne 0) { throw 'Could not configure .env.' }
Write-Host 'Local model ready. Launch with: python -m streamlit run app.py'
