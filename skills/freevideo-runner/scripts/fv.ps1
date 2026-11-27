# FreeVideo agent bridge - one entry point for a local MiniMax H3 install.
#
#   fv.ps1 doctor                      preflight: is anything safe to run right now?
#   fv.ps1 status                      readiness, version, queue
#   fv.ps1 caps                         legal canvas sizes and clip lengths
#   fv.ps1 plan -JobFile job.json      validate + estimate (never renders)
#   fv.ps1 submit -JobFile job.json    queue it, print the job id
#   fv.ps1 wait -Id <job>              poll until it finishes, print status
#   fv.ps1 download -Id <job> -Out x.mp4
#   fv.ps1 jobs                        recent jobs, newest first
#
# Everything here talks to the FreeVideo agent HTTP API, so it always hits the
# server the user already has open. It never starts a second ComfyUI.

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet('doctor', 'status', 'caps', 'plan', 'submit', 'wait', 'jobs', 'job', 'download', 'release', 'hello')]
    [string]$Action,

    [string]$JobFile,
    [string]$Prompt,
    [double]$Seconds = 0,
    [string]$Aspect = '16:9',
    [int]$Width = 0,
    [int]$Height = 0,
    [string]$Quality = '',
    [string]$Id,
    [string]$Out,
    [int]$TimeoutSec = 5400,
    [string]$Engine = '',
    [string]$Url = ''
)

$ErrorActionPreference = 'Stop'
$script:Ok = $true
function Say($m, $c = 'Gray') { Write-Host $m -ForegroundColor $c }
function Pass($m) { Write-Host "PASS  $m" -ForegroundColor Green }
function Warn($m, $next) { $script:Ok = $false; Write-Host "WARN  $m" -ForegroundColor Yellow; if ($next) { Write-Host "      -> $next" -ForegroundColor DarkYellow } }
function Bad($m, $next) { $script:Ok = $false; Write-Host "FAIL  $m" -ForegroundColor Red; if ($next) { Write-Host "      -> $next" -ForegroundColor DarkYellow } }

# ---------------------------------------------------------------- environment
function Resolve-Engine {
    $cands = @()
    if ($Engine) { $cands += $Engine }
    if ($env:FREEVIDEO_ENGINE) { $cands += $env:FREEVIDEO_ENGINE }
    $cands += 'C:\Users\Admin\FreeVideo\FreeVideo-engine'
    foreach ($c in $cands) {
        if (-not $c) { continue }
        if (Test-Path -LiteralPath (Join-Path $c 'agent\token')) { return (Resolve-Path -LiteralPath $c).Path }
    }
    # engine without a token yet: accept the folder that holds the launcher tree
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath (Join-Path $c 'launcher\source'))) { return (Resolve-Path -LiteralPath $c).Path }
    }
    return $null
}

$engineRoot = Resolve-Engine
if (-not $engineRoot) {
    Bad 'FreeVideo engine not found' 'Pass -Engine C:\Users\Admin\FreeVideo\FreeVideo-engine'
    exit 2
}
$tokenFile = Join-Path $engineRoot 'agent\token'

# The server port is not fixed: if 8188 is taken, ComfyUI moves to 8189 and the
# FreeVideo app keeps its own instance there. Prefer the one the app started.
function Resolve-ServerUrl {
    $found = @()
    foreach ($port in 8186..8195) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $listener) { continue }
        $owner = $listener.OwningProcess
        $managed = $false
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$owner" -ErrorAction SilentlyContinue
        for ($hop = 0; $hop -lt 4 -and $proc; $hop++) {
            $parent = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $proc.ParentProcessId) -ErrorAction SilentlyContinue
            if (-not $parent) { break }
            if ($parent.Name -match 'FreeVideo') { $managed = $true; break }
            $proc = $parent
        }
        try { Invoke-RestMethod -Uri "http://127.0.0.1:$port/system_stats" -TimeoutSec 3 | Out-Null } catch { continue }
        $found += [pscustomobject]@{ Port = $port; Managed = $managed }
    }
    if (-not $found) { return $null }
    $managedHit = $found | Where-Object { $_.Managed } | Select-Object -First 1
    if ($managedHit) { return [pscustomobject]@{ Url = "http://127.0.0.1:$($managedHit.Port)"; Managed = $true; Others = $found } }
    $first = $found | Sort-Object Port | Select-Object -First 1
    return [pscustomobject]@{ Url = "http://127.0.0.1:$($first.Port)"; Managed = $false; Others = $found }
}

if (-not $Url) {
    $resolved = Resolve-ServerUrl
    if ($resolved) { $Url = $resolved.Url; $script:ServerManaged = $resolved.Managed; $script:AllServers = $resolved.Others }
    else { $Url = 'http://127.0.0.1:8188' }
}
$base = "$Url/freevideo/agent/v1"

function Get-Token {
    if (Test-Path -LiteralPath $tokenFile) { return (Get-Content -LiteralPath $tokenFile -Raw).Trim() }
    try {
        $c = Invoke-RestMethod -Uri "$base/connect" -TimeoutSec 10
        if ($c -match 'Token file:\s*(.+)') {
            $p = $Matches[1].Trim()
            if (Test-Path -LiteralPath $p) { return (Get-Content -LiteralPath $p -Raw).Trim() }
        }
    } catch { }
    return $null
}

$token = Get-Token

function Api {
    param([string]$Method, [string]$Path, $Body = $null, [int]$Timeout = 120)
    if (-not $token) { throw 'no_token: read the token file first (GET /freevideo/agent/v1/connect)' }
    $headers = @{ Authorization = "Bearer $token"; 'X-FreeVideo-Client' = 'OpenCode' }
    $params = @{
        Method      = $Method
        Uri         = "$base$Path"
        Headers     = $headers
        TimeoutSec  = $Timeout
        ErrorAction = 'Stop'
    }
    if ($null -ne $Body) {
        # Vietnamese prompts: PowerShell 5.1 would send the string as ANSI and the
        # server answers invalid_json. Send explicit UTF-8 bytes.
        $params.Body = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 30 -Compress))
        $params.ContentType = 'application/json; charset=utf-8'
    }
    $bytes = [Text.Encoding]::UTF8
    try {
        return Invoke-RestMethod @params
    } catch {
        $detail = ''
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $detail = $_.ErrorDetails.Message }
        throw ("{0} {1} failed: {2}" -f $Method, $Path, $detail)
    }
}

function To-Hashtable($value) {
    # Windows PowerShell 5.1 has no ConvertFrom-Json -AsHashtable.
    if ($null -eq $value) { return $null }
    if ($value -is [System.Collections.IDictionary]) {
        $out = @{}
        foreach ($k in $value.Keys) { $out[$k] = To-Hashtable $value[$k] }
        return $out
    }
    if ($value -is [pscustomobject]) {
        $out = @{}
        foreach ($p in $value.PSObject.Properties) { $out[$p.Name] = To-Hashtable $p.Value }
        return $out
    }
    if ($value -is [System.Collections.IEnumerable] -and $value -isnot [string]) {
        return @($value | ForEach-Object { To-Hashtable $_ })
    }
    return $value
}

function Read-Job([string]$path) {
    return (To-Hashtable (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json))
}

function Connect {
    if (-not $token) { return $false }
    try { Api POST '/connect/hello' @{ client = 'OpenCode'; via = 'http' } -Timeout 15 | Out-Null; return $true }
    catch { return $false }
}

# ------------------------------------------------------------------ doctor
if ($Action -eq 'doctor') {
    Say "FreeVideo doctor - engine $engineRoot"
    Say "agent API $base"
    Say ''

    if ($token) { Pass "token file: $tokenFile" }
    else { Bad 'no agent token' 'Start the FreeVideo app once (it writes <engine>\agent\token), then rerun.' }

    # server + readiness
    $stats = $null
    try { $stats = Invoke-RestMethod -Uri "$Url/system_stats" -TimeoutSec 8 } catch { }
    if ($stats) {
        $vramTotal = [math]::Round($stats.devices[0].vram_total / 1GB, 1)
        $vramFree = [math]::Round($stats.devices[0].vram_free / 1GB, 1)
        Pass ("server on $Url  ({0}, ComfyUI {1}, VRAM {2}/{3} GiB free)" -f $stats.devices[0].name, $stats.system.comfyui_version, $vramFree, $vramTotal)
    } else {
        Bad "no server on $Url" 'Open the FreeVideo app (or let the user open it). Do not start a second ComfyUI by hand.'
        foreach ($port in 8186..8195) {
            $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $listener) { continue }
            try { Invoke-RestMethod -Uri "http://127.0.0.1:$port/system_stats" -TimeoutSec 3 | Out-Null }
            catch { Warn ("port {0} has a listener that never answers" -f $port) 'Half-started server (usually a second instance lost the database lock): restart the FreeVideo app, then rerun doctor.' }
        }
    }

    if ($token -and $stats) {
        if (Connect) {
            try {
                $s = Api GET ''
                if ($s.ready -eq $true) { Pass ("FreeVideo ready, build {0}" -f $s.build) }
                else { Bad ("FreeVideo not ready: {0}" -f $s.problem) 'Read the problem text; fix models/setup before queueing.' }
            } catch { Bad "agent status failed: $($_.Exception.Message)" 'Check the token file matches this engine root.' }
            try {
                $q = Api GET '/jobs?limit=5'
                $active = @($q.jobs | Where-Object { $_.status -in @('queued', 'running', 'preparing') })
                if ($active.Count -gt 0) {
                    Warn ("{0} job(s) already active ({1})" -f $active.Count, (($active | ForEach-Object { $_.id }) -join ', ')) 'Wait for them (`fv.ps1 wait -Id <job>`) before submitting anything else; one GPU.'
                } else { Pass 'job queue idle' }
            } catch { Warn "job list unavailable: $($_.Exception.Message)" 'Ignore if the version predates /jobs; otherwise check the token.' }
        } else { Bad 'agent handshake failed' 'Restart the FreeVideo page / app so the agent route is registered.' }
    }

    # competing processes
    # Servers only: the launcher starts every server through a bootstrap python in
    # ProgramData\FV, so counting those doubles every instance.
    $servers = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'main\.py' -and $_.CommandLine -notmatch 'ProgramData\\FV' })
    if ($servers.Count -gt 1) {
        Warn ("{0} ComfyUI servers are running" -f $servers.Count) 'Close the extra one (keep the one FreeVideo opened); two servers fight for the same user database and the same VRAM.'
    } elseif ($servers.Count -eq 1) { Pass 'exactly one ComfyUI server' }
    else { Warn 'no ComfyUI server process visible' 'Open the FreeVideo app; do not start main.py by hand.' }

    $busy = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'gen_image\.py|freevideo_engine\.generate' -and $_.CommandLine -notmatch 'ProgramData\\FV' })
    if ($busy.Count -gt 0) {
        Warn ("{0} generation process(es) running outside the job queue" -f $busy.Count) 'Image and video generation share the GPU; a picture job while the video engine is busy fails with busy_video. Finish or stop it first.'
    } else { Pass 'no stray generation process' }

    $stale = Join-Path $env:USERPROFILE 'Downloads\FreeVideo\src\FreeVideo-main\pyproject.toml'
    if (Test-Path -LiteralPath $stale) {
        $v = (Select-String -Path $stale -Pattern '^version' | Select-Object -First 1).Line
        Warn ("stale FreeVideo source in Downloads ($v)") 'Never point the runner at it; always use the engine root above.'
    }

    try {
        $free = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
        if ($free -lt 20) { Warn ("C: has {0} GB free" -f $free) 'Free space: every 10 s clip is ~0.4 GB and renders keep their intermediates.' }
        else { Pass ("disk free {0} GB" -f $free) }
    } catch { }

    Say ''
    if ($script:Ok) { Say 'GO - safe to plan/submit.' 'Green' } else { Say 'NO-GO - fix the FAIL/WARN lines above first.' 'Yellow' }
    exit $(if ($script:Ok) { 0 } else { 1 })
}

# ------------------------------------------------------------------ actions
switch ($Action) {
    'hello' { if (Connect) { Say 'connected' } else { Bad 'handshake failed'; exit 2 } }
    'status' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        $s = Api GET ''
        $s | ConvertTo-Json -Depth 8
    }
    'caps' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        Api GET '/capabilities' | ConvertTo-Json -Depth 8
    }
    'jobs' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        (Api GET '/jobs?limit=20').jobs |
            Select-Object id, status, label, @{n = 'progress'; e = { $_.progress.percent } }, created_at |
            Format-Table -AutoSize | Out-String -Width 160
    }
    'job' {
        if (-not $Id) { Bad '-Id is required'; exit 2 }
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        (Api GET "/jobs/$Id").job | ConvertTo-Json -Depth 10
    }
    'plan' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        $body = @{}
        if ($JobFile) { $body = Read-Job $JobFile }
        if ($Prompt) { $body['prompt'] = $Prompt }
        if ($Seconds -gt 0) { $body['seconds'] = $Seconds }
        if ($Width -gt 0) { $body['width'] = $Width }
        if ($Height -gt 0) { $body['height'] = $Height }
        # aspect and width/height are mutually exclusive on this API
        if ($Aspect -and -not ($body['width'] -or $body['height'])) { $body['aspect'] = $Aspect }
        if ($Quality) { $body['quality'] = $Quality }
        if (-not $body['prompt']) { Bad 'need -JobFile or -Prompt'; exit 2 }
        $p = Api POST '/plan' $body
        $mins = [math]::Round($p.estimate.seconds / 60, 1)
        Say ("canvas {0}x{1}  frames {2}  {3}s  quality {4} ({5} steps)" -f $p.spec.width, $p.spec.height, $p.spec.frames, [math]::Round($p.spec.output_seconds, 2), $p.spec.quality, $p.sampling.total_steps) 'Cyan'
        Say ("estimate {0} min ({1})" -f $mins, $p.estimate.basis) 'Cyan'
        if ($p.warnings) { $p.warnings | ForEach-Object { Warn $_ } }
        if ($p.estimate.seconds -gt 900) { Warn ("long run: {0} min" -f $mins) 'Tell the user the estimate before queueing.' }
        ($p | ConvertTo-Json -Depth 10) -replace '\s+', ' ' | Out-Null
        $p | ConvertTo-Json -Depth 10
    }
    'submit' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        if (-not $JobFile) { Bad '-JobFile is required'; exit 2 }
        $body = Read-Job $JobFile
        if (-not $body['ref']) {
            $body['ref'] = 'opencode-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
            Warn "no ref in job file, using $($body['ref'])" 'A stable ref makes an unanswered submit safe to repeat.'
        }
        $r = Api POST '/jobs' $body -Timeout 120
        $job = $r.job
        Say ("queued {0}  status {1}" -f $job.id, $job.status) 'Green'
        $job | ConvertTo-Json -Depth 8
    }
    'wait' {
        if (-not $Id) { Bad '-Id is required'; exit 2 }
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        $deadline = (Get-Date).AddSeconds($TimeoutSec)
        $last = ''
        while ((Get-Date) -lt $deadline) {
            $job = (Api GET "/jobs/$Id`?wait=25" -Timeout 60).job
            $pct = $job.progress.percent
            $line = "status $($job.status) $pct%"
            if ($line -ne $last) { Say $line 'DarkGray'; $last = $line }
            if ($job.status -in @('succeeded', 'failed', 'cancelled', 'interrupted')) { break }
        }
        if (-not $job) { Bad 'no answer from /jobs'; exit 2 }
        if ($job.status -eq 'succeeded') {
            Pass "succeeded: $($job.result.video.url)"
            $job | ConvertTo-Json -Depth 10
            exit 0
        }
        Bad "job ended as $($job.status)"
        if ($job.error) {
            Say ("error {0}: {1}" -f $job.error.code, $job.error.message) 'Red'
            if ($job.error.next) { Say ("next: {0}" -f $job.error.next) 'Yellow' }
            if ($job.error.details) { $job.error.details | ConvertTo-Json -Depth 6 }
        }
        exit 1
    }
    'download' {
        if (-not $Id) { Bad '-Id is required'; exit 2 }
        if (-not $Out) { Bad '-Out is required, e.g. -Out out\shot-01.mp4'; exit 2 }
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        $job = (Api GET "/jobs/$Id").job
        if ($job.status -ne 'succeeded') { Bad "job is $($job.status), nothing to download"; exit 2 }
        $relative = $job.result.video.url
        $dir = Split-Path -Parent $Out
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        Invoke-WebRequest -Uri "$Url$relative" -Headers @{ Authorization = "Bearer $token" } -OutFile $Out -TimeoutSec 600
        Pass ("saved {0} ({1:N1} MB)" -f $Out, ((Get-Item -LiteralPath $Out).Length / 1MB))
    }
    'release' {
        if (-not (Connect)) { Bad 'no token/handshake'; exit 2 }
        try { Api POST '/gpu/release' @{} | ConvertTo-Json -Depth 6 }
        catch { Warn "release failed: $($_.Exception.Message)" 'Fallback: `freevideo.cmd agent release-gpu --root <engine>`.' }
    }
    default { Bad "unknown action $Action"; exit 2 }
}
