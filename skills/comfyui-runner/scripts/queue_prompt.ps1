param(
    [Parameter(Mandatory = $true)][string]$Workflow,
    [string]$PromptFile,
    [string]$Prompt,
    [string]$Server = 'http://127.0.0.1:8188',
    [string]$Placeholder = '{{PROMPT}}',
    [string]$NodeId,
    [string]$OutDir,
    [int]$TimeoutSec = 7200,
    [int]$PollSeconds = 3,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Fail($m) { Write-Host "ERROR $m" -ForegroundColor Red; exit 2 }

if (-not (Test-Path -LiteralPath $Workflow)) { Fail "workflow not found: $Workflow" }
$wfText = Get-Content -LiteralPath $Workflow -Raw -Encoding UTF8
try { $wf = $wfText | ConvertFrom-Json } catch { Fail "workflow is not valid JSON: $($_.Exception.Message)" }

if ($PSBoundParameters.ContainsKey('PromptFile')) {
    if (-not (Test-Path -LiteralPath $PromptFile)) { Fail "prompt file not found: $PromptFile" }
    $Prompt = Get-Content -LiteralPath $PromptFile -Raw -Encoding UTF8
}
if (-not $Prompt -and -not $ValidateOnly) { Fail 'Provide -PromptFile or -Prompt' }
if ($Prompt) { $Prompt = $Prompt.TrimEnd() }

# ---------- choose injection point ----------
$usedNode = $null
if ($NodeId) {
    $node = $wf.PSObject.Properties[$NodeId]
    if (-not $node) { Fail "node $NodeId not found in workflow" }
    if (-not $node.Value.inputs -or -not $node.Value.inputs.PSObject.Properties['text']) {
        Fail "node $NodeId has no inputs.text"
    }
    if (-not $ValidateOnly) { $node.Value.inputs.text = $Prompt }
    $usedNode = $NodeId
}
elseif ($wfText.Contains($Placeholder)) {
    if (-not $ValidateOnly) {
        $escaped = ConvertTo-Json -InputObject $Prompt -Compress
        $escaped = $escaped.Substring(1, $escaped.Length - 2)
        $wfText = $wfText.Replace($Placeholder, $escaped)
        $wf = $wfText | ConvertFrom-Json
    }
    $usedNode = 'placeholder'
}
else {
    $candidates = @()
    foreach ($p in $wf.PSObject.Properties) {
        $ct = [string]$p.Value.class_type
        if ($ct -match 'CLIPTextEncode|TextEncode') {
            if ($p.Value.inputs -and $p.Value.inputs.PSObject.Properties['text']) { $candidates += $p.Name }
        }
    }
    if ($candidates.Count -eq 1) {
        $NodeId = $candidates[0]
        if (-not $ValidateOnly) { $wf.PSObject.Properties[$NodeId].Value.inputs.text = $Prompt }
        $usedNode = $NodeId
    }
    elseif ($candidates.Count -eq 0) { Fail 'No {{PROMPT}} placeholder and no TextEncode node with inputs.text; pass -NodeId' }
    else { Fail ("Several text nodes: {0}. Pass -NodeId or use {1}" -f ($candidates -join ', '), $Placeholder) }
}

Info ("workflow : $Workflow")
Info ("inject   : $usedNode")
Info ("server   : $Server")
if ($ValidateOnly) { Info 'validate only: OK'; exit 0 }

# ---------- queue ----------
$clientId = [guid]::NewGuid().ToString()
$body = @{ prompt = $wf; client_id = $clientId } | ConvertTo-Json -Depth 100 -Compress
$bytes = [Text.Encoding]::UTF8.GetBytes($body)
try {
    $resp = Invoke-RestMethod -Uri "$Server/prompt" -Method Post -ContentType 'application/json; charset=utf-8' -Body $bytes -TimeoutSec 60
}
catch {
    $detail = ''
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $detail = $_.ErrorDetails.Message }
    Fail "POST /prompt failed. Is ComfyUI running at $Server ? $detail"
}
if ($resp.node_errors -and $resp.node_errors.PSObject.Properties.Count -gt 0) {
    $resp.node_errors | ConvertTo-Json -Depth 8
    Fail 'workflow rejected (node_errors above)'
}
$id = $resp.prompt_id
if (-not $id) { Fail ("no prompt_id in response: " + ($resp | ConvertTo-Json -Depth 5 -Compress)) }
Info "queued: $id"

# ---------- poll ----------
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$entry = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds $PollSeconds
    try {
        $hist = Invoke-RestMethod -Uri "$Server/history/$id" -TimeoutSec 30
    }
    catch { continue }
    $e = $hist.PSObject.Properties[$id]
    if ($e) {
        $entry = $e.Value
        $status = [string]$entry.status.status_str
        if ($status -eq 'error') {
            $entry.status | ConvertTo-Json -Depth 8
            Fail 'execution error'
        }
        if ($entry.outputs -and ($entry.outputs.PSObject.Properties.Count -gt 0)) { break }
        if ($status -eq 'success') { break }
    }
}

if (-not $entry) { Fail "timeout after $TimeoutSec s" }

# ---------- collect outputs ----------
if (-not $OutDir) { $OutDir = Join-Path (Get-Location) 'out' }
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$files = @()
foreach ($np in $entry.outputs.PSObject.Properties) {
    $out = $np.Value
    foreach ($key in 'images', 'gifs', 'videos') {
        if ($out.PSObject.Properties[$key]) {
            foreach ($f in $out.$key) {
                $q = 'filename=' + [uri]::EscapeDataString([string]$f.filename) +
                     '&subfolder=' + [uri]::EscapeDataString([string]$f.subfolder) +
                     '&type=' + [uri]::EscapeDataString([string]$f.type)
                $dest = Join-Path $OutDir ([string]$f.filename)
                Invoke-WebRequest -Uri "$Server/view?$q" -OutFile $dest -TimeoutSec 300
                $files += $dest
            }
        }
    }
}
if ($files.Count -eq 0) { Fail 'finished but no downloadable outputs found' }
foreach ($f in $files) { Info ("saved: {0}  ({1:N1} MB)" -f $f, ((Get-Item -LiteralPath $f).Length / 1MB)) }
exit 0
