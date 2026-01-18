<# * * * claude generated 
# ArXiv PDF Renamer and EPUB Downloader
# Renames arXiv PDFs to: Title_Author_arXivID.pdf
# Downloads matching EPUB files automatically
# 20260108@0644 
# kind of strange that claude messed up a simple powershell script ... did not start w/ correct powershell syntax
# used shortcut powershell slang which breaks on version changes; completely messed up "" or ' ' in regex strings ... note LLM's
# have to correct themselves all the time with regex calls .. the llm next token for regex is wrong on anything complicated
# they must have a tool call checker for just regex now since all models do the same errors.  But poweshell should be the simpliest
# yet it mess that up too...
# i need to refine my boiler plate.  Why are the defaults powershell code so ugly in claude...there are plenty of examples of good
# modern powershell ... yet the product is more one-off style of coding...which i guess is the majority of training data.
# gemini3 python code follows modern standards .. claude powershell is workable but poor ai slop
and the first  error is you cannot have [CmdletBinding()] at the top of a script and i lost my pretty prints wrapping it...
so you got to read the script for the parameters...  should be easy to fix but i'm sleepy...

as always mrphelps if your caught or ki.... published ai generated slop will lead to model collapse and the end of the universe and we will disclaim any knowledge and blame the trumper's...
#>
function ArxivRENAMEid2TitleAuthorDLepubs()
{
[CmdletBinding()]
param(
    [Parameter(Position=0, HelpMessage="Folder containing PDF files to process")]
    [ValidateScript({Test-Path $_ -PathType Container})]
    [string]$FolderPath = ".",
    
    [Parameter(HelpMessage="Test run without making changes")]
    [switch]$WhatIf,
    
    [Parameter(HelpMessage="Minimum delay in seconds between requests")]
    [ValidateRange(1, 120)]
    [int]$MinDelaySec = 10,
    
    [Parameter(HelpMessage="Maximum delay in seconds between requests")]
    [ValidateRange(1, 120)]
    [int]$MaxDelaySec = 50,
    
    [Parameter(HelpMessage="Skip EPUB downloads")]
    [switch]$SkipEpub
)
}
# Display parameters
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ArXiv PDF Renamer and EPUB Downloader" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Parameters:" -ForegroundColor Yellow
Write-Host "  FolderPath   : $FolderPath" -ForegroundColor White
Write-Host "  WhatIf       : $WhatIf" -ForegroundColor White
Write-Host "  MinDelaySec  : $MinDelaySec" -ForegroundColor White
Write-Host "  MaxDelaySec  : $MaxDelaySec" -ForegroundColor White
Write-Host "  SkipEpub     : $SkipEpub" -ForegroundColor White
Write-Host ""

function Get-ArXivMetadata {
    param([string]$ArXivId)
    
    if ([string]::IsNullOrWhiteSpace($ArXivId)) {
        Write-Warning "Empty arXiv ID provided"
        return $null
    }
    
    # Clean the arXiv ID (handle various formats)
    $cleanId = $ArXivId -replace "v\d+$", ""  # Remove version number
    
    try {
        $url = "https://arxiv.org/abs/$cleanId"
        Write-Verbose "Fetching: $url"
        
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing
        $html = $response.Content
        
        # Extract title - look for meta tag or h1.title
        $title = ""
        if ($html -match '<meta name="citation_title" content="([^"]+)"') {
            $title = $matches[1]
        }
        elseif ($html -match '<h1 class="title[^"]*">.*?<span[^>]*>([^<]+)</span>') {
            $title = $matches[1]
        }
        elseif ($html -match '<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>') {
            $titleBlock = $matches[1]
            if ($titleBlock -match '>([^<]+)</') {
                $title = $matches[1]
            }
        }
        
        # Extract all authors - collect multiple authors
        $authors = @()
        $authorMatches = [regex]::Matches($html, '<meta name="citation_author" content="([^"]+)"')
        if ($authorMatches.Count -gt 0) {
            foreach ($match in $authorMatches) {
                $authors += $match.Groups[1].Value
            }
        }
        elseif ($html -match '<div class="authors">.*?<a[^>]*>([^<]+)</a>') {
            $authors += $matches[1]
        }
        
        # Clean up extracted text
        $title = $title -replace "&#39;", "'" -replace "&quot;", '"' -replace "&amp;", "&"
        $title = $title -replace "\s+", " " -replace "`n", " "
        $title = $title.Trim()
        
        if ([string]::IsNullOrWhiteSpace($title)) {
            Write-Warning "Could not extract title from HTML for $cleanId"
            return $null
        }
        
        # Process authors - get last names and join them
        $authorString = ""
        if ($authors.Count -eq 0) {
            Write-Warning "Could not extract authors from HTML for $cleanId"
            $authorString = "Unknown"
        }
        else {
            $lastNames = @()
            foreach ($auth in $authors) {
                $auth = $auth -replace "&#39;", "'" -replace "&quot;", '"' -replace "&amp;", "&"
                $auth = $auth.Trim() -replace ",$", ""  # Remove trailing comma
                
                # Get last name (last word)
                $lastName = ($auth -split "\s+")[-1]
                $lastNames += $lastName
            }
            
            # Join authors with no spaces and limit to 30 chars
            $authorString = ($lastNames -join "") -replace "\s+", ""
            if ($authorString.Length -gt 30) {
                $authorString = $authorString.Substring(0, 30)
            }
        }
        
        return @{
            Title = $title
            Author = $authorString
            ArXivId = $cleanId
            Success = $true
        }
    }
    catch {
        Write-Warning "Failed to fetch metadata for $ArXivId : $($_.Exception.Message)"
        return $null
    }
}

function Clean-Filename {
    param([string]$Name)
    
    # Remove invalid filename characters
    $invalid = [System.IO.Path]::GetInvalidFileNameChars()
    $cleaned = $Name
    foreach ($char in $invalid) {
        $cleaned = $cleaned.Replace($char, "_")
    }
    
    # Replace colon and other problematic chars
    $cleaned = $cleaned -replace ":", "_"
    $cleaned = $cleaned -replace '"', ""
    $cleaned = $cleaned -replace "\*", ""
    $cleaned = $cleaned -replace "\?", ""
    
    # Replace multiple spaces/underscores with single underscore
    $cleaned = $cleaned -replace "\s+", "_"
    $cleaned = $cleaned -replace "_+", "_"
    $cleaned = $cleaned -replace "^_|_$", ""  # Trim underscores from ends
    
    # Limit length (Windows has 260 char path limit)
    if ($cleaned.Length -gt 150) {
        $cleaned = $cleaned.Substring(0, 150)
    }
    
    return $cleaned
}

function Extract-ArXivId {
    param([string]$Filename)
    
    # Match common arXiv ID patterns
    # New format: 0704.0001 or 1234.56789 (required format)
    # With version: 1234.56789v1
    
    # Try new format first (YYMM.NNNNN)
    if ($Filename -match "(\d{4}\.\d{4,5})(v\d+)?") {
        return $matches[1]
    }
    # Old format: arch-ive/9901001 or astro-ph/0001001
    elseif ($Filename -match "([a-z\-]+/\d{7})(v\d+)?") {
        return $matches[1]
    }
    
    return $null
}

function Download-ArXivEpub {
    param(
        [string]$ArXivId,
        [string]$OutputPath
    )
    
    try {
        $epubUrl = "https://arxiv.org/e-print/$ArXivId"
        Write-Host "    Downloading EPUB..." -ForegroundColor Cyan -NoNewline
        
        $response = Invoke-WebRequest -Uri $epubUrl -Method Head -ErrorAction Stop
        
        # Download the EPUB
        Invoke-WebRequest -Uri $epubUrl -OutFile $OutputPath -ErrorAction Stop
        Write-Host " Done" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host " Not available" -ForegroundColor DarkGray
        return $false
    }
}

# Main script
$folderFullPath = Resolve-Path $FolderPath
Write-Host "Processing folder: $folderFullPath" -ForegroundColor Yellow
Write-Host ""

$pdfFiles = Get-ChildItem -Path $FolderPath -Filter "*.pdf"

if ($pdfFiles.Count -eq 0) {
    Write-Host "No PDF files found in the specified folder." -ForegroundColor Red
    exit
}

Write-Host "Found $($pdfFiles.Count) PDF file(s)" -ForegroundColor Cyan
Write-Host ""

$processed = 0
$skipped = 0
$failed = 0
$epubDownloaded = 0

foreach ($pdf in $pdfFiles) {
    Write-Host "[$($processed + $skipped + $failed + 1)/$($pdfFiles.Count)] $($pdf.Name)" -ForegroundColor White
    
    # Extract arXiv ID from filename
    $arxivId = Extract-ArXivId -Filename $pdf.Name
    
    if (-not $arxivId) {
        Write-Host "  Skipped: Could not extract arXiv ID" -ForegroundColor Yellow
        $skipped++
        Write-Host ""
        continue
    }
    
    Write-Host "  ArXiv ID: $arxivId" -ForegroundColor Gray
    
    # Add random delay to avoid rate limiting (except for first request)
    if ($processed -gt 0) {
        $delaySec = Get-Random -Minimum $MinDelaySec -Maximum ($MaxDelaySec + 1)
        Write-Host "  Waiting $delaySec seconds..." -ForegroundColor DarkGray
        Start-Sleep -Seconds $delaySec
    }
    
    # Get metadata from arXiv HTML page
    $metadata = Get-ArXivMetadata -ArXivId $arxivId
    
    if (-not $metadata) {
        Write-Host "  Failed: Could not retrieve metadata" -ForegroundColor Red
        $failed++
        Write-Host ""
        continue
    }
    
    Write-Host "  Title: $($metadata.Title)" -ForegroundColor Gray
    Write-Host "  Authors: $($metadata.Author)" -ForegroundColor Gray
    
    # Create new filename
    $cleanTitle = Clean-Filename -Name $metadata.Title
    $cleanAuthor = Clean-Filename -Name $metadata.Author
    $newName = "${cleanTitle}_${cleanAuthor}_$($metadata.ArXivId).pdf"
    $newPath = Join-Path -Path $pdf.DirectoryName -ChildPath $newName
    
    # Rename the PDF file
    if (-not $WhatIf) {
        if (Test-Path $newPath) {
            Write-Host "  PDF: Already exists with new name" -ForegroundColor DarkGray
        }
        else {
            try {
                Rename-Item -Path $pdf.FullName -NewName $newName -ErrorAction Stop
                Write-Host "  PDF: Renamed successfully" -ForegroundColor Green
            }
            catch {
                Write-Host "  Failed to rename: $($_.Exception.Message)" -ForegroundColor Red
                $failed++
                Write-Host ""
                continue
            }
        }
    }
    else {
        Write-Host "  [WhatIf] Would rename to:" -ForegroundColor Yellow
        Write-Host "    $newName" -ForegroundColor DarkYellow
    }
    
    # Download EPUB
    if (-not $SkipEpub -and -not $WhatIf) {
        $epubName = "${cleanTitle}_${cleanAuthor}_$($metadata.ArXivId).epub"
        $epubPath = Join-Path -Path $pdf.DirectoryName -ChildPath $epubName
        
        if (Test-Path $epubPath) {
            Write-Host "  EPUB: Already exists" -ForegroundColor DarkGray
        }
        else {
            $downloaded = Download-ArXivEpub -ArXivId $arxivId -OutputPath $epubPath
            if ($downloaded) {
                $epubDownloaded++
            }
        }
    }
    elseif (-not $WhatIf) {
        Write-Host "  EPUB: Skipped (use without -SkipEpub to download)" -ForegroundColor DarkGray
    }
    
    $processed++
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Total files      : $($pdfFiles.Count)" -ForegroundColor White
Write-Host "  Processed        : $processed" -ForegroundColor Cyan
Write-Host "  Skipped          : $skipped" -ForegroundColor Yellow
Write-Host "  Failed           : $failed" -ForegroundColor Red
if (-not $SkipEpub -and -not $WhatIf) {
    Write-Host "  EPUBs downloaded : $epubDownloaded" -ForegroundColor Cyan
}
Write-Host ""

if ($WhatIf) {
    Write-Host "This was a test run. Remove -WhatIf to actually rename files." -ForegroundColor Yellow
    Write-Host ""
}