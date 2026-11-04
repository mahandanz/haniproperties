# Run FROM INSIDE the unitpic folder, with folders_to_keep.txt next to this script.
# Deletes every subfolder of the current folder that is NOT in folders_to_keep.txt.
#   Dry run: powershell -ExecutionPolicy Bypass -File .\delete_orphans.ps1
#   Delete:  powershell -ExecutionPolicy Bypass -File .\delete_orphans.ps1 -Confirm

param([switch]$Confirm, [switch]$AnyFolder)

$here = Get-Location
if (-not $AnyFolder -and (Split-Path $here -Leaf) -ne "unitpic") {
    Write-Error "This is not the unitpic folder ($here). cd into unitpic first, or pass -AnyFolder."
    exit 1
}

$listFile = Join-Path $PSScriptRoot "folders_to_keep.txt"
if (-not (Test-Path $listFile)) { Write-Error "folders_to_keep.txt not found next to this script."; exit 1 }

$keep = @(Get-Content $listFile -Encoding UTF8 | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
if ($keep.Count -lt 20) {
    Write-Error "Keep list has only $($keep.Count) names - looks wrong. Aborting so nothing gets wiped."
    exit 1
}
$keepSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$keep | ForEach-Object { [void]$keepSet.Add($_) }

$onDisk = @(Get-ChildItem -Path $here -Directory)
$orphans = @($onDisk | Where-Object { -not $keepSet.Contains($_.Name) })
$diskNames = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$onDisk | ForEach-Object { [void]$diskNames.Add($_.Name) }
$missing = @($keep | Where-Object { -not $diskNames.Contains($_) })

Write-Host "Folders on disk:            $($onDisk.Count)"
Write-Host "Folders in keep list:       $($keep.Count)"
Write-Host "Orphans (would be deleted): $($orphans.Count)"
Write-Host "Kept but missing on disk:   $($missing.Count)  (active listings with no local photos)"

if ($orphans.Count -gt 0) {
    Write-Host "`n--- Orphan folders ---"
    $orphans | ForEach-Object { Write-Host "  $($_.Name)" }
}
if ($onDisk.Count -gt 0 -and $orphans.Count -gt ($onDisk.Count / 2)) {
    Write-Warning "More than half of the folders on disk would be deleted. Double-check the CSV is the full, latest export."
}

if (-not $Confirm) {
    Write-Host "`nDRY RUN ONLY - nothing was deleted. Re-run with -Confirm to delete $($orphans.Count) folders."
    exit 0
}

$log = Join-Path $PSScriptRoot ("deleted_" + (Get-Date -Format "yyyyMMdd_HHmm") + ".txt")
foreach ($d in $orphans) {
    try {
        Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Stop
        Add-Content -Path $log -Value $d.Name
        Write-Host "Deleted: $($d.Name)"
    } catch { Write-Warning "Failed to delete $($d.Name): $_" }
}
Write-Host "Done. Log: $log"
