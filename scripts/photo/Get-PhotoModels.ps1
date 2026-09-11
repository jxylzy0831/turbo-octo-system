#Requires -Version 5.1
<#
.SYNOPSIS
    把中转站/自建网关支持的模型列表打出来，用来确认三个模型 id 到底叫什么。

.DESCRIPTION
    修图脚本失败最常见的两个原因：
      1) 网关没开 /images/edits（只开了文生图）；
      2) 模型 id 猜错了。
    先跑这个把 id 抄准，比反复试快得多。

.EXAMPLE
    .\Get-PhotoModels.ps1 -BaseUrl 'https://api.xxx.com/v1' -ApiKey 'sk-...'
#>
[CmdletBinding()]
param(
    [string]$BaseUrl = $env:PHOTO_BASE_URL,
    [string]$ApiKey = $env:PHOTO_API_KEY,
    [switch]$Json,
    [int]$TimeoutSec = 60,
    [string]$EnvFile = (Join-Path $PSScriptRoot 'photo.env.ps1')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if ((-not $ApiKey -or -not $BaseUrl) -and (Test-Path -LiteralPath $EnvFile)) {
    . $EnvFile
    if (-not $BaseUrl) { $BaseUrl = $env:PHOTO_BASE_URL }
    if (-not $ApiKey) { $ApiKey = $env:PHOTO_API_KEY }
}
if (-not $BaseUrl) { Write-Host '缺少 BaseUrl：设置 $env:PHOTO_BASE_URL 或写 scripts/photo/photo.env.ps1' -ForegroundColor Red; exit 1 }
if (-not $ApiKey) { Write-Host '缺少 ApiKey：设置 $env:PHOTO_API_KEY 或写 scripts/photo/photo.env.ps1' -ForegroundColor Red; exit 1 }

$BaseUrl = $BaseUrl.TrimEnd('/')
$hdr = Join-Path ([System.IO.Path]::GetTempPath()) ("phdr-" + [guid]::NewGuid().ToString('N') + '.txt')
[System.IO.File]::WriteAllText($hdr, "Authorization: Bearer $ApiKey", [System.Text.UTF8Encoding]::new($false))

try {
    $raw = & curl.exe -sS "$BaseUrl/models" -H "@$hdr" -w "`n__HTTP_STATUS__:%{http_code}" -m $TimeoutSec 2>&1 | Out-String
} finally {
    Remove-Item -LiteralPath $hdr -ErrorAction SilentlyContinue
}

$status = 0
$m = [regex]::Match($raw, '__HTTP_STATUS__:(\d+)\s*$')
if ($m.Success) { $status = [int]$m.Groups[1].Value; $raw = $raw.Substring(0, $m.Index) }
$body = $raw.TrimEnd()

if ($status -ne 200) {
    Write-Host "GET $BaseUrl/models 失败：HTTP $status" -ForegroundColor Red
    if ($body) {
        if ($body.Length -gt 800) { $body = $body.Substring(0, 800) + ' …' }
        Write-Host $body -ForegroundColor DarkGray
    }
    Write-Host ''
    Write-Host '若这里 401/403：key 不对或没带对前缀。若 404：base_url 少了或多了 /v1。' -ForegroundColor Yellow
    exit 1
}

if ($Json) { Write-Host $body; exit 0 }

$obj = $body | ConvertFrom-Json
$ids = @()
if ($obj.data) { $ids = @($obj.data | ForEach-Object { $_.id }) }
elseif ($obj.models) { $ids = @($obj.models | ForEach-Object { if ($_.id) { $_.id } else { $_ } }) }

if (-not $ids.Count) { Write-Host '响应里没解析出模型 id，原始响应：' -ForegroundColor Yellow; Write-Host $body; exit 0 }

Write-Host "共 $($ids.Count) 个模型：" -ForegroundColor Cyan
$ids | Sort-Object | ForEach-Object { Write-Host "  $_" }

Write-Host ''
Write-Host '挑模型时重点看这几类关键词：' -ForegroundColor Cyan
Write-Host '  看图（诊断段 -VisionModel）  : gpt-4o / gpt-4.1 / gpt-5 / claude / gemini / qwen-vl / vision'
Write-Host '  图像编辑（修图段 -ImageModel）: image / gpt-image / seedream / flux / kontext / qwen-image / nano-banana'
Write-Host ''
if (-not ($ids -match 'image')) {
    Write-Host '注意：列表里没看到名字带 image 的模型，这个站可能没开图像接口。' -ForegroundColor Yellow
}
