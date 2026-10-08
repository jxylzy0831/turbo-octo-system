$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd([IO.Path]::DirectorySeparatorChar)
$taskTemp=[IO.Path]::GetFullPath((Join-Path $taskRoot '临时存储/pdf_to_docx'))
$taskRootPrefix=$taskRoot+[IO.Path]::DirectorySeparatorChar
$taskTempPrefix=$taskTemp+[IO.Path]::DirectorySeparatorChar
$taskPaths=@(
 'qa/converted_manuals','qa/rendered_manuals',
 'qa/first_page_contact','qa/multimodal_scan_review',
 'qa/qingbai_editable_pairs','qa/qingbai_editable_render',
 'qa/qingbai_editable_render_v2','qa/qingbai_editable_render_v3',
 'qa/qingbai_facsimile_pages','analysis/ocr_jobs',
 'analysis/qingbai_raster_ocr.jsonl','analysis/qingbai_ocr.jsonl',
 'analysis/qingbai_source_path.txt'
)
$taskPlan=@()
foreach($taskRelative in $taskPaths) {
 $taskSource=[IO.Path]::GetFullPath((Join-Path $taskRoot $taskRelative))
 $taskLeaf=Split-Path -Leaf $taskSource
 $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskTemp $taskLeaf))
 if(-not $taskSource.StartsWith($taskRootPrefix,[StringComparison]::OrdinalIgnoreCase) -or
    -not $taskDestination.StartsWith($taskTempPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw '目标路径越界' }
 if(-not(Test-Path -LiteralPath $taskSource)) { continue }
 if(Test-Path -LiteralPath $taskDestination) { throw "目标已存在：$taskDestination" }
 $taskItem=Get-Item -LiteralPath $taskSource -Force
 if($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "不移动链接：$taskSource" }
 if($taskItem.PSIsContainer) {
  $taskChildren=@(Get-ChildItem -LiteralPath $taskSource -Recurse -Force)
  if(@($taskChildren | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count) {throw '目录含链接，停止移动'}
  $taskFiles=@($taskChildren | Where-Object {-not $_.PSIsContainer})
 } else {$taskFiles=@($taskItem)}
 $taskPlan += [pscustomobject]@{Relative=$taskRelative;Source=$taskSource;Destination=$taskDestination;Leaf=$taskLeaf;Count=$taskFiles.Count;Bytes=($taskFiles | Measure-Object Length -Sum).Sum}
}
$taskManifest=Join-Path $taskRoot 'analysis/PDF转换临时存储迁移清单-20261002.md'
if(Test-Path -LiteralPath $taskManifest) {throw '清单已存在，禁止覆盖'}
New-Item -ItemType Directory -Path $taskTemp -Force | Out-Null
@('# PDF 转 DOCX 副产品迁移清单','','2026-10-02。副产品统一移入 Git 忽略的临时存储；原始 PDF、output 中的成品、正式清单与核对结论保留。只移动，未重跑 PDF 转换。','','| 原位置 | 新位置 | 文件数 |','|---|---|---:|') | Set-Content -LiteralPath $taskManifest -Encoding utf8
foreach($taskEntry in $taskPlan) {
 Move-Item -LiteralPath $taskEntry.Source -Destination $taskEntry.Destination
 Add-Content -LiteralPath $taskManifest -Encoding utf8 -Value ('| `'+$taskEntry.Relative+'` | `临时存储/pdf_to_docx/'+$taskEntry.Leaf+'` | '+$taskEntry.Count+' |')
}
# 忽略规则不能取消已经跟踪的文件；若旧路径在索引中，明确取消其跟踪。
$taskExisting=@($taskPlan | ForEach-Object Relative)
$taskTracked=@()
if($taskExisting.Count) {
 $taskTracked=@(& git -C $taskRoot ls-files -- $taskExisting)
 if($LASTEXITCODE -ne 0) {throw 'Git 索引查询失败'}
 if($taskTracked.Count) {
  & git -C $taskRoot rm --cached --ignore-unmatch -r -- $taskExisting
  if($LASTEXITCODE -ne 0) {throw '取消旧副产品的 Git 跟踪失败，文件已移动，请查看清单'}
 }
}
$taskIgnored=@(& git -C $taskRoot check-ignore '临时存储/pdf_to_docx/')
if($LASTEXITCODE -ne 0) {throw '临时目录的 Git 忽略规则未生效'}
$taskCount=($taskPlan | Measure-Object Count -Sum).Sum
$taskMiB=[math]::Round(($taskPlan | Measure-Object Bytes -Sum).Sum/1MB,2)
Add-Content -LiteralPath $taskManifest -Encoding utf8 -Value @('',"共移动 $($taskPlan.Count) 项、$taskCount 个文件，约 $taskMiB MiB。", "迁移前 Git 已跟踪的旧路径条目数为 $($taskTracked.Count)；已处理。Git check-ignore 已确认临时目录被忽略。",'', '转换、OCR、渲染脚本的默认工作路径已同步迁移。带显式输出路径的通用工具按 AGENTS.md 指定临时存储调用，不重跑转换或渲染。')
Write-Output "已移动 $($taskPlan.Count) 项、$taskCount 个文件，约 $taskMiB MiB；旧路径跟踪条目 $($taskTracked.Count)，临时目录已忽略。"
