# ALH learn hook v3 - append-only learning log (no GPU, no pipeline mutation).
#
# v3 fixes (2026-11-27 review):
#   - v2 is the ONLY learning system; this hook never writes LEARNINGS.md or SKILL.md,
#     so sync can regenerate the rendered section without a second writer fighting it;
#   - id allocation + append happen under a cross-process .lock file, so two agents
#     cannot take the same E### or lose an event during `alh.py set`;
#   - -DetailFile / -Rule accept UTF-8 text, avoiding PowerShell's lost Vietnamese tones;
#   - new events carry rule / supersedes / status_by / status_ts and a canonical part.
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('qa_fail','node_error','asset_qa_fail','warn_accepted','rule_gap','asset_reuse','verdict','promoted','revoked')]
    [string]$Event,
    [Parameter(Mandatory = $true)][string]$Shot,
    [Parameter(Mandatory = $true)][string]$Layer,
    [string]$Detail,
    [string]$DetailFile,
    [string]$Rule,
    [string]$Skill = 'comfyui-runner',
    [string]$Part = '',
    [ValidateSet('proposed','accepted','revoked')][string]$Status = 'proposed',
    [ValidateSet('agent','machine','user')][string]$Actor = 'agent',
    [string]$Supersedes = ''
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Normalize-Part([string]$value) {
    $p = ([string]$value).Trim().ToLowerInvariant()
    if ($p -in @('1','p1')) { return 'part1' }
    if ($p -in @('2','p2')) { return 'part2' }
    if ($p -in @('3','p3')) { return 'part3' }
    if ($p -in @('','all','part1','part2','part3')) { return $p }
    throw "invalid part '$value' (use '', all, part1, part2, part3, or 1/2/3)"
}

function Get-Rule([string]$text) {
    $one = (($text -replace '\s+', ' ').Trim() -replace '^(?:user|hy4|agent|machine)\s+\d{1,2}/\d{1,2}\s*:\s*', '')
    $first = [regex]::Split($one, '(?<=[.!?])\s+')[0].Trim([char[]]@(' ', '-', [char]0x2013))
    if ($first.Length -gt 200) { $first = $first.Substring(0, 200) + [char]0x2026 }
    return $first
}

try {
    $root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
    $dir = Join-Path $root 'art\comfy\ALH'
    New-Item -ItemType Directory -Force $dir | Out-Null
    $log = Join-Path $dir 'learning-log.jsonl'

    if ($DetailFile) {
        if (-not (Test-Path -LiteralPath $DetailFile)) { throw "DetailFile not found: $DetailFile" }
        $resolved = (Resolve-Path -LiteralPath $DetailFile).Path
        $Detail = [System.IO.File]::ReadAllText($resolved, [System.Text.Encoding]::UTF8).Trim()
    }
    if ([string]::IsNullOrWhiteSpace($Detail)) { throw 'supply -Detail or -DetailFile' }

    $part = Normalize-Part $Part
    $validSkills = @(Get-ChildItem -LiteralPath (Join-Path $root '.opencode\skills') -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } |
        ForEach-Object { $_.Name })
    $validSkills += 'global'
    if ($Skill -notin $validSkills) { throw "unknown skill '$Skill'; sync would drop the event" }

    $ruleSource = 'explicit'
    if (-not $Rule) {
        $Rule = Get-Rule $Detail
        $ruleSource = 'derived'
        if ($Event -eq 'verdict' -or $Detail -match '(?i)\battempt\b|re-render|\bPASS\b|\br\d\b') {
            $ruleSource = 'derived_run'
        }
    }
    $now = (Get-Date).ToString('o')

    # ---- mutex: id scan + append + confirmation are one critical section ---------
    $lockPath = Join-Path $dir '.lock'
    $lock = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::OpenOrCreate,
                                  [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try {
        $next = 1
        if (Test-Path -LiteralPath $log) {
            $ids = Select-String -LiteralPath $log -Pattern '"id":"E(\d+)"' -AllMatches |
                ForEach-Object { $_.Matches } | ForEach-Object { [int]$_.Groups[1].Value }
            if ($ids) { $next = ([int]($ids | Measure-Object -Maximum).Maximum) + 1 }
            else { $next = @(Get-Content -LiteralPath $log).Count + 1 }
        }
        $id = 'E{0:D3}' -f $next

        $entry = [ordered]@{
            id        = $id
            ts        = $now
            schema    = 2
            event     = $Event
            status    = $Status
            skill     = $Skill
            part      = $part
            shot      = $Shot
            layer     = $Layer
            actor      = $Actor
            rule       = $Rule
            rule_source = $ruleSource
            supersedes = $Supersedes
            status_by = $Actor
            status_ts = $now
            detail    = $Detail
        }
        $json = $entry | ConvertTo-Json -Compress -Depth 5
        [System.IO.File]::AppendAllText($log, $json + "`n", $utf8)

        # verify the log write actually landed before reporting success
        $last = Get-Content -LiteralPath $log -Tail 1
        if ($last -notmatch [regex]::Escape($id)) { throw "log write not confirmed for $id" }
    }
    finally {
        $lock.Dispose()
    }

    Write-Host "ALH $id recorded -> $log  |  skill=$Skill part='$part'"
    Write-Host 'Render rules with: python art/comfy/ALH/alh.py sync'
}
catch {
    Write-Error "ALH hook failed: $($_.Exception.Message)"
    exit 1
}
