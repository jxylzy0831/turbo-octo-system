$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd([IO.Path]::DirectorySeparatorChar)
$taskTrashRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot '垃圾箱/20261002_弃用生成物'))
$taskRootPrefix = $taskRoot + [IO.Path]::DirectorySeparatorChar
$taskTrashPrefix = $taskTrashRoot + [IO.Path]::DirectorySeparatorChar

$taskTargets = @(
    @{ Path='质检/ocr_probe'; Reason='一次性 OCR 接口与路径试验' },
    @{ Path='自动化脚本/__pycache__'; Reason='可自动重建的 Python 字节码缓存' },
    @{ Path='分析/ocr_test_png.ps1'; Reason='单页 OCR 接口试验脚本' },
    @{ Path='成品/《青白》组织者手册_逐页图像一比一核对版.docx'; Reason='已被用户否定的整页图片 Word 方案，非可编辑正文版' },
    @{ Path='自动化脚本/create_qingbai_facsimile_docx.py'; Reason='仅生成上述弃用整页图片 Word 的脚本' },
    @{ Path='质检/qingbai_facsimile_render'; Reason='上述弃用图片 Word 的派生渲染' },
    @{ Path='质检/qingbai_page_pairs'; Reason='上述弃用图片 Word 与 PDF 的配对图' },
    @{ Path='分析/青白一比一核对版清单.json'; Reason='上述弃用图片 Word 的清单' },
    @{ Path='分析/青白一比一页面配对差异.json'; Reason='上述弃用图片 Word 的图片差异数据' },
    @{ Path='分析/青白逐页多模态核对记录.md'; Reason='上述弃用图片 Word 的核对记录，不能用来证明正文已可编辑' }
)

# 先验证所有绝对路径和文件类型，再开始移动。保留相对目录结构，不覆盖同名文件。
$taskPlan = @()
foreach ($taskTarget in $taskTargets) {
    $taskSource = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskTarget.Path))
    $taskDestination = [IO.Path]::GetFullPath((Join-Path $taskTrashRoot $taskTarget.Path))
    if (-not $taskSource.StartsWith($taskRootPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not $taskDestination.StartsWith($taskTrashPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "目标越出工作区或垃圾箱范围：$($taskTarget.Path)"
    }
    if ($taskSource.StartsWith((Join-Path $taskRoot '原始资料') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw '禁止移动原始资料'
    }
    if (-not (Test-Path -LiteralPath $taskSource)) { throw "源文件不存在：$($taskTarget.Path)" }
    if (Test-Path -LiteralPath $taskDestination) { throw "目标已存在，停止以防覆盖：$taskDestination" }
    $taskItem = Get-Item -LiteralPath $taskSource -Force
    if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "不处理链接目录：$taskSource" }
    $taskFiles = @(if ($taskItem.PSIsContainer) { Get-ChildItem -LiteralPath $taskSource -Recurse -File -Force } else { $taskItem })
    if ($taskItem.PSIsContainer) {
        $taskLinks = @(Get-ChildItem -LiteralPath $taskSource -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($taskLinks.Count) { throw "目录含链接，停止：$taskSource" }
    }
    $taskPlan += [pscustomobject]@{ Source=$taskSource; Destination=$taskDestination; Relative=$taskTarget.Path; Reason=$taskTarget.Reason; Count=$taskFiles.Count; Bytes=($taskFiles | Measure-Object Length -Sum).Sum }
}

$taskManifest = Join-Path $taskRoot '分析/垃圾箱整理清单-20261002.md'
if (Test-Path -LiteralPath $taskManifest) { throw '整理清单已存在，禁止覆盖' }
$taskText = @(
    '# 垃圾箱整理清单', '',
    '2026-10-02。按用户要求，根目录垃圾箱保存弃用文件，不再作为参考。只移动，不删除。原始资料、可编辑 Word、当前互动稿与依赖脚本均保留。', '',
    '| 原路径 | 移入位置 | 文件数 | 原因 |',
    '|---|---|---:|---|'
)
$taskText | Set-Content -LiteralPath $taskManifest -Encoding utf8
$taskMoved = 0
foreach ($taskEntry in $taskPlan) {
    $taskParent = Split-Path -Parent $taskEntry.Destination
    New-Item -ItemType Directory -Path $taskParent -Force | Out-Null
    Move-Item -LiteralPath $taskEntry.Source -Destination $taskEntry.Destination
    $taskRow = '| `' + $taskEntry.Relative + '` | `垃圾箱/20261002_弃用生成物/' + $taskEntry.Relative + '` | ' + $taskEntry.Count + ' | ' + $taskEntry.Reason + ' |'
    Add-Content -LiteralPath $taskManifest -Value $taskRow -Encoding utf8
    $taskMoved += $taskEntry.Count
}
$taskMB = [math]::Round(($taskPlan | Measure-Object Bytes -Sum).Sum / 1MB, 2)
Add-Content -LiteralPath $taskManifest -Encoding utf8 -Value @('', "共移动 $($taskPlan.Count) 项、$taskMoved 个文件，约 $taskMB MiB。移动不释放磁盘空间。", '', 'AGENTS.md 已明确排除垃圾箱；.gitignore 已忽略该目录。仅在用户明确要求找回时使用原路径清单恢复指定文件。')
Write-Output "已移动 $($taskPlan.Count) 项、$taskMoved 个文件，约 $taskMB MiB。"
