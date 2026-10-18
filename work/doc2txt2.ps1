# Convert legacy .doc files to UTF-8 .txt using Word COM, one Word instance per file
# with a hard wall-clock timeout, so a single stubborn file cannot stall the batch.
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Out,
  [int]$TimeoutSec = 40
)

$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force -Path $Out | Out-Null

$docs = @(Get-ChildItem -Path $Root -Recurse -File | Where-Object { $_.Extension -eq '.doc' })
Write-Output ("FOUND {0} .doc files" -f $docs.Count)

$ok = 0; $skip = 0; $fail = 0

foreach ($f in $docs) {
  $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
  $dest = Join-Path $Out ([System.IO.Path]::ChangeExtension($rel, '.txt'))
  if (Test-Path $dest) { Write-Output ("SKIP-EXISTS  {0}" -f $rel); $skip++; continue }
  New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null

  # sanity check: OLE2 compound-file signature
  $fs = [System.IO.File]::OpenRead($f.FullName)
  $sig = New-Object byte[] 8
  $null = $fs.Read($sig, 0, 8)
  $fs.Close()
  $hex = ($sig | ForEach-Object { $_.ToString('X2') }) -join ' '
  $isOle = ($hex -eq 'D0 CF 11 E0 A1 B1 1A E1')
  if (-not $isOle) {
    Write-Output ("NOT-OLE      {0}  sig={1}" -f $rel, $hex)
    $fail++
    continue
  }

  $ps = Start-Process -FilePath "powershell.exe" -PassThru -WindowStyle Hidden -ArgumentList @(
    '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-Command',
    "& { `$w = New-Object -ComObject Word.Application; `$w.Visible=`$false; `$w.DisplayAlerts=0; try { `$w.AutomationSecurity = 3 } catch {}; `$w.Options.ConfirmConversions=`$false; `$d = `$w.Documents.Open('$($f.FullName)', `$false, `$true, `$false); `$d.SaveAs2('$env:TEMP\__w1.txt', 2); `$d.Close(0); `$w.Quit() } catch { try { `$w.Quit() } catch {} ; exit 9 }"
  )
  $done = $ps.WaitForExit($TimeoutSec * 1000)
  if (-not $done) {
    try { $ps.Kill() } catch {}
    Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Output ("TIMEOUT      {0}" -f $rel)
    $fail++
    continue
  }
  $tmp = Join-Path $env:TEMP '__w1.txt'
  if ($ps.ExitCode -eq 0 -and (Test-Path $tmp)) {
    $bytes = [System.IO.File]::ReadAllBytes($tmp)
    $text = [System.Text.Encoding]::GetEncoding(936).GetString($bytes)
    $text = $text -replace "`r`n", "`n"
    $header = "# SOURCE: $($f.FullName)`n# SIZE_MB: $([math]::Round($f.Length/1MB,2))`n# CONVERTED: Word COM (wdFormatText, cp936 -> UTF-8)`n`n"
    [System.IO.File]::WriteAllText($dest, $header + $text, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output ("OK {0,8}c  {1}" -f $text.Length, $rel)
    $ok++
  } else {
    Write-Output ("FAIL(exit={0}) {1}" -f $ps.ExitCode, $rel)
    $fail++
  }
  Remove-Item $tmp -ErrorAction SilentlyContinue
}

Write-Output ("DONE ok={0} skip={1} fail={2}" -f $ok, $skip, $fail)
