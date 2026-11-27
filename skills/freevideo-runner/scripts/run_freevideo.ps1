param(
    [string]$PromptFile,
    [string]$Out,
    [string]$Root = '',
    [string]$Entry = '',
    [string]$Cache = '',
    [int]$Width = 1280,
    [int]$Height = 704,
    [switch]$Vertical,
    [switch]$Square,
    [double]$Seconds = 0,
    [int]$Frames = 0,
    [ValidateSet('light', 'medium', 'high', 'max', 'custom')][string]$Quality = 'light',
    [int]$BaseSteps = 0,
    [int]$RefineSteps = 0,
    [double]$UpscaleFactor = 0,
    [switch]$NoTwoPass,
    [int]$Seed = 0,
    [switch]$Plan,
    [int]$VramGib = 0,
    [int]$RamGib = 0,
    [switch]$Check,
    [switch]$NoLint,
    [string[]]$ExtraArgs = @()
)

$ErrorActionPreference = 'Stop'

function Fail([string]$m) { Write-Host "ERROR $m" -ForegroundColor Red; exit 2 }
function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }

# ---------- locate FreeVideo ----------
function Find-Entry {
    if ($Entry) {
        if (Test-Path -LiteralPath $Entry) { return $Entry }
        Write-Host "WARN -Entry not found: $Entry" -ForegroundColor Yellow
    }
    $cands = @()
    # The managed install (FreeVideo app): engine launcher source, newest version first.
    $engineCandidates = @()
    if ($env:FREEVIDEO_ENGINE) { $engineCandidates += $env:FREEVIDEO_ENGINE }
    $engineCandidates += 'C:\Users\Admin\FreeVideo\FreeVideo-engine'
    foreach ($engine in $engineCandidates) {
        $sources = Join-Path $engine 'launcher\source'
        if (Test-Path -LiteralPath $sources) {
            $newest = Get-ChildItem -LiteralPath $sources -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | Select-Object -First 1
            if ($newest) {
                $cands += (Join-Path $newest.FullName 'freevideo.ps1')
                $cands += (Join-Path $newest.FullName 'freevideo.cmd')
            }
        }
        $cands += (Join-Path $engine 'freevideo.ps1')
    }
    if ($Root) { $cands += (Join-Path $Root 'freevideo.ps1'); $cands += (Join-Path $Root 'freevideo.cmd') }
    $cands += (Join-Path $env:LOCALAPPDATA 'FreeVideo\freevideo.ps1')
    $cands += 'C:\FreeVideo\freevideo.ps1'
    $cands += (Join-Path $env:USERPROFILE 'FreeVideo\freevideo.ps1')
    # A plain git checkout is the last resort: it is usually an older build with different flags.
    $cands += (Join-Path $env:USERPROFILE 'Downloads\FreeVideo\src\FreeVideo-main\freevideo.ps1')
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

function Find-EngineRoot([string]$entryPath) {
    # freevideo.ps1 inside ...\FreeVideo-engine\launcher\source\<version>
    $dir = Split-Path -Parent $entryPath
    for ($i = 0; $i -lt 4 -and $dir; $i++) {
        if (Test-Path -LiteralPath (Join-Path $dir 'agent\token')) { return $dir }
        if (Test-Path -LiteralPath (Join-Path $dir 'machine.json')) { return $dir }
        $dir = Split-Path -Parent $dir
    }
    return $null
}

function Find-InstallRoot {
    $cands = @()
    if ($Root) { $cands += $Root }
    if ($env:FREEVIDEO_HOME) { $cands += $env:FREEVIDEO_HOME }
    $cands += (Join-Path $env:LOCALAPPDATA 'FreeVideo')
    $cands += (Join-Path $env:USERPROFILE 'FreeVideo')
    $cands += 'C:\FreeVideo'
    foreach ($c in $cands) {
        if (-not $c) { continue }
        if (Test-Path -LiteralPath (Join-Path $c 'machine.json')) { return $c }
    }
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

function Find-Cache([string]$installRoot) {
    if (-not $installRoot) { return $null }
    $prep = Join-Path $installRoot 'prepared'
    if (-not (Test-Path -LiteralPath $prep)) { return $null }
    $dirs = Get-ChildItem -LiteralPath $prep -Recurse -Directory -Filter 'cache' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\.freevideo-downloads' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'manifest.json')) } |
        Sort-Object LastWriteTime -Descending
    if ($dirs) { return $dirs[0].FullName }
    return $null
}

$entry = Find-Entry
if (-not $entry) {
    Fail @'
FreeVideo entry point not found. Pass -Entry "C:\...\FreeVideo-main\freevideo.ps1"
or -Root "C:\path\to\FreeVideo_install". Install from https://github.com/FlashML-org/FreeVideo first.
'@
}
$installRoot = Find-EngineRoot $entry
if (-not $installRoot) { $installRoot = Find-InstallRoot }
if (-not $installRoot) { $installRoot = $Root }
if (-not $installRoot) { Fail 'FreeVideo installation root not found (folder containing machine.json). Pass -Root.' }
if ($entry -match '\\Downloads\\') {
    Write-Host "WARN this entry is a plain git checkout, often an older build with different flags." -ForegroundColor Yellow
    Write-Host "     Prefer the managed install: C:\Users\Admin\FreeVideo\FreeVideo-engine\launcher\source\<version>\freevideo.ps1" -ForegroundColor Yellow
}
Info "FreeVideo : $entry"
Info "install   : $installRoot"


function Invoke-FreeVideo([string[]]$fvArgs) {
    $all = @('--root', $installRoot) + $fvArgs
    if ($entry -like '*.ps1') {
        & $entry @all
    }
    elseif ($entry -like '*.cmd') {
        & cmd /c $entry @all
    }
    else {
        & $entry @all
    }
}

# ---------- plan mode ----------
if ($Plan) {
    $a = @('plan', '--width', $Width, '--height', $Height)
    if ($VramGib -gt 0) { $a += @('--vram-gib', $VramGib) }
    if ($RamGib -gt 0) { $a += @('--ram-gib', $RamGib) }
    if ($Seconds -gt 0) { $a += @('--seconds', $Seconds) }
    Info ("plan command: freevideo " + ($a -join ' '))
    Invoke-FreeVideo $a
    exit $LASTEXITCODE
}

# ---------- validate inputs ----------
if (-not $PromptFile) { Fail 'PromptFile is required (use -Plan for a dry plan).' }
if (-not (Test-Path -LiteralPath $PromptFile)) { Fail "Prompt file not found: $PromptFile" }
if (-not $Out) { Fail 'Out is required, e.g. -Out .\out\shot-01.mp4' }
if ($Out -notmatch '\.mp4$') { Fail 'Out must end with .mp4' }
if ($Seconds -le 0 -and $Frames -le 0) { Fail 'Pass -Seconds (4-15) or -Frames (17k+5).' }
if ($Frames -gt 0 -and (($Frames - 5) % 17) -ne 0) { Fail "Frames $Frames is not 17k+5 (39, 56, 73, ... 362)." }

# ---------- aspect presets ----------
$explicitSize = $PSBoundParameters.ContainsKey('Width') -or $PSBoundParameters.ContainsKey('Height')
if ($Vertical -and -not $explicitSize) { $Width = 704; $Height = 1280 }
if ($Square -and -not $explicitSize) { $Width = 960; $Height = 960 }
if (($Width % 32) -ne 0 -or ($Height % 32) -ne 0 -or $Width -lt 256 -or $Height -lt 256) {
    Fail ("Canvas {0}x{1} is invalid: width/height must be multiples of 32 and at least 256. " -f $Width, $Height +
          'For 9:16 use 704x1280 (or 544x960 for drafts).')
}

# ---------- lint ----------
if (-not $NoLint) {
    $lint = Join-Path $PSScriptRoot '..\..\h3-prompt-linter\scripts\lint_h3.ps1'
    $lint = [IO.Path]::GetFullPath($lint)
    if (Test-Path -LiteralPath $lint) {
        $la = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $lint, '-Path', $PromptFile)
        if ($Frames -gt 0) { $la += @('-Frames', $Frames) } elseif ($Seconds -gt 0) { $la += @('-Seconds', $Seconds) }
        & powershell @la
        if ($LASTEXITCODE -ne 0) { Fail 'Prompt failed lint. Fix errors or rerun with -NoLint.' }
    }
    else { Write-Host 'WARN linter not found, skipping lint' -ForegroundColor Yellow }
}

# ---------- quality ----------
$twoPass = $true
$base = 8; $refine = 3; $upscale = 2.0; $stepCache = ''
switch ($Quality) {
    'light' { $twoPass = $true; $base = 8; $refine = 3; $upscale = 2.0 }
    'medium' { $twoPass = $true; $base = 8; $refine = 3; $upscale = 1.5 }
    'high' { $twoPass = $false; $base = 16; $refine = 3; $stepCache = 'easycache-av' }
    'max' { $twoPass = $false; $base = 20; $refine = 3; $stepCache = 'easycache-av' }
    'custom' { $twoPass = -not $NoTwoPass }
}
if ($BaseSteps -gt 0) { $base = $BaseSteps }
if ($RefineSteps -gt 0) { $refine = $RefineSteps }
if ($UpscaleFactor -gt 0) { $upscale = $UpscaleFactor }
if ($NoTwoPass) { $twoPass = $false }

# ---------- cache ----------
if (-not $Cache) {
    $Cache = Find-Cache $installRoot
    if ($Cache) { Info "cache     : $Cache (auto-detected)" }
}
if (-not $Cache) {
    Fail @'
-Cache not found. Point it at the prepared-model cache created by FreeVideo setup
(the folder containing manifest.json, usually <install>\prepared\*\*\cache).
Run "freevideo setup --root <install>" first if setup never finished.
'@
}
if (-not (Test-Path -LiteralPath $Cache) -and -not $Check) { Fail "Cache folder not found: $Cache" }

$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path -LiteralPath $outDir) -and -not $Check) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

$a = @('generate', '--prompt-file', (Resolve-Path -LiteralPath $PromptFile).Path, '--out', $Out,
       '--cache', $Cache, '--width', $Width, '--height', $Height)
if ($Frames -gt 0) { $a += @('--frames', $Frames) } else { $a += @('--seconds', $Seconds) }
if ($twoPass) { $a += '--two-pass'; $a += @('--base-steps', $base, '--refine-steps', $refine, '--upscale-factor', $upscale) }
else { $a += '--no-two-pass'; $a += @('--base-steps', $base) }
if ($stepCache) { $a += @('--step-cache', $stepCache) }
if ($Seed -ne 0) { $a += @('--seed', $Seed) }
if ($ExtraArgs.Count -gt 0) { $a += $ExtraArgs }

Info ("command: freevideo " + ($a -join ' '))
if ($Check) { exit 0 }

# ---------- run ----------
$log = "$Out.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    & {
        if ($entry -like '*.ps1') { & $entry @a 2>&1 }
        elseif ($entry -like '*.cmd') { & cmd /c $entry @a 2>&1 }
        else { & $entry @a 2>&1 }
    } | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
}
catch {
    $code = 1
    $_ | Out-String | Add-Content -LiteralPath $log
}
$sw.Stop()
$mins = [math]::Round($sw.Elapsed.TotalMinutes, 1)

if ($code -eq 0 -and (Test-Path -LiteralPath $Out)) {
    Info ("DONE {0}  ({1} min, {2:N1} MB)" -f $Out, $mins, ((Get-Item -LiteralPath $Out).Length / 1MB))
    exit 0
}
Write-Host ("FAILED exit={0} after {1} min. Log: {2}" -f $code, $mins, $log) -ForegroundColor Red
exit 1
