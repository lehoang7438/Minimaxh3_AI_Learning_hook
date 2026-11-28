param(
  [string]$Src = (Get-Location).Path,
  [string]$Repo = (Join-Path $PSScriptRoot '..'),
  [string]$HistoryDir = 'C:\Users\Admin\AppData\Local\Temp\opencode\history-prompts',
  [string]$Message = 'Restructure learning bundle: skills, ALH, project tools and audit snapshots',
  [switch]$NoCommit
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$Src = (Resolve-Path -LiteralPath $Src).Path
$Repo = (Resolve-Path -LiteralPath $Repo).Path

$srcSkills = Join-Path $Src '.opencode\skills'
$srcAlh = Join-Path $Src 'art\comfy\ALH'
$srcChain = Join-Path $Src 'art\comfy\chain4\h3-chain4.json'
if (-not (Test-Path -LiteralPath $srcSkills)) { throw "missing skills: $srcSkills" }
if (-not (Test-Path -LiteralPath $srcAlh)) { throw "missing ALH: $srcAlh" }

function Reset-BundleDir([string]$Path) {
  if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Recurse -Force }
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Copy-IfExists([string]$From, [string]$To) {
  if (Test-Path -LiteralPath $From) {
    Copy-Item -LiteralPath $From -Destination $To -Force
  } else {
    Write-Output "MISSING $From"
  }
}

# 1. skills/ ------------------------------------------------------------------
$skillsDest = Join-Path $Repo 'skills'
Reset-BundleDir $skillsDest
Copy-Item -Path (Join-Path $srcSkills '*') -Destination $skillsDest -Recurse -Force
Get-ChildItem -LiteralPath $skillsDest -Recurse -Directory -Filter '__pycache__' -EA SilentlyContinue |
  Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $skillsDest -Recurse -File -Filter '*.pyc' -EA SilentlyContinue |
  Remove-Item -Force
Copy-IfExists (Join-Path $Repo 'docs\skills-README.md') (Join-Path $skillsDest 'README.md')

# 2. alh/ ---------------------------------------------------------------------
$alhDest = Join-Path $Repo 'alh'
Reset-BundleDir $alhDest
foreach ($f in @(
  'alh.py', 'learn_hook.ps1', 'completion_handler.ps1',
  'REPORT.md', 'GLOBAL-RULES.md', 'CONDENSED-RULES-DRAFT.md',
  'learning-log.jsonl', 'RUN-LOG.md', 'SESSION-SUMMARY.md',
  'CLEANUP-REPORT-20261127.md', 'CLEANUP-REPORT-FREEVIDEO-20261127.md'
)) {
  Copy-IfExists (Join-Path $srcAlh $f) (Join-Path $alhDest $f)
}
Copy-IfExists (Join-Path $Repo 'docs\alh-README.md') (Join-Path $alhDest 'README.md')
Copy-IfExists (Join-Path $srcAlh 'PLAYBOOK.md') (Join-Path $Repo 'PLAYBOOK.md')

# 3. project-tools/ ------------------------------------------------------------
$toolsDest = Join-Path $Repo 'project-tools'
Reset-BundleDir $toolsDest
foreach ($f in @(
  'rebuild_prompts.py', 'h3_prompt_rules.py', 'prompt_consistency_audit.py',
  'chain4_run.py', 'chain4_prepare.py', 'chain4_qa.py', 'chain4_recover.py',
  'workflow_state.py', 'build_single_node_ui.py',
  'h3_route_rules.py', 'h3_route_validate.py'
)) {
  Copy-IfExists (Join-Path $Src (Join-Path 'art\tests' $f)) (Join-Path $toolsDest $f)
}
Copy-IfExists $srcChain (Join-Path $toolsDest 'h3-chain4.json')
Copy-IfExists (Join-Path $Src 'art\comfy\h3-master.json') (Join-Path $toolsDest 'h3-master.json')
Copy-IfExists (Join-Path $Src 'art\comfy\h3-single-node-ui.json') (Join-Path $toolsDest 'h3-single-node-ui.json')
Copy-IfExists 'C:\Users\Admin\FreeVideo\ComfyUI\custom_nodes\FreeVideoGhe27AContext\__init__.py' (Join-Path $toolsDest 'FreeVideoGhe27AContext__init__.py')
Copy-IfExists (Join-Path $Repo 'docs\project-tools-README.md') (Join-Path $toolsDest 'README.md')

# 4. audit-inputs/ (frozen reviewer snapshot) ---------------------------------
$auditDest = Join-Path $Repo 'audit-inputs'
Reset-BundleDir $auditDest
Copy-IfExists (Join-Path $Repo 'docs\audit-inputs-README.md') (Join-Path $auditDest 'README.md')
$snapshot = @(
  'art\env\cabin-map.json',
  'art\env\global-context.json',
  'art\env\global-context-part2.json',
  'art\env\global-context-part3.json',
  'art\part1-spec.json',
  'art\tests\rebuild_prompts.py',
  'art\tests\h3_prompt_rules.py',
  'art\tests\chain4_run.py',
  'art\tests\build_single_node_ui.py',
  'art\tests\h3_route_rules.py',
  'art\tests\h3_route_validate.py',
  'art\comfy\chain4\h3-chain4.json',
  'art\comfy\h3-master.json',
  'art\comfy\h3-single-node-ui.json',
  'art\comfy\ALH\learning-log.jsonl',
  'art\comfy\ALH\REPORT.md',
  'art\comfy\ALH\GLOBAL-RULES.md',
  'art\comfy\ALH\CONDENSED-RULES-DRAFT.md',
  'art\comfy\ALH\CLEANUP-REPORT-20261127.md',
  'art\comfy\ALH\CLEANUP-REPORT-FREEVIDEO-20261127.md',
  'art\comfy\ALH\PLAYBOOK.md',
  'prompts\part1-rebuilt\G01.txt',
  'prompts\part1-rebuilt\G02.txt',
  'prompts\part1-rebuilt\G03.txt',
  'prompts\part1-rebuilt\G04.txt',
  'prompts\part1-rebuilt\G05.txt',
  'art\tests\prompt_consistency_audit.py',
  'out\story-g01\qa\prompt-consistency-report.json',
  'out\story-g01\qa\prompt-consistency-report.md',
  'out\story-g01\qa\prompt-system-review.md',
  'out\story-g01\qa\g03-gradient-rootcause.md',
  'out\story-g01\qa\audit-manual-check.md'
)
foreach ($f in $snapshot) {
  $p = Join-Path $Src $f
  if (Test-Path -LiteralPath $p) {
    $name = $f -replace '\\', '__'
    Copy-Item -LiteralPath $p -Destination (Join-Path $auditDest $name) -Force
  } else {
    Write-Output "MISSING $f"
  }
}
Copy-IfExists 'C:\Users\Admin\FreeVideo\ComfyUI\custom_nodes\FreeVideoGhe27AContext\__init__.py' (Join-Path $auditDest 'FreeVideoGhe27AContext__init__.py')
if (Test-Path -LiteralPath $HistoryDir) {
  $payloadDest = Join-Path $auditDest 'queued-payloads'
  New-Item -ItemType Directory -Force -Path $payloadDest | Out-Null
  Copy-Item -Path (Join-Path $HistoryDir '*') -Destination $payloadDest -Recurse -Force
}

# 5. MANIFEST ------------------------------------------------------------------
$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'
$all = Get-ChildItem -LiteralPath $Repo -File -Recurse -EA SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\\.git\\' }
$lines = @(
  '# MANIFEST - GHE 27A learning bundle',
  '',
  "synced: $stamp",
  "source: $Src",
  "files: $($all.Count)",
  '',
  '| path | sha256 |',
  '|---|---|'
)
foreach ($f in @(
  'PLAYBOOK.md', 'alh\learning-log.jsonl', 'alh\REPORT.md',
  'alh\CONDENSED-RULES-DRAFT.md', 'skills\h3-prompt-writing\SKILL.md',
  'skills\comfyui-runner\SKILL.md', 'project-tools\h3-chain4.json',
  'project-tools\h3-master.json', 'project-tools\h3-single-node-ui.json',
  'project-tools\h3_route_rules.py', 'project-tools\h3_route_validate.py',
  'project-tools\FreeVideoGhe27AContext__init__.py', 'docs\ROUTE-WORKFLOW.md'
)) {
  $p = Join-Path $Repo $f
  if (Test-Path -LiteralPath $p) {
    $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
    $lines += "| $f | $h |"
  }
}
$lines += ''
$lines += 'Rule: repo is a one-way snapshot; local ALH log is the source of truth.'
Set-Content -LiteralPath (Join-Path $Repo 'MANIFEST.md') -Value $lines -Encoding UTF8

# 6. commit + push -------------------------------------------------------------
Write-Output "bundle ready: skills=$((Get-ChildItem -LiteralPath $skillsDest -Recurse -File).Count) alh=$((Get-ChildItem -LiteralPath $alhDest -Recurse -File).Count) tools=$((Get-ChildItem -LiteralPath $toolsDest -Recurse -File).Count) audit=$((Get-ChildItem -LiteralPath $auditDest -Recurse -File).Count)"
if ($NoCommit) {
  git -C $Repo status --short
  return
}
git -C $Repo add -A
$diff = git -C $Repo diff --cached --name-only
if (-not $diff) {
  Write-Output 'nothing to commit'
} else {
  git -C $Repo -c user.name='OpenCode Agent' -c user.email='opencode@users.noreply.github.com' commit -m $Message | Out-String
  git -C $Repo push origin main 2>&1 | Out-String
  Write-Output "push_exit=$LASTEXITCODE"
}
git -C $Repo status --short -b
