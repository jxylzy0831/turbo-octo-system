param([Parameter(Mandatory=$true)][string]$PathFile,[string]$OutputFile,[int]$StartPage=1,[int]$EndPage=0)
$ErrorActionPreference='Stop'
if (-not $OutputFile) {
 $taskSource=[IO.File]::ReadAllText((Resolve-Path -LiteralPath $PathFile).Path,[Text.Encoding]::UTF8).Trim()
 $taskStem=[IO.Path]::GetFileNameWithoutExtension($taskSource)
 $OutputFile=Join-Path $PSScriptRoot ("../临时存储/pdf_to_docx/"+$taskStem+'/ocr.jsonl')
}
$OutputFile=[IO.Path]::GetFullPath($OutputFile)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($OutputFile)) | Out-Null
[void][Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime')
$allMethods=[System.WindowsRuntimeSystemExtensions].GetMethods()
$genericAsTask=$allMethods | Where-Object {try {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1} catch {$false}} | Select-Object -First 1
$actionAsTask=$allMethods | Where-Object {try {$_.Name -eq 'AsTask' -and !$_.IsGenericMethod -and $_.GetParameters().Count -eq 1} catch {$false}} | Select-Object -First 1
function Wait-Operation($Operation,[Type]$ResultType){$m=$genericAsTask.MakeGenericMethod($ResultType);$task=$m.Invoke($null,@($Operation));return $task.GetAwaiter().GetResult()}
function Wait-Action($Operation){$task=$actionAsTask.Invoke($null,@($Operation));$task.GetAwaiter().GetResult();return $null}
$sourcePath=[IO.File]::ReadAllText($PathFile,[Text.Encoding]::UTF8).Trim()
$fileType=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$pdfType=[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$storageFile=Wait-Operation ($fileType::GetFileFromPathAsync($sourcePath)) $fileType
$pdf=Wait-Operation ($pdfType::LoadFromFileAsync($storageFile)) $pdfType
if($EndPage -le 0 -or $EndPage -gt $pdf.PageCount){$EndPage=[int]$pdf.PageCount}
$lang=[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]::new('zh-Hans-CN')
$engine=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]::TryCreateFromLanguage($lang)
if($null -eq $engine){throw 'Simplified Chinese OCR recognizer unavailable.'}
$utf8NoBom=New-Object System.Text.UTF8Encoding($false)
$writer=New-Object IO.StreamWriter($OutputFile,$false,$utf8NoBom)
try {
 for($number=$StartPage;$number -le $EndPage;$number++) {
  $page=$null;$stream=$null
  try {
   $page=$pdf.GetPage([uint32]($number-1))
   $stream=[Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]::new()
   $null=Wait-Action ($page.RenderToStreamAsync($stream))
   $stream.Seek(0)
   $decoderType=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
   $decoder=Wait-Operation ($decoderType::CreateAsync($stream)) $decoderType
   $bitmapType=[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
   $bitmap=Wait-Operation ($decoder.GetSoftwareBitmapAsync()) $bitmapType
   $resultType=[Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
   $result=Wait-Operation ($engine.RecognizeAsync($bitmap)) $resultType
   $lines=@(); foreach($line in $result.Lines){$rect=$line.BoundingRect;$text=($line.Words|ForEach-Object Text)-join ''; $lines+=@{text=$text;x=[double]$rect.X;y=[double]$rect.Y;width=[double]$rect.Width;height=[double]$rect.Height}}
   $record=@{page=$number;width=[double]$page.Size.Width;height=[double]$page.Size.Height;bitmapWidth=[int]$bitmap.PixelWidth;bitmapHeight=[int]$bitmap.PixelHeight;lines=$lines;error=$null}
  } catch { $record=@{page=$number;error=$_.Exception.Message;lines=@()} }
  $writer.WriteLine((ConvertTo-Json -InputObject $record -Depth 6 -Compress))
  if(($number % 20) -eq 0){$writer.Flush();Write-Output "OCR $number / $EndPage"}
  if($page){$null=$page.Dispose()};if($stream){$null=$stream.Dispose()};if($bitmap){$null=$bitmap.Dispose()}
 }
} finally {$writer.Dispose();}


