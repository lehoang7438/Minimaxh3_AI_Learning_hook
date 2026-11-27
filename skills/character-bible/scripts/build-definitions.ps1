param(
    [Parameter(Mandatory = $true)][string]$Bible,
    [Parameter(Mandatory = $true)][string[]]$Ids
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Bible)) { Write-Host "ERROR bible not found: $Bible" -ForegroundColor Red; exit 2 }
try { $data = Get-Content -LiteralPath $Bible -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { Write-Host "ERROR invalid JSON: $($_.Exception.Message)" -ForegroundColor Red; exit 2 }

function Describe($c) {
    $refs = @($c.refs | ForEach-Object { "$($_.label) ($($_.use))" })
    $line = "$($c.subject_label) is $($c.display_name)"
    if ($c.appearance) { $line += ". Appearance: $($c.appearance)" }
    if ($c.wardrobe) { $line += " Wardrobe: $($c.wardrobe)" }
    if ($refs.Count -gt 0) { $line += " References: $($refs -join ', ')." }
    if ($c.must_keep) { $line += " Must keep: $($c.must_keep -join '; ')." }
    if ($c.voice) {
        $v = $c.voice
        $line += " Voice: $($v.timbre), $($v.pace), $($v.accent) accent, speaks $($v.language)."
    }
    return ($line -replace '\s+', ' ').Trim()
}

$lines = @()
foreach ($id in $Ids) {
    $c = $data.characters | Where-Object { $_.id -eq $id } | Select-Object -First 1
    if (-not $c) { Write-Host "ERROR character id not found: $id" -ForegroundColor Red; exit 1 }
    $lines += Describe $c
}
"subject_definitions: " + ($lines -join ' ')
