param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [int]$FromPage = 0,
    [int]$ToPage = 0
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $InputPath).Path
$target = [System.IO.Path]::GetFullPath($OutputPath)
$targetDirectory = [System.IO.Path]::GetDirectoryName($target)
[System.IO.Directory]::CreateDirectory($targetDirectory) | Out-Null

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($source, $false, $true, $false, '', '', $false, '', '', 0, $false, $true, 0, $true, $false, $false)
    if ($FromPage -gt 0 -and $ToPage -ge $FromPage) {
        $document.ExportAsFixedFormat($target, 17, $false, 0, 3, $FromPage, $ToPage, 0, $true, $true, 0, $true, $true, $false)
    }
    else {
        $document.ExportAsFixedFormat($target, 17)
    }
}
finally {
    if ($null -ne $document) {
        try { $document.Close(0) } catch { }
        try { [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null } catch { }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output $target
