param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskRootPrefix = $taskRoot.TrimEnd('\') + '\'
$taskTrashRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot '垃圾箱/20261009_全部旧写作稿弃用'))
$taskTrashPrefix = $taskTrashRoot.TrimEnd('\') + '\'
$taskManifest = Join-Path $taskRoot '分析/垃圾箱整理清单-20261009.md'
$taskMetadata = Join-Path $taskRoot '分析/垃圾箱整理清单-20261009.json'

function Assert-TaskPath([string]$Path, [string]$Prefix) {
    $taskFullPath = [IO.Path]::GetFullPath($Path)
    if (-not $taskFullPath.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "路径超出授权范围：$taskFullPath"
    }
    $taskAncestor = $taskFullPath
    while ($taskAncestor -and $taskAncestor.StartsWith($taskRootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path -LiteralPath $taskAncestor) {
            if ((Get-Item -LiteralPath $taskAncestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "路径包含链接或重解析点，停止移动：$taskAncestor"
            }
        }
        $taskAncestor = Split-Path -Parent $taskAncestor
    }
}

$taskCreativeAnalysis = @(
    'ABC信息释放方案-v2.md', 'v2重写硬约束.md', '原创补缀登记-v3.md',
    '现代新本-十一人功能表-v1.md', '末世情感本-全流程任务清单.html',
    '阿奇七幕方案.md', '阿奇ABC逻辑审计-2026-08-03.md',
    '阿奇A本-v2.jsonl', '阿奇A本-v2-校订版.jsonl', '黛利拉改版影响表.md',
    '末日学校第一幕公共戏v3评估-20260928.md', '北境停火题材-AgentA马斯克审视-v1.md'
)
$taskQaDirs = @('final', 'final-v3', 'final-v4', 'prompt_word_v1')
$taskFiles = & rg --files --hidden --no-ignore drafts output analysis qa -g '!垃圾箱/**' -g '!垃圾桶/**' -g '!临时存储/**' -g '!.gitkeep' -g '!分析/会话记录/**' -g '!质检/skill-validation-deps/**'
if ($LASTEXITCODE -ne 0) { throw '文件枚举失败。' }
$taskPlan = @(
    foreach ($taskFile in $taskFiles) {
        $taskRelative = $taskFile.Replace('\', '/')
        $taskParts = $taskRelative.Split('/')
        $taskReason = $null
        if ($taskParts[0] -eq 'drafts') {
            $taskReason = '用户确认弃用所有已有写作稿、当前稿、大纲、人物设定和母提示词'
        } elseif ($taskParts[0] -eq 'output' -and ($taskParts[-1] -like '阿奇*.docx' -or $taskParts[-1] -eq '黛利拉与程聿怀人物关系梳理.html')) {
            $taskReason = '旧写作成品与旧人物关系稿，含原定稿和合订本'
        } elseif ($taskParts[0] -eq 'analysis') {
            if ($taskParts[1] -eq '末日学校' -or $taskParts[1] -eq 'reviews' -or
                ($taskParts.Length -eq 2 -and ($taskCreativeAnalysis -contains $taskParts[-1] -or
                $taskParts[-1] -like 'AgentA-*' -or $taskParts[-1] -like 'AgentB-*' -or $taskParts[-1] -like '末日学校-*'))) {
                $taskReason = '弃用写作稿配套的创作方案、设计说明、评审与派生抽取'
            }
        } elseif ($taskParts[0] -eq 'qa') {
            if ($taskQaDirs -contains $taskParts[1] -or $taskParts[1] -like '末日学校-*' -or
                ($taskParts.Length -eq 2 -and ($taskParts[-1] -like '黛利拉与程聿怀人物关系梳理-*.png' -or
                $taskParts[-1] -eq '文本与版式质检报告-v3.md'))) {
                $taskReason = '旧写作稿的页面渲染、预览与质检副产品'
            }
        }
        if (-not $taskReason) { continue }
        $taskSource = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskRelative))
        $taskDestination = [IO.Path]::GetFullPath((Join-Path $taskTrashRoot $taskRelative))
        Assert-TaskPath $taskSource $taskRootPrefix
        Assert-TaskPath $taskDestination $taskTrashPrefix
        if (Test-Path -LiteralPath $taskDestination) { throw "目标已存在，禁止覆盖：$taskDestination" }
        $taskItem = Get-Item -LiteralPath $taskSource -Force
        [PSCustomObject]@{
            Original = $taskRelative
            Destination = '垃圾箱/20261009_全部旧写作稿弃用/' + $taskRelative
            Bytes = $taskItem.Length
            SHA256 = (Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
            Reason = $taskReason
            Status = 'planned'
        }
    }
)
if (-not $Apply) {
    $taskPlan | Group-Object { $_.Original.Split('/')[0] } | Select-Object Name, Count
    Write-Output "计划移动 $($taskPlan.Count) 个文件；添加 -Apply 才执行。"
    return
}
if (-not $taskPlan.Count) { throw '没有找到待整理文件，不覆盖既有整理清单。' }
if ((Test-Path -LiteralPath $taskManifest) -or (Test-Path -LiteralPath $taskMetadata)) { throw '整理清单已存在，请先核对上次执行状态。' }

function Save-TaskMetadata {
    $taskPlan | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $taskMetadata -Encoding utf8
}
Save-TaskMetadata
$taskMoved = 0
try {
    foreach ($taskEntry in $taskPlan) {
        $taskSource = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.Original))
        $taskDestination = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.Destination))
        Assert-TaskPath $taskSource $taskRootPrefix
        Assert-TaskPath $taskDestination $taskTrashPrefix
        if (Test-Path -LiteralPath $taskDestination) { throw "目标已存在：$taskDestination" }
        New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
        Move-Item -LiteralPath $taskSource -Destination $taskDestination
        if ((Test-Path -LiteralPath $taskSource) -or
            (Get-Item -LiteralPath $taskDestination -Force).Length -ne $taskEntry.Bytes) {
            throw "移动后的路径或文件大小核对失败：$($taskEntry.Original)"
        }
        $taskEntry.Status = 'moved'
        $taskMoved++
    }
} finally {
    Save-TaskMetadata
    $taskLines = @(
        '# 全部旧写作稿弃用整理清单', '',
        '日期：2026-10-09。用户明确选择“所有已有写作稿和母提示词都移入垃圾桶”。沿用根目录垃圾箱，只移动，不删除，不覆盖同名文件。', '',
        '垃圾箱中的旧稿、母提示词和相关副产品没有参考价值，默认不读取、不检索、不带入上下文。本清单仅用于文件操作追踪与指定恢复，不是设定或写作参考。', '',
        '保留 scripts、StageFlow、两套互动设计工具、工具依赖与配置、原始资料、原始资料抽取及索引、参考手册转换成品、通用评分标准、会话记录和 PDF 转换临时文件。工具源码和演示数据中的旧案例只用于工具维护。', '',
        "共计划移动 $($taskPlan.Count) 个文件，实际完成 $taskMoved 个。SHA-256 为移动前取得，详见同名 JSON 清单。", '',
        '| 原路径 | 移入位置 | 原因 | 状态 |', '|---|---|---|---|'
    )
    foreach ($taskEntry in $taskPlan) {
        $taskLines += '| ' + $taskEntry.Original + ' | ' + $taskEntry.Destination + ' | ' + $taskEntry.Reason + ' | ' + $taskEntry.Status + ' |'
    }
    $taskLines | Set-Content -LiteralPath $taskManifest -Encoding utf8
}
Write-Output "已移动 $taskMoved 个文件，整理清单：分析/垃圾箱整理清单-20261009.md"
