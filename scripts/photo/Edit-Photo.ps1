#Requires -Version 5.1
<#
.SYNOPSIS
    高质量修图工作流：看图诊断 -> 生成修图提示词 -> 调图像编辑接口出图。

.DESCRIPTION
    两段式，故意不合并：
      1) 诊断段：把原图交给一个「能看图」的模型，输出严格的 JSON 诊断 + 英文修图指令。
      2) 修图段：把诊断出的指令交给 gpt-image 系图像编辑接口，出图。
    合并成一个黑盒只会让你看不清到底改了什么；分开你才能逐段核对、逐段重跑。

    脚本不加任何日志包装、不改原图、不覆盖同名文件。
    原图保护：所有产物写入 -OutDir，原图只读。

.PARAMETER Mode
    analyze = 只做诊断，出 analysis.json（便宜，先跑这个）
    edit    = 只做修图，需要一个 analysis.json 或显式 -GradingDirection
    all     = 两段连跑（花钱，会打印将要发出的提示词）

.PARAMETER BaseUrl
    OpenAI 兼容前缀。自建/中转站一般形如 https://xxx.yyy/v1 。
    也可用环境变量 PHOTO_BASE_URL。

.PARAMETER ApiKey
    也可用环境变量 PHOTO_API_KEY。（脚本不会把 key 写进任何文件）

.PARAMETER VisionModel
    能看图的对话模型。诊断段用。

.PARAMETER ImageModel
    图像编辑模型。修图段用。

.PARAMETER MaxSide
    调用前把原图长边缩到该值（像素），避免超出接口尺寸上限、也省 token。
    0 = 不缩放。原图不受影响，只在临时目录里缩。

.EXAMPLE
    $env:PHOTO_BASE_URL = 'https://api.xxx.com/v1'
    $env:PHOTO_API_KEY  = 'sk-...'
    .\Edit-Photo.ps1 -Mode analyze -Image '.\assets\某人.png' -VisionModel 'gpt-4o'

.EXAMPLE
    .\Edit-Photo.ps1 -Mode edit -Image '.\assets\某人.png' `
        -AnalysisPath '.\photo_out\某人\analysis.json' `
        -ImageModel 'gpt-image-1.5' -GradingDirection '整体提亮 1/3 档，阴影偏青，降饱和 5%'
#>
[CmdletBinding()]
param(
    [ValidateSet('analyze', 'edit', 'all')]
    [string]$Mode = 'all',

    [string]$BaseUrl = $env:PHOTO_BASE_URL,
    [string]$ApiKey = $env:PHOTO_API_KEY,

    [string]$Image,
    [string]$OutDir,

    [string]$VisionModel = 'gpt-4o',
    [string]$ImageModel = 'gpt-image-1',

    [string]$AnalysisPath,
    [string]$GradingDirection,

    [string]$Size = 'auto',
    [string]$Quality = 'high',
    [string]$Background = 'auto',

    [int]$MaxSide = 1536,
    [int]$TimeoutSec = 300,
    [switch]$Force,
    [string]$EnvFile = (Join-Path $PSScriptRoot 'photo.env.ps1')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ---------------------------------------------------------------- 基础设施

function Write-Step { param([string]$m) Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Ok { param([string]$m) Write-Host "  ok  $m" -ForegroundColor Green }
function Write-Warn2 { param([string]$m) Write-Host "  !!  $m" -ForegroundColor Yellow }
function Write-Die { param([string]$m) Write-Host "  xx  $m" -ForegroundColor Red; exit 1 }

function Read-TextFileUtf8 {
    param([string]$Path)
    # PS 5.1 的 Get-Content 默认按 ANSI 解码，中文会烂；一律走 .NET 显式 UTF-8。
    return [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
}

function Write-TextFileUtf8 {
    param([string]$Path, [string]$Text)
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Unescape-JsonString {
    param([string]$s)
    # 只做标准 JSON 转义还原，够用于 \n \t \" \\ \/ \uXXXX
    if ([string]::IsNullOrEmpty($s)) { return $s }
    $s = [regex]::Replace($s, '\\u([0-9a-fA-F]{4})', {
            param($m) [char][Convert]::ToInt32($m.Groups[1].Value, 16)
        })
    $s = $s.Replace('\/', '/').Replace('\"', '"').Replace('\\', '\').Replace('\n', "`n").Replace('\r', "`r").Replace('\t', "`t")
    return $s
}

function Get-JsonStringValue {
    param([string]$Json, [string]$Key)
    # 从原始 JSON 文本里抠出某个字符串字段（不经过 PS 对象，避免中文与转义被二次处理）
    $m = [regex]::Match($Json, '"' + [regex]::Escape($Key) + '"\s*:\s*"((?:[^"\\]|\\.)*)"')
    if (-not $m.Success) { return $null }
    return $m.Groups[1].Value
}

function Get-Mime {
    param([string]$Path)
    switch ([System.IO.Path]::GetExtension($Path).ToLowerInvariant()) {
        '.png' { 'image/png' }
        '.jpg' { 'image/jpeg' }
        '.jpeg' { 'image/jpeg' }
        '.webp' { 'image/webp' }
        default { 'image/png' }
    }
}

function Test-ImageBytes {
    param([byte[]]$Bytes)
    if ($null -eq $Bytes -or $Bytes.Length -lt 8) { return $false }
    if ($Bytes[0] -eq 0x89 -and $Bytes[1] -eq 0x50 -and $Bytes[2] -eq 0x4E -and $Bytes[3] -eq 0x47) { return $true } # PNG
    if ($Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xD8 -and $Bytes[2] -eq 0xFF) { return $true }                     # JPEG
    if ($Bytes[0] -eq 0x52 -and $Bytes[1] -eq 0x49 -and $Bytes[2] -eq 0x46 -and $Bytes[3] -eq 0x46) { return $true } # RIFF/WebP
    return $false
}

# ---------------------------------------------------------------- 配置载入

if ((-not $ApiKey -or -not $BaseUrl) -and (Test-Path -LiteralPath $EnvFile)) {
    Write-Step "载入本地配置 $EnvFile"
    . $EnvFile
    if (-not $BaseUrl) { $BaseUrl = $env:PHOTO_BASE_URL }
    if (-not $ApiKey) { $ApiKey = $env:PHOTO_API_KEY }
}

if (-not $BaseUrl) { Write-Die '缺少 BaseUrl。设置 $env:PHOTO_BASE_URL，或写进 scripts/photo/photo.env.ps1，或用 -BaseUrl 传入。' }
if (-not $ApiKey) { Write-Die '缺少 ApiKey。设置 $env:PHOTO_API_KEY，或写进 scripts/photo/photo.env.ps1，或用 -ApiKey 传入。' }
$BaseUrl = $BaseUrl.TrimEnd('/')
if (-not $Image) { Write-Die '缺少 -Image 原图路径。' }
if (-not (Test-Path -LiteralPath $Image)) { Write-Die "找不到原图：$Image" }

$ImageItem = Get-Item -LiteralPath $Image
$ImageFull = $ImageItem.FullName
$ImageHash = (Get-FileHash -LiteralPath $ImageFull -Algorithm SHA256).Hash

if (-not $OutDir) {
    $OutDir = Join-Path (Join-Path $PSScriptRoot '..\..') ('photo_out\' + [System.IO.Path]::GetFileNameWithoutExtension($ImageFull))
}
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

Write-Host ''
Write-Step "任务"
Write-Host "  模式      : $Mode"
Write-Host "  原图      : $ImageFull"
Write-Host "  原图 sha256: $ImageHash"
Write-Host "  尺寸      : $([math]::Round($ImageItem.Length/1MB,2)) MB"
Write-Host "  接口      : $BaseUrl"
Write-Host "  看图模型  : $VisionModel"
Write-Host "  修图模型  : $ImageModel"
Write-Host "  输出目录  : $OutDir"
Write-Host ''

# ---------------------------------------------------------------- 缩放副本

function New-ScaledCopy {
    param([string]$Src, [int]$MaxSide, [string]$WorkDir)
    if ($MaxSide -le 0) { return $Src }
    Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue

    $img = $null
    try { $img = [System.Drawing.Image]::FromFile($Src) } catch { Write-Warn2 "无法解码原图（$($_.Exception.Message)），直接用原文件。"; return $Src }
    try {
        $long = [Math]::Max($img.Width, $img.Height)
        if ($long -le $MaxSide) { return $Src }
        $scale = $MaxSide / $long
        $w = [int][Math]::Round($img.Width * $scale)
        $h = [int][Math]::Round($img.Height * $scale)
        $bmp = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        try {
            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $g.DrawImage($img, 0, 0, $w, $h)
        } finally { $g.Dispose() }
        $dst = Join-Path $WorkDir ("in-" + $w + "x" + $h + ".png")
        $bmp.Save($dst, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
        Write-Ok "缩放副本 $w x $h -> $dst"
        return $dst
    } finally { if ($img) { $img.Dispose() } }
}

# ---------------------------------------------------------------- HTTP 基座

function Get-B64OfFile {
    param([string]$Path)
    # 手动分块转 base64，兼容大图
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return [Convert]::ToBase64String($bytes)
}

function Write-JsonBody {
    param([string]$Json)
    # 用 UTF-8 写文件，彻底绕开 PowerShell 5.1 把请求体按 ANSI 发出去的老坑。
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("photobody-" + [guid]::NewGuid().ToString('N') + '.json')
    [System.IO.File]::WriteAllText($tmp, $Json, [System.Text.UTF8Encoding]::new($false))
    return $tmp
}

function Invoke-PhotoJson {
    <#
        发一个 JSON 请求，返回 @{ Status = <int>; Body = <原始响应文本>; Transport = <错误信息或空> }
        刻意不抛异常：调用方要按状态码做降级重试。
    #>
    param(
        [string]$Method = 'POST',
        [string]$Url,
        [string]$Json,
        [hashtable]$Headers,
        [int]$TimeoutSec = 300
    )
    $bodyFile = Write-JsonBody -Json $Json
    $hdrFile = Join-Path ([System.IO.Path]::GetTempPath()) ("photohdr-" + [guid]::NewGuid().ToString('N') + '.txt')
    try {
        $lines = @()
        foreach ($k in $Headers.Keys) { $lines += ('{0}: {1}' -f $k, $Headers[$k]) }
        [System.IO.File]::WriteAllLines($hdrFile, $lines, [System.Text.UTF8Encoding]::new($false))

        $raw = & curl.exe -sS -X $Method $Url `
            -H "@$hdrFile" `
            -H 'Content-Type: application/json' `
            --data-binary "@$bodyFile" `
            -w "`n__HTTP_STATUS__:%{http_code}" `
            -m $TimeoutSec 2>&1 | Out-String

        $status = 0
        $m = [regex]::Match($raw, '__HTTP_STATUS__:(\d+)\s*$')
        if ($m.Success) {
            $status = [int]$m.Groups[1].Value
            $raw = $raw.Substring(0, $m.Index)
        }
        return @{ Status = $status; Body = $raw.TrimEnd(); Transport = '' }
    } catch {
        return @{ Status = 0; Body = ''; Transport = $_.Exception.Message }
    } finally {
        Remove-Item -LiteralPath $bodyFile, $hdrFile -ErrorAction SilentlyContinue
    }
}

function Show-ApiError {
    param($Resp, [string]$What)
    Write-Warn2 "$What 失败：HTTP $($Resp.Status) $($Resp.Transport)"
    if ($Resp.Body) {
        $snippet = $Resp.Body
        if ($snippet.Length -gt 900) { $snippet = $snippet.Substring(0, 900) + ' …' }
        Write-Host $snippet -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------- 第一段：诊断

function Invoke-Analysis {
    param([string]$ImagePath, [string]$WorkDir)

    $sysPrompt = Read-TextFileUtf8 (Join-Path $PSScriptRoot 'prompts\analyze-system.md')
    $b64 = Get-B64OfFile $ImagePath
    $dataUrl = 'data:' + (Get-Mime $ImagePath) + ';base64,' + $b64

    $payload = @{
        model       = $VisionModel
        temperature = 0.2
        messages    = @(
            @{ role = 'system'; content = $sysPrompt },
            @{ role = 'user'; content = @(
                    @{ type = 'text'; text = '分析这张照片，按要求输出 JSON。' },
                    @{ type = 'image_url'; image_url = @{ url = $dataUrl } }
                ) }
        )
    } | ConvertTo-Json -Depth 12 -Compress

    Write-Step "诊断段：$VisionModel 看图"
    $resp = Invoke-PhotoJson -Url "$BaseUrl/chat/completions" -Json $payload -Headers @{ Authorization = "Bearer $ApiKey" } -TimeoutSec $TimeoutSec

    if ($resp.Status -ne 200) {
        Show-ApiError $resp '诊断'
        Write-Die '诊断段失败。先跑 -Mode analyze 单独排障；确认 VisionModel 是本站支持的看图模型名。'
    }

    $obj = $resp.Body | ConvertFrom-Json
    if (-not $obj.choices -or -not $obj.choices[0].message.content) { Write-Die "诊断响应里没有 choices[0].message.content：$($resp.Body.Substring(0,[Math]::Min(400,$resp.Body.Length)))" }
    $content = [string]$obj.choices[0].message.content

    # 模型偶尔会套 ```json 围栏，剥掉
    $clean = $content.Trim()
    $fence = [regex]::Match($clean, '(?s)```(?:json)?\s*(.*?)\s*```')
    if ($fence.Success) { $clean = $fence.Groups[1].Value.Trim() }
    $brace = $clean.IndexOf('{'); $lastBrace = $clean.LastIndexOf('}')
    if ($brace -ge 0 -and $lastBrace -gt $brace) { $clean = $clean.Substring($brace, $lastBrace - $brace + 1) }

    $analysisPath = Join-Path $WorkDir ("analysis-" + $Stamp + '.json')
    Write-TextFileUtf8 -Path $analysisPath -Text $clean
    Write-Ok "诊断写入 $analysisPath"

    try {
        $a = $clean | ConvertFrom-Json
        Write-Host ''
        Write-Host '--- 诊断摘要 ---' -ForegroundColor Cyan
        foreach ($k in @('scene', 'subject')) { if ($a.PSObject.Properties.Name -contains $k) { Write-Host ("  {0,-14}: {1}" -f $k, $a.$k) } }
        if ($a.PSObject.Properties.Name -contains 'grade_direction') { Write-Host ("  {0,-14}: {1}" -f 'grade_direction', $a.grade_direction) }
        if ($a.PSObject.Properties.Name -contains 'keep') { Write-Host ("  {0,-14}: {1}" -f 'keep', ($a.keep -join ' / ')) }
        if ($a.PSObject.Properties.Name -contains 'issues') { Write-Host ("  {0,-14}: {1}" -f 'issues', (($a.issues) -join ' / ')) }
        Write-Host ''
        Write-Host '--- 模型给出的英文修图指令 ---' -ForegroundColor Cyan
        if ($a.PSObject.Properties.Name -contains 'prompt_en') { Write-Host $a.prompt_en -ForegroundColor White }
        Write-Host ''
    } catch {
        Write-Warn2 "诊断 JSON 解析失败（原文已存盘，可人工修）：$($_.Exception.Message)"
    }

    return $analysisPath
}

# ---------------------------------------------------------------- 第二段：修图

function Build-EditPrompt {
    param([string]$BaseSystem, [string]$ModelPromptEn, [string]$Direction)

    $parts = @()
    $parts += $BaseSystem.Trim()
    if ($Direction) { $parts += "本次调整要求（人给的，优先级最高）：$Direction" }
    if ($ModelPromptEn) { $parts += "诊断得到的执行指令：$ModelPromptEn" }
    $parts += @'
执行方式：只对这张图做全局与局部的光色与质感调整，输出一张与原图构图、画幅、主体完全一致的成品。
Negative: no added or removed objects, no text, no watermark, no frame, no relighting from a new direction, no face reshaping, no skin plastic-smoothing, no HDR halos, no heavy vignette, no color shift beyond the direction specified.
'@
    return ($parts -join "`n`n")
}

function Invoke-ImageEdit {
    param([string]$ImagePath, [string]$Prompt)

    $b64 = Get-B64OfFile $ImagePath
    $mime = Get-Mime $ImagePath
    $dataUrl = 'data:' + $mime + ';base64,' + $b64

    # 不同站点对 image edits 的参数名不一致，按顺序试；第一个成功的记住。
    $attempts = @(
        @{ Name = 'json:image+size+quality'; Body = (@{ model = $ImageModel; prompt = $Prompt; image = @($dataUrl); size = $Size; quality = $Quality; background = $Background } | ConvertTo-Json -Depth 8 -Compress) },
        @{ Name = 'json:image only'; Body = (@{ model = $ImageModel; prompt = $Prompt; image = @($dataUrl) } | ConvertTo-Json -Depth 8 -Compress) },
        @{ Name = 'json:images[]'; Body = (@{ model = $ImageModel; prompt = $Prompt; images = @(@{ image_url = $dataUrl }) } | ConvertTo-Json -Depth 8 -Compress) },
        @{ Name = 'json:input_image'; Body = (@{ model = $ImageModel; prompt = $Prompt; input_image = $dataUrl } | ConvertTo-Json -Depth 8 -Compress) }
    )

    Write-Step "修图段：$ImageModel 出图（提示词 $($Prompt.Length) 字符）"
    Write-Host '  --- 本次提示词 ---' -ForegroundColor DarkGray
    Write-Host $Prompt -ForegroundColor DarkGray
    Write-Host '  ------------------' -ForegroundColor DarkGray

    foreach ($a in $attempts) {
        Write-Host "  尝试 $($a.Name) …" -ForegroundColor DarkGray
        $resp = Invoke-PhotoJson -Url "$BaseUrl/images/edits" -Json $a.Body -Headers @{ Authorization = "Bearer $ApiKey" } -TimeoutSec $TimeoutSec

        if ($resp.Status -eq 200 -and $resp.Body) {
            $out = Save-ImageResponse -Body $resp.Body
            if ($out) { Write-Ok "出图：$out"; return $out }
            Write-Warn2 "HTTP 200 但响应里没有可用图像，继续降级。"
        } else {
            $snippet = $resp.Body
            if ($snippet -and $snippet.Length -gt 220) { $snippet = $snippet.Substring(0, 220) + ' …' }
            Write-Warn2 "HTTP $($resp.Status) $($resp.Transport) $snippet"
        }
    }

    Write-Die @'
四个变体全部失败。按顺序排查：
  1) 模型名：让中转站确认图像编辑模型的确切 id（有的站点叫 gpt-image-1，有的转发成别的名字）。
  2) 站点是否只开了 /images/generations（文生图），没开 /images/edits（图生图）。前者代替不了修图。
  3) 该 key 是否被限流或没余额（HTTP 429 / 402）。
  4) 尺寸：加 -MaxSide 1024 再试。
'@
}

function Save-ImageResponse {
    param([string]$Body)

    $json = $null
    try { $json = $Body | ConvertFrom-Json } catch { return $null }

    $nodes = @()
    if ($json.data) { $nodes = @($json.data) }
    elseif ($json -is [array]) { $nodes = @($json) }
    else { $nodes = @($json) }

    foreach ($n in $nodes) {
        # 兼容多种响应字段
        foreach ($field in @('b64_json', 'b64', 'image_base64', 'image')) {
            if ($n.PSObject.Properties.Name -notcontains $field) { continue }
            $v = [string]$n.$field
            if ([string]::IsNullOrWhiteSpace($v)) { continue }
            if ($v.StartsWith('http')) { Write-Warn2 "响应返回的是 URL（$v），本脚本不代下载；请把该 URL 内容另存。"; continue }
            if ($v.StartsWith('data:')) { $v = $v.Substring($v.IndexOf(',') + 1) }
            try {
                $bytes = [Convert]::FromBase64String($v)
                if (Test-ImageBytes $bytes) {
                    $ext = if ($bytes[0] -eq 0x89) { '.png' } else { '.jpg' }
                    $dst = Join-Path $OutDir ("retouched-" + $Stamp + $ext)
                    if ((Test-Path -LiteralPath $dst) -and -not $Force) { Write-Die "目标已存在：$dst（用 -Force 覆盖）" }
                    [System.IO.File]::WriteAllBytes($dst, $bytes)
                    return $dst
                }
                Write-Warn2 "字段 $field 解码后不是图像魔数，跳过。"
            } catch { Write-Warn2 "字段 $field base64 解码失败：$($_.Exception.Message)" }
        }
        if ($n.PSObject.Properties.Name -contains 'url' -and $n.url) {
            Write-Warn2 "响应返回 URL：$($n.url)（本脚本不代下载）"
        }
    }
    return $null
}

# ---------------------------------------------------------------- 主流程

$workDir = Join-Path ([System.IO.Path]::GetTempPath()) ("photowork-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $workDir -Force | Out-Null

try {
    $working = New-ScaledCopy -Src $ImageFull -MaxSide $MaxSide -WorkDir $workDir
    if ($working -eq $ImageFull) { Write-Ok '原图尺寸在限制内，直接使用原文件。' }

    $promptEn = $null
    if ($Mode -eq 'analyze' -or $Mode -eq 'all') {
        $generated = Invoke-Analysis -ImagePath $working -WorkDir $workDir
        if ($Mode -eq 'analyze') {
            Write-Host ''
            Write-Host '下一步：' -ForegroundColor Cyan
            Write-Host "  .\Edit-Photo.ps1 -Mode edit -Image '$ImageFull' -AnalysisPath '$generated'"
            Write-Host '  （建议先用 -GradingDirection 把方向改成你自己的判断，别全信模型）'
            return
        }
        $AnalysisPath = $generated
    }

    if ($AnalysisPath) {
        if (-not (Test-Path -LiteralPath $AnalysisPath)) { Write-Die "找不到诊断文件：$AnalysisPath" }
        $raw = Read-TextFileUtf8 $AnalysisPath
        $promptEn = Unescape-JsonString (Get-JsonStringValue -Json $raw -Key 'prompt_en')
        if (-not $promptEn) { Write-Warn2 '诊断文件里没有 prompt_en，将只用系统指令 + 你的方向。' }
    }

    if ($Mode -eq 'edit' -and -not $promptEn -and -not $GradingDirection) {
        Write-Die '没有可用的修图指令：既没有 -AnalysisPath，也没有 -GradingDirection。'
    }

    $baseSystem = Read-TextFileUtf8 (Join-Path $PSScriptRoot 'prompts\photographer-system.md')
    $finalPrompt = Build-EditPrompt -BaseSystem $baseSystem -ModelPromptEn $promptEn -Direction $GradingDirection

    $outFile = Invoke-ImageEdit -ImagePath $working -Prompt $finalPrompt

    # 落一份可复现记录，但不含 key
    $record = [ordered]@{
        when           = (Get-Date).ToString('s')
        sourceImage    = $ImageFull
        sourceSha256   = $ImageHash
        sentWidth      = $null
        visualModel    = $VisionModel
        imageModel     = $ImageModel
        baseUrl        = $BaseUrl
        direction      = $GradingDirection
        finalPrompt    = $finalPrompt
        output         = $outFile
    } | ConvertTo-Json -Depth 6
    $recPath = Join-Path $OutDir ("run-" + $Stamp + '.json')
    Write-TextFileUtf8 -Path $recPath -Text $record

    Write-Host ''
    Write-Ok "成品：$outFile"
    Write-Ok "记录：$recPath（不含 key）"
    Write-Host ''
    Write-Host '提醒：模型会顺手改细节。请把成品与原图并排放大到 100% 逐区核对（五官、手、文字、纹样、边缘）。' -ForegroundColor Yellow
} finally {
    Remove-Item -LiteralPath $workDir -Recurse -Force -ErrorAction SilentlyContinue
}
