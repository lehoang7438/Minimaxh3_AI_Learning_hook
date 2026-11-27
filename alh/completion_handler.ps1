# ALH completion handler v3 - runs when a generation session finishes.
# Collects QA verdicts, clip coverage and the learning log into one session summary.
# No GPU, no pipeline mutation. It stays fail-silent at the render boundary, but a
# missing Python/alh.py failure is now written as a visible WARN, not a healthy-looking
# empty "Learning log" section.
param([string]$SessionName = 'session')
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$alh = Join-Path $root 'art\comfy\ALH'
$out = Join-Path $alh 'SESSION-SUMMARY.md'

try {
    $py = Join-Path $root '.venv-tts\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $py)) { throw "python not found: $py" }
    New-Item -ItemType Directory -Force $alh | Out-Null

    $lines = @()
    $lines += "# ALH session summary - $SessionName"
    $lines += ''
    $lines += "Finished: $((Get-Date).ToString('o'))"
    $lines += ''

    foreach ($part in 1..3) {
        $outDir = Join-Path $root "out\part$part-t2v"
        $notesPath = Join-Path $outDir 'qa-notes.json'
        $specPath = Join-Path $root "art\part$part-spec.json"

        $lines += "## part$part"
        if (-not (Test-Path -LiteralPath $notesPath)) {
            $lines += 'verdicts: WARN - no qa-notes.json (nothing recorded this session)'
        }
        else {
            $notes = Get-Content -LiteralPath $notesPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $pass = 0; $warn = 0; $fail = 0; $bad = @()
            foreach ($p in $notes.PSObject.Properties) {
                $v = [string]$p.Value.verdict
                if ($v -match 'PASS_WITH_WARN') { $warn++; $bad += "$($p.Name): WARN $($p.Value.layer)" }
                elseif ($v -match 'PASS') { $pass++ }
                else { $fail++; $bad += "$($p.Name): FAIL $($p.Value.layer)" }
            }
            $total = $pass + $warn + $fail
            $lines += "verdicts: $total recorded, $pass PASS, $warn PASS_WITH_WARN, $fail FAIL"
            foreach ($b in $bad) { $lines += "  - $b" }
        }

        if (Test-Path -LiteralPath $specPath) {
            $spec = Get-Content -LiteralPath $specPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $want = @($spec.shots).Count
            $have = @(Get-ChildItem -LiteralPath $outDir -Directory -ErrorAction SilentlyContinue |
                      Where-Object { Get-ChildItem $_.FullName -Filter '*.mp4' -ErrorAction SilentlyContinue }).Count
            $lines += "clips: $have / $want shot(s) have an mp4"
        }
        $lines += ''
    }

    $report = & $py (Join-Path $alh 'alh.py') report 2>&1
    if ($LASTEXITCODE -ne 0) { throw "alh.py report failed (exit $LASTEXITCODE): $($report -join ' ')" }
    $lines += '## Learning log'
    $lines += ($report | Where-Object { $_ -notmatch '^report ->' })
    $lines += ''
    $lines += 'Review: `python art/comfy/ALH/alh.py report` then `set <id> accepted|revoked`, then `sync`.'

    [System.IO.File]::WriteAllText($out, ($lines -join "`n") + "`n", $utf8)
    Write-Host "ALH session summary -> $out"
}
catch {
    $msg = $($_.Exception.Message)
    $warnLines = @(
        "# ALH session summary - $SessionName",
        '',
        "Finished: $((Get-Date).ToString('o'))",
        '',
        "WARN: completion handler could not build the summary: $msg",
        '',
        'Render was NOT blocked. Fix the cause above, then re-run this handler.'
    )
    [System.IO.File]::WriteAllText($out, ($warnLines -join "`n") + "`n", $utf8)
    Write-Warning "ALH completion handler skipped: $msg (WARN written to $out)"
}
