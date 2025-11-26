<#
    Script: PNGify - Complete Version
    By: Stephen Chapman (Enhanced)
    Site: http://dsasmblr.com/blog
    GitHub: http://github.com/dsasmblr
    
    Description: Extracts base64-encoded images (PNG, JPEG, GIF, WebP) from files
                 and saves them with proper metadata and organization.
#>

#-----------------#
# -- FUNCTIONS -- #
#-----------------#

# Script header
Function Show-Header {
    Write-Host "#---------------------------#" -ForegroundColor Cyan
    Write-Host "       P-N-G-i-f-y v2.0      " -ForegroundColor Cyan
    Write-Host "   By Stephen Chapman        " -ForegroundColor Cyan
    Write-Host "      dsasmblr.com           " -ForegroundColor Cyan
    Write-Host "#---------------------------#`n" -ForegroundColor Cyan
}

# File selector dialog box
Function Get-FileName {
    param([string]$InitialDirectory)
    
    Add-Type -AssemblyName System.Windows.Forms
    
    $OpenFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $OpenFileDialog.InitialDirectory = $InitialDirectory
    $OpenFileDialog.Filter = "All files (*.*)|*.*|HTML files (*.html;*.htm)|*.html;*.htm|CSS files (*.css)|*.css|JavaScript files (*.js)|*.js"
    $OpenFileDialog.Title = "Select a file to extract images from"
    
    if ($OpenFileDialog.ShowDialog() -eq 'OK') {
        return $OpenFileDialog.FileName
    }
    return $null
}

# Detect image format from base64 header
Function Get-ImageFormat {
    param([string]$Base64String)
    
    $header = $Base64String.Substring(0, [Math]::Min(20, $Base64String.Length))
    
    if ($header.StartsWith("iVBOR")) { return "png" }
    elseif ($header.StartsWith("/9j/")) { return "jpg" }
    elseif ($header.StartsWith("R0lGOD")) { return "gif" }
    elseif ($header.StartsWith("UklGR")) { return "webp" }
    elseif ($header.StartsWith("Qk")) { return "bmp" }
    else { return "png" } # Default to PNG
}

# Extract images with multiple format support
Function Extract-Images {
    param(
        [string]$FilePath,
        [string]$OutputDir
    )
    
    Write-Host "`nAnalyzing file: $([System.IO.Path]::GetFileName($FilePath))" -ForegroundColor Yellow
    Write-Host "Reading file contents..." -ForegroundColor Gray
    
    try {
        $FileContent = Get-Content -Path $FilePath -Raw -ErrorAction Stop
    }
    catch {
        Write-Host "Error reading file: $_" -ForegroundColor Red
        return 0
    }
    
    # Regex patterns for different image formats
    $patterns = @{
        'png'  = 'data:image/png;base64,([A-Za-z0-9+/=]+)'
        'jpg'  = 'data:image/(?:jpeg|jpg);base64,([A-Za-z0-9+/=]+)'
        'gif'  = 'data:image/gif;base64,([A-Za-z0-9+/=]+)'
        'webp' = 'data:image/webp;base64,([A-Za-z0-9+/=]+)'
    }
    
    $count = 0
    $stats = @{}
    
    foreach ($format in $patterns.Keys) {
        $stats[$format] = 0
        $matches = [regex]::Matches($FileContent, $patterns[$format])
        
        foreach ($match in $matches) {
            try {
                $base64Data = $match.Groups[1].Value
                $base64Data = $base64Data -replace '\s', '' # Remove whitespace
                
                # Validate base64 string
                if ($base64Data.Length -eq 0 -or $base64Data.Length % 4 -ne 0) {
                    continue
                }
                
                $imageBytes = [Convert]::FromBase64String($base64Data)
                
                # Skip if image is too small (likely corrupt)
                if ($imageBytes.Length -lt 100) {
                    continue
                }
                
                $count++
                $detectedFormat = Get-ImageFormat $base64Data
                $fileName = "{0:D4}_{1}.{2}" -f $count, $format, $detectedFormat
                $outputPath = Join-Path $OutputDir $fileName
                
                [System.IO.File]::WriteAllBytes($outputPath, $imageBytes)
                $stats[$format]++
                
                Write-Host "  [✓] Extracted: $fileName ($($imageBytes.Length) bytes)" -ForegroundColor Green
            }
            catch {
                Write-Host "  [✗] Failed to decode image #$count : $_" -ForegroundColor Red
            }
        }
    }
    
    # Summary
    Write-Host "`n--- Extraction Summary ---" -ForegroundColor Cyan
    foreach ($format in $stats.Keys) {
        if ($stats[$format] -gt 0) {
            Write-Host "  $($format.ToUpper()): $($stats[$format]) images" -ForegroundColor White
        }
    }
    Write-Host "  Total: $count images extracted" -ForegroundColor Yellow
    
    return $count
}

# Create output directory with conflict handling
Function New-OutputDirectory {
    param([string]$BaseName)
    
    $dirName = $BaseName
    $counter = 1
    
    while (Test-Path $dirName) {
        Write-Host "`nDirectory '$dirName' already exists." -ForegroundColor Yellow
        Write-Host "[O] Overwrite  [N] New directory  [C] Cancel" -ForegroundColor Cyan
        
        $choice = Read-Host "Choose an option"
        
        switch ($choice.ToUpper()) {
            "O" {
                Write-Host "Using existing directory (files may be overwritten)..." -ForegroundColor Yellow
                return $dirName
            }
            "N" {
                $dirName = "${BaseName}_${counter}"
                $counter++
            }
            "C" {
                return $null
            }
            default {
                Write-Host "Invalid choice. Please enter O, N, or C." -ForegroundColor Red
            }
        }
    }
    
    New-Item -Path $dirName -ItemType Directory -Force | Out-Null
    Write-Host "Created directory: $dirName" -ForegroundColor Green
    return $dirName
}

#--------------------------#
# -- SCRIPT ENTRY POINT -- #
#--------------------------#

# Main execution loop
$storedPath = ""

do {
    Clear-Host
    Show-Header
    
    # Determine initial directory
    if (-not $storedPath) {
        $steamPath = "C:\Program Files (x86)\Steam\steamapps\common"
        $initialDir = if (Test-Path $steamPath) { $steamPath } else { [Environment]::GetFolderPath('MyDocuments') }
    }
    else {
        $initialDir = $storedPath
    }
    
    Write-Host "Press Enter to select a file for image extraction..." -ForegroundColor White
    Read-Host
    
    # Get input file
    $inputFile = Get-FileName -InitialDirectory $initialDir
    
    if (-not $inputFile) {
        Write-Host "`nNo file selected. Exiting..." -ForegroundColor Red
        Start-Sleep -Seconds 2
        exit
    }
    
    $storedPath = Split-Path $inputFile -Parent
    
    # Create output directory
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($inputFile) + "_images"
    $outputDir = New-OutputDirectory -BaseName $baseName
    
    if (-not $outputDir) {
        Write-Host "`nOperation cancelled." -ForegroundColor Red
        Start-Sleep -Seconds 2
        continue
    }
    
    # Extract images
    $extractedCount = Extract-Images -FilePath $inputFile -OutputDir $outputDir
    
    if ($extractedCount -gt 0) {
        Write-Host "`n✓ Operation completed successfully!" -ForegroundColor Green
        Start-Sleep -Seconds 1
        Invoke-Item $outputDir
    }
    else {
        Write-Host "`n⚠ No images found in the selected file." -ForegroundColor Yellow
    }
    
    # Ask to run again
    Write-Host "`n[Y] Process another file  [N] Exit" -ForegroundColor Cyan
    $response = Read-Host "Choose an option"
    
} while ($response.ToUpper() -eq "Y")

Write-Host "`nThank you for using PNGify! Goodbye." -ForegroundColor Cyan
Start-Sleep -Seconds 1