param(
    [Parameter(Mandatory = $true)][string]$Path,
    [double]$Seconds = 0,
    [int]$Frames = 0,
    [ValidateSet('auto', 'base', 'ref')][string]$Mode = 'auto',
    # The old gate said "PASS, 0 warning" but only the exit code was checked and
    # PASS ignored warnings, so a warning sailed into the render. Callers that
    # mean it (run_master, diagnose) pass this switch.
    [switch]$FailOnWarn
)

$ErrorActionPreference = 'Stop'
$errors = New-Object 'System.Collections.Generic.List[string]'
$warns = New-Object 'System.Collections.Generic.List[string]'

function Add-Err([string]$m) { $errors.Add($m) }
function Add-Warn([string]$m) { $warns.Add($m) }

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "ERROR file not found: $Path" -ForegroundColor Red
    exit 1
}

$raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
if ($null -eq $raw) { $raw = '' }
$lines = $raw -split "`r?`n"

$baseFields = @('integrated_multimodal_description', 'overall_soundscape', 'non_diegetic_music')
$refFields = @('subject_definitions', 'summary', 'retention_analysis', 'detailed_description', 'overall_soundscape', 'non_diegetic_music')
$allFields = @($baseFields + $refFields | Select-Object -Unique)
$fieldAlt = ($allFields | ForEach-Object { [regex]::Escape($_) }) -join '|'
$fieldLine = [regex]::new("^\s*($fieldAlt)\s*:\s*(.*)$")

$found = @{}
$order = New-Object 'System.Collections.Generic.List[string]'
$current = $null
$buffer = New-Object 'System.Collections.Generic.List[string]'

function Flush-Field {
    if ($null -eq $script:current) { return }
    $text = ($script:buffer -join "`n").Trim()
    $script:found[$script:current] = $text
    $script:current = $null
    $script:buffer.Clear()
}

foreach ($line in $lines) {
    $m = $fieldLine.Match($line)
    if ($m.Success) {
        Flush-Field
        $name = $m.Groups[1].Value
        $current = $name
        $order.Add($name)
        if ($m.Groups[2].Value.Trim()) { $buffer.Add($m.Groups[2].Value) }
    }
    elseif ($null -ne $current) {
        $buffer.Add($line)
    }
}
Flush-Field

# ---------- mode ----------
$detected = if ($found.ContainsKey('subject_definitions') -or $found.ContainsKey('retention_analysis') -or $found.ContainsKey('detailed_description')) { 'ref' }
            elseif ($found.ContainsKey('integrated_multimodal_description')) { 'base' }
            else { 'unknown' }

if ($Mode -eq 'auto') {
    if ($detected -eq 'unknown') {
        Add-Err 'Cannot detect prompt shape: no integrated_multimodal_description and no Ref2VA fields found.'
        $Mode = 'base'
    } else { $Mode = $detected }
}

$expected = if ($Mode -eq 'ref') { $refFields } else { $baseFields }

# ---------- fields ----------
foreach ($f in $expected) {
    if (-not $found.ContainsKey($f)) { Add-Err "Missing required field: $f" }
    elseif ([string]::IsNullOrWhiteSpace($found[$f])) { Add-Err "Field is empty: $f" }
}
foreach ($f in $order) {
    if ($expected -notcontains $f) { Add-Err "Field not allowed in $Mode mode: $f" }
}
$prev = -1
foreach ($f in $order) {
    $idx = [array]::IndexOf($expected, $f)
    if ($idx -lt 0) { continue }
    if ($idx -le $prev) { Add-Err "Field out of order: $f (expected order: $($expected -join ' -> '))" }
    $prev = [math]::Max($prev, $idx)
}
if (($order | Select-Object -Unique).Count -ne $order.Count) { Add-Err 'A field appears more than once.' }

$descKey = if ($Mode -eq 'ref') { 'detailed_description' } else { 'integrated_multimodal_description' }
$desc = if ($descKey -and $found.ContainsKey($descKey)) { $found[$descKey] } else { '' }

# ---------- placeholders ----------
foreach ($f in $expected) {
    if (-not $found.ContainsKey($f)) { continue }
    if ($found[$f] -match '\{\{|\}\}|\bTODO\b|\bTBD\b|\[insert') {
        Add-Err "Unresolved placeholder in ${f}: $($Matches[0])"
    }
}

# ---------- style contract position ----------
# The rule used to be documented but never measured: the check only verified that the
# body starts at [Shot 1], which is trivially true. A prompt whose contract sits after a
# prepended blob (the old feed_h3_context composition) lost H3's style weighting.
if ($desc.Trim().Length -gt 0) {
    $window = $desc.Trim()
    if ($window.Length -gt 400) { $window = $window.Substring(0, 400) }
    if ($window -notmatch '(?i)solid flat fills|flat 2D') {
        Add-Warn "style contract should lead the field: put 'Solid flat fills' before [Shot 1] (first 400 chars)"
    }
}

# ---------- text allowance must be one clause ----------
# G01 shipped "no text, no watermark." in the contract and "Visible text allowed only: 00:00"
# at the tail: two opposite instructions about the same timer, and H3 split the difference.
# allow_text belongs inside the contract as "no text except ...".
if ($desc -match '(?i)\b(visible\s+)?text\s+allowed\s+only\b') {
    Add-Err "text allowance contradicts the contract: merge it as 'no text except <what>' instead of 'Visible text allowed only'"
}

# ---------- E298: pipeline metadata must not reach prompt_visible ----------
# cabin-map.compositing_note is QA metadata only. The G02 queued prompt still
# said "three generic passengers are composited later"; catch it here and in
# h3_prompt_rules.validate_prompt before the next render.
if ($desc -match '(?i)\bcomposited\b|\bcompositing stage\b') {
    Add-Err 'pipeline/compositing metadata in prompt_visible; keep it in cabin-map QA notes only (E298)'
}

# ---------- shots ----------
$shotMatches = [regex]::Matches($desc, '\[Shot\s+([0-9]+)\]')
if ($shotMatches.Count -eq 0) {
    Add-Err "No [Shot N] tag in $descKey"
}
else {
    # Style contract is allowed to lead the field (h3-prompt-writing position rule);
    # only the shot body after that prefix must begin with [Shot 1].
    $head = $desc.TrimStart()
    $tagAt = $head.IndexOf('[Shot 1]')
    $body = if ($tagAt -gt 0) { $head.Substring($tagAt) } else { $head }
    if (-not $body.StartsWith('[Shot 1]')) {
        Add-Warn "$descKey should start with [Shot 1]"
    }
    $n = 0
    foreach ($s in $shotMatches) {
        $n++
        $got = [int]$s.Groups[1].Value
        if ($got -ne $n) { Add-Err "Shot numbering breaks at [Shot $got]: expected [Shot $n]" }
    }
}

# ---------- continuous motion ----------
# A frozen camera reads as a frozen clip; the prompt must give H3 something to animate.
# Only the plain "static camera" wording is caught: a scripted fixed security-camera shot
# (G49) says "fixed security camera view" and stays legal.
if ($desc -match '(?i)\b(camera\s+static|static\s+camera)\b' -and
    $desc -notmatch '(?i)\bdrift\b|\bsway\b|\bhandheld\b|\bpush-in\b') {
    Add-Warn 'static camera without drift: add a slow push-in/handheld sway plus environment motion'
}

# ---------- E268: jerk-mode contradiction ----------
# Discrete wrist/finger snaps were smoothed into a dolly by a trailing "continue evenly"
# line. Requiring BOTH wrist and fingers keeps a normal head "snaps up" legal.
if ($desc -match '(?i)\bwrist\b' -and
    $desc -match '(?i)\bfingers\b' -and
    $desc -match '(?i)\b(snap|snaps|jerk|jerks|flick|flicks|spasm|spasms)\b' -and
    $desc -match '(?i)\b(continue evenly|continues evenly|slides slowly|slow pan|smoothly|eases closer|keeps drifting)\b') {
    Add-Err 'motion contradiction: wrist/finger snaps must not be paired with even/slow/smooth camera drift (E268)'
}

# ---------- timecodes ----------
$tc = [regex]::Matches($desc, '(?i)\bAt\s+(\d{2}):(\d{2})\.(\d{3})')
$prevT = -1.0
foreach ($t in $tc) {
    $mm = [int]$t.Groups[1].Value; $ss = [int]$t.Groups[2].Value; $ms = [int]$t.Groups[3].Value
    if ($ss -ge 60) { Add-Err "Bad timecode (seconds >= 60): $($t.Value)" }
    $v = $mm * 60 + $ss + $ms / 1000.0
    if ($v -le $prevT) { Add-Err "Timecode not increasing: $($t.Value)" }
    $prevT = $v
}

# ---------- duration ----------
if ($Frames -le 0 -and $Seconds -gt 0) {
    $req = [int][math]::Ceiling($Seconds * 24)
    $Frames = $req + (((5 - $req) % 17) + 17) % 17
}
if ($Frames -gt 0) {
    if ((($Frames - 5) % 17) -ne 0) { Add-Err "Frames $Frames are not 17k+5 (valid: 39, 56, 73, ...)" }
    $dur = $Frames / 24.0
    if ($tc.Count -gt 0 -and $prevT -gt $dur + 0.001) {
        Add-Err ("Last timecode {0:N3}s exceeds clip length {1:N3}s ({2} frames)" -f $prevT, $dur, $Frames)
    }
}

# ---------- references ----------
$labelRe = '<(Subject|Picture|Video|Audio)\s+([0-9]+)>'
$defined = New-Object 'System.Collections.Generic.HashSet[string]'
if ($Mode -eq 'ref') {
    if ($found.ContainsKey('subject_definitions')) {
        foreach ($m in [regex]::Matches($found['subject_definitions'], $labelRe)) {
            [void]$defined.Add("$($m.Groups[1].Value) $($m.Groups[2].Value)")
        }
        if ($defined.Count -eq 0) { Add-Err 'subject_definitions contains no <Subject N>, <Picture N>, <Video N> or <Audio N> label' }
    }
    foreach ($m in [regex]::Matches($desc, $labelRe)) {
        $key = "$($m.Groups[1].Value) $($m.Groups[2].Value)"
        if (-not $defined.Contains($key)) { Add-Err "Label used but not defined in subject_definitions: $($m.Value)" }
    }
    foreach ($d in $defined) {
        $parts = $d -split ' '
        if ($desc -notmatch [regex]::Escape("<$($parts[0]) $($parts[1])>")) {
            Add-Warn ("Defined but never used in {0}: <{1} {2}>" -f $descKey, $parts[0], $parts[1])
        }
    }
}
foreach ($m in [regex]::Matches($raw, '<\s*(subject|picture|video|audio)\s+[0-9]+\s*>')) {
    Add-Warn "Label casing/spacing should be <Subject 1> style: $($m.Value)"
}
if ($raw -match '<<|>>') { Add-Err 'Double angle brackets found (<<character_1>> style is not valid; use <Subject 1>)' }

# ---------- dialogue ----------
$opens = [regex]::Matches($raw, '<d>').Count
$closes = [regex]::Matches($raw, '</d>').Count
if ($opens -ne $closes) { Add-Err "Unbalanced dialogue tags: $opens <d> vs $closes </d>" }
foreach ($m in [regex]::Matches($raw, '<d>(.*?)</d>', 'Singleline')) {
    $body = $m.Groups[1].Value.Trim()
    if ($body -eq '') { Add-Err 'Empty <d></d> dialogue tag' ; continue }
    if ($body -notmatch '^\[[A-Za-z][A-Za-z\-]*\]') {
        Add-Err "Dialogue missing language tag, expected <d>[English] ...</d>: $body"
    }
}

# ---------- sound ----------
if ($found.ContainsKey('overall_soundscape') -and $found['overall_soundscape'] -match '^\s*$') {
    Add-Err 'overall_soundscape is empty'
}

# ---------- report ----------
Write-Host ''
Write-Host "H3 prompt lint: $Path" -ForegroundColor Cyan
Write-Host ("mode={0}  fields={1}  shots={2}  timecodes={3}{4}" -f $Mode, $order.Count, $shotMatches.Count, $tc.Count,
    $(if ($Frames -gt 0) { "  frames=$Frames ($([math]::Round($Frames / 24.0, 3))s)" } else { '' }))
Write-Host ''
foreach ($w in $warns) { Write-Host "WARN  $w" -ForegroundColor Yellow }
foreach ($e in $errors) { Write-Host "ERROR $e" -ForegroundColor Red }
Write-Host ''
if ($errors.Count -eq 0 -and -not ($FailOnWarn -and $warns.Count -gt 0)) {
    Write-Host ("PASS  ({0} warning(s))" -f $warns.Count) -ForegroundColor Green
    exit 0
}
if ($errors.Count -eq 0) {
    Write-Host ("FAIL  {0} warning(s) treated as errors by -FailOnWarn" -f $warns.Count) -ForegroundColor Red
    exit 1
}
Write-Host ("FAIL  {0} error(s), {1} warning(s)" -f $errors.Count, $warns.Count) -ForegroundColor Red
exit 1
