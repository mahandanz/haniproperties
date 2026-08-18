# delete_folders.ps1
# Run this script FROM INSIDE the "unitpic" folder
# (C:\Users\rashd\OneDrive\Documents\GitHub\haniproperties\images\unitpic)
#
# It reads folders_to_delete.txt (must be in the same directory as this
# script, or edit $listFile below) and deletes each listed subfolder.
#
# Usage:
#   Dry run (just shows what would be deleted, deletes nothing):
#     .\delete_folders.ps1
#   Actually delete:
#     .\delete_folders.ps1 -Confirm

param(
    [switch]$Confirm
)

$listFile = Join-Path $PSScriptRoot "folders_to_delete.txt"

if (-not (Test-Path $listFile)) {
    Write-Error "Could not find folders_to_delete.txt next to this script."
    exit 1
}

$folders = Get-Content $listFile | Where-Object { $_.Trim() -ne "" }

$found = @()
$missing = @()

foreach ($name in $folders) {
    $path = Join-Path (Get-Location) $name
    if (Test-Path $path) {
        $found += $path
    } else {
        $missing += $name
    }
}

Write-Host "Total folders in list: $($folders.Count)"
Write-Host "Found on disk (would be deleted): $($found.Count)"
Write-Host "Not found on disk (skipped): $($missing.Count)"

if ($missing.Count -gt 0) {
    Write-Host "`n--- Missing / not found ---"
    $missing | ForEach-Object { Write-Host "  $_" }
}

if (-not $Confirm) {
    Write-Host "`nDRY RUN ONLY - nothing was deleted."
    Write-Host "Re-run with -Confirm to actually delete these $($found.Count) folders."
    exit 0
}

Write-Host "`nDeleting $($found.Count) folders..."
foreach ($path in $found) {
    try {
        Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
        Write-Host "Deleted: $path"
    } catch {
        Write-Warning "Failed to delete $path : $_"
    }
}
Write-Host "Done."
