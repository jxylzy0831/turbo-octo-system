param([switch]$执行)

$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$taskBatch = '20261029-清理旧稿-第1批'
$taskArchive = [System.IO.Path]::GetFullPath((Join-Path $taskRoot "垃圾箱/$taskBatch"))
$taskReport = Join-Path $taskRoot '分析/旧稿整理-20261029'
$taskPlanPath = Join-Path $taskReport '整理清单.json'
$taskRootPrefix = $taskRoot.TrimEnd('\') + '\'
$taskItems = [System.Collections.Generic.List[object]]::new()

function Assert-WorkspacePath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($taskRootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "目标不在项目内，停止操作：$full"
    }
    return $full
}

function Get-RelativePath([string]$Path) {
    return [System.IO.Path]::GetRelativePath($taskRoot, $Path).Replace('\', '/')
}

function Add-ArchiveItem([System.IO.FileSystemInfo]$Item, [string]$Reason) {
    $source = Assert-WorkspacePath ((Resolve-Path -LiteralPath $Item.FullName).Path)
    $relative = Get-RelativePath $source
    if ($relative -notmatch '^(草稿|成品|分析|质检|drafts)/' -and $relative -ne 'drafts') {
        throw "来源不在允许整理的区域：$relative"
    }
    if (($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "不移动链接或重解析目录：$relative"
    }
    $files = if ($Item.PSIsContainer) {
        @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
    } else { @($Item) }
    $inventory = @($files | ForEach-Object {
        [ordered]@{
            原路径 = Get-RelativePath $_.FullName
            字节数 = $_.Length
            SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    })
    $taskItems.Add([ordered]@{
        原路径 = $relative
        归档路径 = "垃圾箱/$taskBatch/$relative"
        原因 = $Reason
        文件数 = $files.Count
        字节数 = [long](($files | Measure-Object -Property Length -Sum).Sum)
        文件校验 = $inventory
    })
}

Assert-WorkspacePath $taskArchive | Out-Null
if (Test-Path -LiteralPath $taskArchive) {
    throw '本批次垃圾箱已存在，避免混入或覆盖，请另建批次。'
}
$taskTrashParent = Join-Path $taskRoot '垃圾箱'
if ((Get-Item -LiteralPath $taskTrashParent -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
    throw '垃圾箱是重解析目录，停止移动。'
}

$draftKeep = @('.gitkeep', '春日恋综版四位玩家个人本-20261028-第1版', '故事泳道图_单屏模板_01')
Get-ChildItem -LiteralPath (Join-Path $taskRoot '草稿') -Force |
    Where-Object { $_.Name -notin $draftKeep } |
    ForEach-Object { Add-ArchiveItem $_ '已被当前恋综四人合稿替代的旧校园稿、单人版本及其附稿' }

Get-ChildItem -LiteralPath (Join-Path $taskRoot '成品') -Force |
    Where-Object { $_.Name -ne '.gitkeep' } |
    ForEach-Object { Add-ArchiveItem $_ '旧校园版导出成品，不属于当前恋综稿' }

$analysisKeep = @(
    '.gitkeep', '会话记录', '流氓叙事文本研究', '流氓叙事创作逆向', '旧稿整理-20261029',
    '恋综版四玩家合稿-20261028-共用设定.md',
    '春日恋综版四玩家本-20261028-文本与现场衔接.md',
    '剧本杀严格评分与验证规范-20260920-第1版.md',
    '剧本杀评审工作表-20260920-第1版.md',
    '互动技能通用化整理-20261002-第2版.md',
    '互动技能旧版保留清单-20261002.json',
    '互动网页呈现约定-20260930.md'
)
Get-ChildItem -LiteralPath (Join-Path $taskRoot '分析') -Force |
    Where-Object { $_.Name -notin $analysisKeep } |
    ForEach-Object { Add-ArchiveItem $_ '旧方案的需求、设定、争议、评审或历史整理记录，已退出当前创作依据' }

Get-ChildItem -LiteralPath (Join-Path $taskRoot '分析/会话记录') -Force |
    ForEach-Object { Add-ArchiveItem $_ '历史会话含已撤销与中间设定，保留到垃圾箱供指定找回' }

Get-ChildItem -LiteralPath (Join-Path $taskRoot '分析/流氓叙事文本研究') -Force |
    Where-Object { $_.Name -notin @('提取文本', '资料索引.json') } |
    ForEach-Object { Add-ArchiveItem $_ '旧技能版本或旧校园试稿对照；现行技能、原文抽取与来源索引保留' }

$qaKeep = @(
    '.gitkeep', '春日恋综版四玩家本-20261028-第1版',
    '流氓叙事技能验证', '命名统一依赖', 'skill-validation-deps',
    '封面参考', '排版模板', '故事泳道图_单屏模板_01',
    '第一幕人物分色-20260930-第一版',
    '源文件校验值复核-2026-08-08.md',
    '项目写作技能安装核对-20261013.json',
    '情感本创作设计技能-20261012第1版.md',
    '流氓叙事创作逆向-20261012第1轮-核对记录.md',
    '互动技能-第2版-结构检查-20261002.json',
    '互动技能-源文件核对-20260915.json',
    '互动技能验证-20260915.md',
    '第一幕互动原文导出核验-20260930-第1版.json',
    '第一幕人物分色标注-20260930-第1版.json',
    '提取视频帧.js'
)
Get-ChildItem -LiteralPath (Join-Path $taskRoot '质检') -Force |
    Where-Object { $_.Name -notin $qaKeep } |
    ForEach-Object { Add-ArchiveItem $_ '旧创作稿对应的排版、渲染、临时图片或质检结果' }

$legacyDrafts = Join-Path $taskRoot 'drafts'
if (Test-Path -LiteralPath $legacyDrafts) {
    Add-ArchiveItem (Get-Item -LiteralPath $legacyDrafts) '英文旧稿目录中的弃用学校大纲'
}

$protectedFiles = @(
    '草稿/春日恋综版四位玩家个人本-20261028-第1版',
    '分析/恋综版四玩家合稿-20261028-共用设定.md',
    '分析/春日恋综版四玩家本-20261028-文本与现场衔接.md',
    '分析/流氓叙事文本研究/提取文本',
    '分析/流氓叙事文本研究/资料索引.json',
    '分析/流氓叙事创作逆向',
    '质检/春日恋综版四玩家本-20261028-第1版',
    '原始资料', '.agents', '互动设计技能', '互动设计技能第二版',
    '自动化脚本', '素材', '草稿/故事泳道图_单屏模板_01'
)
$protectedHashes = [System.Collections.Generic.List[object]]::new()
foreach ($relative in $protectedFiles) {
    $path = Join-Path $taskRoot $relative
    $item = Get-Item -LiteralPath $path -Force
    $files = if ($item.PSIsContainer) {
        @(Get-ChildItem -LiteralPath $path -File -Recurse -Force |
            Where-Object { $_.FullName -notmatch '[\\/](?:__pycache__|node_modules|文档渲染依赖)[\\/]' })
    } else { @($item) }
    foreach ($file in $files) {
        $protectedHashes.Add([ordered]@{
            路径 = Get-RelativePath $file.FullName
            SHA256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        })
    }
}

$taskFileTotal = 0
$taskByteTotal = 0L
foreach ($entry in $taskItems) {
    $taskFileTotal += $entry.文件数
    $taskByteTotal += $entry.字节数
}
$taskPlan = [ordered]@{
    日期 = '2026-10-29'
    项目根目录 = $taskRoot
    状态 = '已核对待移动'
    垃圾箱批次 = "垃圾箱/$taskBatch"
    移动项目数 = $taskItems.Count
    移动文件数 = $taskFileTotal
    总字节数 = $taskByteTotal
    保留文件校验 = $protectedHashes.ToArray()
    说明 = '只移动，不删除。舞台预演整体、全部技能与自动化脚本、原始资料和工具依赖原位保留。'
    移动项目 = $taskItems.ToArray()
}
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
$taskPlan | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskPlanPath -Encoding utf8

if (-not $执行) {
    [ordered]@{
        状态 = '预览完成，尚未移动'
        移动项目数 = $taskPlan.移动项目数
        移动文件数 = $taskPlan.移动文件数
        约MB = [math]::Round($taskPlan.总字节数 / 1MB, 2)
        清单 = Get-RelativePath $taskPlanPath
        分组 = @($taskItems | Group-Object { ($_.原路径 -split '/')[0] } |
            ForEach-Object { [ordered]@{ 区域 = $_.Name; 移动项目数 = $_.Count } })
    } | ConvertTo-Json -Depth 5
    exit 0
}

# 完整验证本批全部来源与目标之后才执行第一项移动。
foreach ($entry in $taskItems) {
    $source = Assert-WorkspacePath (Join-Path $taskRoot $entry.原路径)
    $destination = Assert-WorkspacePath (Join-Path $taskRoot $entry.归档路径)
    if (-not $destination.StartsWith($taskArchive + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "目标越过本批垃圾箱：$destination"
    }
    if (-not (Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $destination)) {
        throw "来源缺失或目标已存在：$($entry.原路径)"
    }
}
New-Item -ItemType Directory -Path $taskArchive | Out-Null
foreach ($entry in $taskItems) {
    $source = Assert-WorkspacePath (Join-Path $taskRoot $entry.原路径)
    $destination = Assert-WorkspacePath (Join-Path $taskRoot $entry.归档路径)
    $parent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Move-Item -LiteralPath $source -Destination $destination
}

foreach ($entry in $taskItems) {
    if (Test-Path -LiteralPath (Join-Path $taskRoot $entry.原路径)) {
        throw "来源仍有残留：$($entry.原路径)"
    }
    foreach ($file in $entry.文件校验) {
        $destination = Assert-WorkspacePath (Join-Path $taskArchive $file.原路径)
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $file.SHA256) {
            throw "归档文件校验不符：$($file.原路径)"
        }
    }
}
foreach ($file in $protectedHashes) {
    $path = Assert-WorkspacePath (Join-Path $taskRoot $file.路径)
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $file.SHA256) {
        throw "保留文件发生变化：$($file.路径)"
    }
}

$taskPlan.状态 = '已移动并通过完整性校验'
$taskPlan['归档核验'] = '全部已移动文件SHA256一致，保留文件SHA256一致'
$taskPlan | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskPlanPath -Encoding utf8
[ordered]@{
    状态 = $taskPlan.状态
    移动项目数 = $taskPlan.移动项目数
    移动文件数 = $taskPlan.移动文件数
    约MB = [math]::Round($taskPlan.总字节数 / 1MB, 2)
    垃圾箱批次 = $taskPlan.垃圾箱批次
    保留文件校验数 = $protectedHashes.Count
} | ConvertTo-Json
