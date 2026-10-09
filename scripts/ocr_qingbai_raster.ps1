param([string]$PagesDirectory=(Join-Path $PSScriptRoot '../临时存储/pdf_to_docx/qingbai_facsimile_pages'),[string]$OutputFile=(Join-Path $PSScriptRoot '../临时存储/pdf_to_docx/qingbai_raster_ocr.jsonl'),[int]$StartPage=2,[int]$EndPage=183)
$ErrorActionPreference='Stop'
$OutputFile=[IO.Path]::GetFullPath($OutputFile)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($OutputFile)) | Out-Null
[void][Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime')
$methods=[System.WindowsRuntimeSystemExtensions].GetMethods()
$generic=$methods | Where-Object {try {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1} catch {$false}} | Select-Object -First 1
$nongeneric=$methods | Where-Object {try {$_.Name -eq 'AsTask' -and !$_.IsGenericMethod -and $_.GetParameters().Count -eq 1} catch {$false}} | Select-Object -First 1
function Wait-Result($operation,[Type]$resultType){$task=$generic.MakeGenericMethod($resultType).Invoke($null,@($operation));$task.GetAwaiter().GetResult()}
$lang=[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]::new('zh-Hans-CN')
$engine=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]::TryCreateFromLanguage($lang)
if($null -eq $engine){throw 'Simplified Chinese OCR recognizer unavailable.'}
$fileType=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$decoderType=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$softwareBitmapType=[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$resultType=[Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
$randomStreamType=[Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$accessModeType=[Windows.Storage.FileAccessMode,Windows.Storage,ContentType=WindowsRuntime]
$writer=[IO.StreamWriter]::new($OutputFile,$false,[Text.UTF8Encoding]::new($false))
try {
 for($number=$StartPage;$number -le $EndPage;$number++) {
  $bitmap=$null;$stream=$null
  try {
   $imagePath=(Resolve-Path -LiteralPath (Join-Path $PagesDirectory ('source-{0:D3}.png' -f $number))).Path
   $storageFile=Wait-Result ($fileType::GetFileFromPathAsync($imagePath)) $fileType
   $stream=Wait-Result ($storageFile.OpenAsync($accessModeType::Read)) $randomStreamType
   $decoder=Wait-Result ($decoderType::CreateAsync($stream)) $decoderType
   $bitmap=Wait-Result ($decoder.GetSoftwareBitmapAsync()) $softwareBitmapType
   $result=Wait-Result ($engine.RecognizeAsync($bitmap)) $resultType
   $lines=@(foreach($line in $result.Lines){[string]$line.Text})
   $record=@{page=$number;lines=$lines;error=$null}
  } catch {$record=@{page=$number;lines=@();error=$_.Exception.Message}}
  $writer.WriteLine((ConvertTo-Json -InputObject $record -Depth 5 -Compress))
  if(($number % 20) -eq 0){$writer.Flush();Write-Output "OCR $number / $EndPage"}
  if($bitmap){$null=$bitmap.Dispose()};if($stream){$null=$stream.Dispose()}
 }
} finally {$writer.Dispose()}
