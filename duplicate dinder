<#
    Script: Duplicate File Finder & Cleaner
    Description: Finds and safely removes duplicate files to free up disk space
    
    Features:
    - Scans folders for duplicate files using hash comparison
    - Shows potential space savings
    - Safe deletion with backup option
    - Detailed reporting
    - Preview before deletion
#>

#-----------------#
# -- FUNCTIONS -- #
#-----------------#

Function Show-Header {
    Clear-Host
    Write-Host "`n#============================================#" -ForegroundColor Cyan
    Write-Host "   DUPLICATE FILE FINDER & CLEANER v1.0" -ForegroundColor Yellow
    Write-Host "   Find duplicates → Save space → Clean up" -ForegroundColor White
    Write-Host "#============================================#`n" -ForegroundColor Cyan
}

Function Get-FolderPath {
    Add-Type -AssemblyName System.Windows.Forms
    
    $FolderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $FolderBrowser.Description = "Select a folder to scan for duplicate files"
    $FolderBrowser.RootFolder = "MyComputer"
    
    if ($FolderBrowser.ShowDialog() -eq 'OK') {
        return $FolderBrowser.SelectedPath
    }
    return $null
}

Function Find-DuplicateFiles {
    param(
        [string]$Path,
        [bool]$IncludeSubfolders
    )
    
    Write-Host "`n[STEP 1] Scanning for files..." -ForegroundColor Yellow
    
    $searchOption = if ($IncludeSubfolders) { 
        [System.IO.SearchOption]::AllDirectories 
    } else { 
        [System.IO.SearchOption]::TopDirectoryOnly 
    }
    
    try {
        $files = [System.IO.Directory]::GetFiles($Path, "*.*", $searchOption)
    }
    catch {
        Write-Host "Error accessing folder: $_" -ForegroundColor Red
        return $null
    }
    
    Write-Host "  ✓ Found $($files.Count) files" -ForegroundColor Green
    
    if ($files.Count -eq 0) {
        Write-Host "`n⚠️ No files found in this location!" -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "`n[STEP 2] Calculating file hashes (this may take a while)..." -ForegroundColor Yellow
    
    $fileData = @()
    $counter = 0
    $totalFiles = $files.Count
    
    foreach ($file in $files) {
        $counter++
        
        # Progress indicator
        if ($counter % 50 -eq 0 -or $counter -eq $totalFiles) {
            $percent = [math]::Round(($counter / $totalFiles) * 100)
            Write-Progress -Activity "Hashing files" -Status "$counter of $totalFiles files ($percent%)" -PercentComplete $percent
        }
        
        try {
            $fileInfo = Get-Item $file
            
            # Skip files larger than 2GB for performance
            if ($fileInfo.Length -gt 2GB) {
                continue
            }
            
            $hash = (Get-FileHash -Path $file -Algorithm MD5).Hash
            
            $fileData += [PSCustomObject]@{
                Path = $file
                Name = $fileInfo.Name
                Size = $fileInfo.Length
                Hash = $hash
                Directory = $fileInfo.DirectoryName
                LastModified = $fileInfo.LastWriteTime
            }
        }
        catch {
            Write-Host "  [!] Skipped: $file (access denied or in use)" -ForegroundColor Red
        }
    }
    
    Write-Progress -Activity "Hashing files" -Completed
    Write-Host "  ✓ Analyzed $($fileData.Count) files" -ForegroundColor Green
    
    return $fileData
}

Function Group-Duplicates {
    param([array]$Files)
    
    Write-Host "`n[STEP 3] Identifying duplicates..." -ForegroundColor Yellow
    
    $grouped = $Files | Group-Object -Property Hash | Where-Object { $_.Count -gt 1 }
    
    if ($grouped.Count -eq 0) {
        Write-Host "  ✓ No duplicates found! Your folder is clean." -ForegroundColor Green
        return $null
    }
    
    $duplicateSets = @()
    $totalDuplicates = 0
    $totalWastedSpace = 0
    
    foreach ($group in $grouped) {
        $files = $group.Group | Sort-Object LastModified
        $original = $files[0]
        $duplicates = $files[1..($files.Count - 1)]
        
        $wastedSpace = $original.Size * $duplicates.Count
        $totalWastedSpace += $wastedSpace
        $totalDuplicates += $duplicates.Count
        
        $duplicateSets += [PSCustomObject]@{
            Original = $original
            Duplicates = $duplicates
            Count = $duplicates.Count
            WastedSpace = $wastedSpace
        }
    }
    
    Write-Host "  ✓ Found $totalDuplicates duplicate files" -ForegroundColor Green
    Write-Host "  ✓ Potential space savings: $([math]::Round($totalWastedSpace / 1MB, 2)) MB" -ForegroundColor Cyan
    
    return $duplicateSets
}

Function Show-DuplicateReport {
    param([array]$DuplicateSets)
    
    Write-Host "`n#============================================#" -ForegroundColor Magenta
    Write-Host "             DUPLICATE REPORT" -ForegroundColor Yellow
    Write-Host "#============================================#" -ForegroundColor Magenta
    
    $setNumber = 0
    foreach ($set in $DuplicateSets) {
        $setNumber++
        
        Write-Host "`n--- Duplicate Set #$setNumber ---" -ForegroundColor Cyan
        Write-Host "File Name: $($set.Original.Name)" -ForegroundColor White
        Write-Host "File Size: $([math]::Round($set.Original.Size / 1KB, 2)) KB" -ForegroundColor Gray
        Write-Host "Duplicates Found: $($set.Count)" -ForegroundColor Yellow
        Write-Host "Space Wasted: $([math]::Round($set.WastedSpace / 1KB, 2)) KB`n" -ForegroundColor Red
        
        Write-Host "  ORIGINAL (will be kept):" -ForegroundColor Green
        Write-Host "    $($set.Original.Path)" -ForegroundColor Gray
        Write-Host "    Modified: $($set.Original.LastModified)`n" -ForegroundColor Gray
        
        Write-Host "  DUPLICATES (will be deleted):" -ForegroundColor Red
        foreach ($dup in $set.Duplicates) {
            Write-Host "    $($dup.Path)" -ForegroundColor Gray
            Write-Host "    Modified: $($dup.LastModified)" -ForegroundColor Gray
        }
        
        if ($setNumber -ge 10) {
            Write-Host "`n... and $($DuplicateSets.Count - 10) more duplicate sets" -ForegroundColor Yellow
            break
        }
    }
}

Function Remove-Duplicates {
    param(
        [array]$DuplicateSets,
        [bool]$CreateBackup
    )
    
    $backupPath = $null
    
    if ($CreateBackup) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "DuplicateBackup_$timestamp"
        New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
        Write-Host "`n✓ Backup folder created: $backupPath" -ForegroundColor Green
    }
    
    Write-Host "`n[STEP 4] Deleting duplicate files..." -ForegroundColor Yellow
    
    $deletedCount = 0
    $freedSpace = 0
    $errors = 0
    
    foreach ($set in $DuplicateSets) {
        foreach ($dup in $set.Duplicates) {
            try {
                if ($CreateBackup) {
                    # Create subdirectory structure in backup
                    $relativePath = $dup.Directory.Replace($dup.Directory.Substring(0, 3), "")
                    $backupDir = Join-Path $backupPath $relativePath
                    
                    if (-not (Test-Path $backupDir)) {
                        New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
                    }
                    
                    $backupFile = Join-Path $backupDir $dup.Name
                    Copy-Item $dup.Path $backupFile -Force
                }
                
                Remove-Item $dup.Path -Force
                $deletedCount++
                $freedSpace += $dup.Size
                
                Write-Host "  ✓ Deleted: $($dup.Name)" -ForegroundColor Green
            }
            catch {
                Write-Host "  ✗ Failed to delete: $($dup.Name)" -ForegroundColor Red
                $errors++
            }
        }
    }
    
    Write-Host "`n#============================================#" -ForegroundColor Magenta
    Write-Host "              CLEANUP COMPLETE!" -ForegroundColor Green
    Write-Host "#============================================#" -ForegroundColor Magenta
    Write-Host "  Files Deleted: $deletedCount" -ForegroundColor Cyan
    Write-Host "  Space Freed: $([math]::Round($freedSpace / 1MB, 2)) MB" -ForegroundColor Yellow
    Write-Host "  Errors: $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Green" })
    
    if ($CreateBackup) {
        Write-Host "`n  Backup Location: $backupPath" -ForegroundColor Cyan
    }
    
    # Generate report file
    $reportPath = "DuplicateCleanup_Report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $report = @"
═══════════════════════════════════════════════════
  DUPLICATE FILE CLEANUP REPORT
  Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
═══════════════════════════════════════════════════

SUMMARY
-------
Files Deleted: $deletedCount
Space Freed: $([math]::Round($freedSpace / 1MB, 2)) MB
Errors: $errors
Backup Created: $(if ($CreateBackup) { "Yes - $backupPath" } else { "No" })

DETAILS
-------
"@
    
    foreach ($set in $DuplicateSets) {
        $report += "`n`nOriginal: $($set.Original.Path)"
        foreach ($dup in $set.Duplicates) {
            $report += "`n  Deleted: $($dup.Path)"
        }
    }
    
    $report | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "`n  Report saved: $reportPath" -ForegroundColor Green
}

#--------------------------#
# -- MAIN SCRIPT -- #
#--------------------------#

do {
    Show-Header
    
    Write-Host "This tool will help you:" -ForegroundColor White
    Write-Host "  • Find duplicate files in any folder" -ForegroundColor Gray
    Write-Host "  • Preview duplicates before deletion" -ForegroundColor Gray
    Write-Host "  • Safely delete duplicates (keeps oldest file)" -ForegroundColor Gray
    Write-Host "  • Optional backup of deleted files" -ForegroundColor Gray
    Write-Host "  • See how much space you'll save`n" -ForegroundColor Gray
    
    # Get folder to scan
    Read-Host "Press Enter to select a folder to scan"
    $scanPath = Get-FolderPath
    
    if (-not $scanPath) {
        Write-Host "`n❌ No folder selected. Exiting..." -ForegroundColor Red
        Start-Sleep -Seconds 2
        exit
    }
    
    Write-Host "`nSelected folder: $scanPath" -ForegroundColor Cyan
    
    # Ask about subfolders
    Write-Host "`nInclude subfolders? [Y/N]" -ForegroundColor Yellow
    $includeSubfolders = (Read-Host).ToUpper() -eq "Y"
    
    # Scan for files
    $files = Find-DuplicateFiles -Path $scanPath -IncludeSubfolders $includeSubfolders
    
    if (-not $files) {
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    # Find duplicates
    $duplicateSets = Group-Duplicates -Files $files
    
    if (-not $duplicateSets) {
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    # Show report
    Show-DuplicateReport -DuplicateSets $duplicateSets
    
    # Ask what to do
    Write-Host "`n#============================================#" -ForegroundColor Magenta
    Write-Host "What would you like to do?" -ForegroundColor Yellow
    Write-Host "[D] Delete duplicates (with backup)" -ForegroundColor Cyan
    Write-Host "[Q] Delete duplicates (NO backup - faster)" -ForegroundColor Red
    Write-Host "[S] Save report and exit (don't delete)" -ForegroundColor Green
    Write-Host "[C] Cancel" -ForegroundColor Gray
    
    $choice = (Read-Host "`nYour choice").ToUpper()
    
    switch ($choice) {
        "D" {
            Write-Host "`n⚠️ WARNING: About to delete $($duplicateSets.Duplicates.Count) files!" -ForegroundColor Red
            Write-Host "A backup will be created first." -ForegroundColor Yellow
            $confirm = Read-Host "Type 'DELETE' to confirm"
            
            if ($confirm -eq "DELETE") {
                Remove-Duplicates -DuplicateSets $duplicateSets -CreateBackup $true
            }
            else {
                Write-Host "`n❌ Cancelled. No files were deleted." -ForegroundColor Yellow
            }
        }
        "Q" {
            Write-Host "`n⚠️ DANGER: About to delete $($duplicateSets.Duplicates.Count) files WITHOUT backup!" -ForegroundColor Red
            Write-Host "This cannot be undone!" -ForegroundColor Red
            $confirm = Read-Host "Type 'DELETE FOREVER' to confirm"
            
            if ($confirm -eq "DELETE FOREVER") {
                Remove-Duplicates -DuplicateSets $duplicateSets -CreateBackup $false
            }
            else {
                Write-Host "`n❌ Cancelled. No files were deleted." -ForegroundColor Yellow
            }
        }
        "S" {
            $reportPath = "DuplicateReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
            $report = "Duplicate Files Found: $($duplicateSets.Count) sets`n`n"
            
            foreach ($set in $duplicateSets) {
                $report += "Original: $($set.Original.Path)`n"
                foreach ($dup in $set.Duplicates) {
                    $report += "  Duplicate: $($dup.Path)`n"
                }
                $report += "`n"
            }
            
            $report | Out-File -FilePath $reportPath -Encoding UTF8
            Write-Host "`n✓ Report saved: $reportPath" -ForegroundColor Green
        }
        "C" {
            Write-Host "`n❌ Cancelled." -ForegroundColor Yellow
        }
        default {
            Write-Host "`n❌ Invalid choice." -ForegroundColor Red
        }
    }
    
    Write-Host "`n[Y] Scan another folder  [N] Exit" -ForegroundColor Cyan
    $again = Read-Host "Your choice"
    
} while ($again.ToUpper() -eq "Y")

Write-Host "`n👋 Thanks for using Duplicate File Finder!" -ForegroundColor Cyan
Start-Sleep -Seconds 2
