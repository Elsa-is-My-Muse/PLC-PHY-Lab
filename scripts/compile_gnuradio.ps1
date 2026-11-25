param(
    [Parameter(Mandatory = $true)]
    [string]$RadiocondaRoot
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExecutable = Join-Path $RadiocondaRoot 'python.exe'
$CompilerScript = Join-Path $RadiocondaRoot 'Scripts\grcc-script.py'
$BlockDirectory = Join-Path $RadiocondaRoot 'Library\share\gnuradio\grc\blocks'
$OutputDirectory = Join-Path $ProjectRoot 'build\gnuradio'
foreach ($RequiredPath in @($PythonExecutable, $CompilerScript, $BlockDirectory)) {
    if (-not (Test-Path -LiteralPath $RequiredPath)) {
        throw "Required GNU Radio path does not exist: $RequiredPath"
    }
}
$OriginalPath = $env:PATH
$OriginalBlocks = $env:GRC_BLOCKS_PATH
try {
    $env:PATH = "$RadiocondaRoot;$(Join-Path $RadiocondaRoot 'Library\bin');$(Join-Path $RadiocondaRoot 'Scripts');$OriginalPath"
    $env:GRC_BLOCKS_PATH = $BlockDirectory
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    & $PythonExecutable $CompilerScript -o $OutputDirectory `
        (Join-Path $ProjectRoot 'sdr\gnuradio\homeplug_spectrum.grc') `
        (Join-Path $ProjectRoot 'sdr\gnuradio\homeplug_capture.grc')
    if ($LASTEXITCODE -ne 0) { throw 'GRC compilation failed' }
    & $PythonExecutable -m py_compile `
        (Join-Path $OutputDirectory 'homeplug_spectrum.py') `
        (Join-Path $OutputDirectory 'homeplug_capture.py')
    if ($LASTEXITCODE -ne 0) { throw 'Generated Python syntax check failed' }
    Write-Output "GNU Radio compilation and Python syntax checks passed: $OutputDirectory"
}
finally {
    $env:PATH = $OriginalPath
    if ($null -eq $OriginalBlocks) {
        Remove-Item Env:\GRC_BLOCKS_PATH -ErrorAction SilentlyContinue
    } else {
        $env:GRC_BLOCKS_PATH = $OriginalBlocks
    }
}
