$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$verifier = Join-Path $PSScriptRoot 'verify-image.py'
$python = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($python) {
    & $python.Source -3 $verifier @args
}
else {
    $python = Get-Command python3 -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python) {
        $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    if (-not $python) {
        Write-Error 'Python 3 is required. Install it with py, python3, or python available on PATH.'
        exit 1
    }
    & $python.Source $verifier @args
}
exit $LASTEXITCODE
