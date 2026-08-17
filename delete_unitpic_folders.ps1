# delete_unitpic_folders.ps1
# Run from the ROOT of your haniproperties.com repo (where images\unitpic lives)
#
# Reads folder names to delete from "folders_to_delete.txt" (one folder name per line)
# in the same folder as this script.
#
# USAGE:
#   .\delete_unitpic_folders.ps1            -> DRY RUN (shows what would be deleted)
#   .\delete_unitpic_folders.ps1 -Force     -> ACTUALLY DELETES the folders

param(
    [switch]$Force
)

$BaseDir = "images\unitpic"
$ListFile = "folders_to_delete.txt"

if (-not (Test-Path $BaseDir)) {
    Write-Host "ERROR: '$BaseDir' not found in current directory." -ForegroundColor Red
    Write-Host "cd into the root of your haniproperties.com repo and try again."
    exit 1
}

if (-not (Test-Path $ListFile)) {
    Write-Host "ERROR: '$ListFile' not found." -ForegroundColor Red
    Write-Host "Create a text file called '$ListFile' in this same folder,"
    Write-Host "with one folder name per line (no URLs, no slashes - just the folder name)."
    exit 1
}

$Folders = Get-Content $ListFile | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" } | Sort-Object -Unique

Write-Host "Total folders in list: $($Folders.Count)"
Write-Host ""

$Found = 0
$Missing = 0

foreach ($f in $Folders) {
    $path = Join-Path $BaseDir $f
    if (Test-Path $path) {
        $Found++
        if ($Force) {
            Remove-Item -Path $path -Recurse -Force
            Write-Host "DELETED: $path" -ForegroundColor Green
        } else {
            Write-Host "[dry-run] would delete: $path"
        }
    } else {
        $Missing++
        Write-Host "[not found, skipping]: $path" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Summary: $Found folders found, $Missing not found."
if (-not $Force) {
    Write-Host ""
    Write-Host "This was a DRY RUN. Nothing was deleted." -ForegroundColor Yellow
    Write-Host "Review the list above, then re-run with -Force to actually delete:"
    Write-Host "  .\delete_unitpic_folders.ps1 -Force"
}
