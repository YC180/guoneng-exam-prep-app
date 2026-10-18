# Re-convert the .doc files whose .txt lacks a CONVERTED header, using Word COM
# with a per-file timeout.
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Out,
  [int]$TimeoutSec = 45
)
$ErrorActionPreference = 'Continue'
Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400

$docs = @(Get-ChildItem -Path $Root -Recurse -File | Where-Object { $_.Extension -eq '.doc' })
$todo = @()
foreach ($f in $docs) {
  $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
  $dest = Join-Path $Out ([System.IO.Path]::ChangeExtension($rel, '.txt'))
  $need = $true
  if (Test-Path $dest) {
    $head = Get-Content -LiteralPath $dest -TotalCount 5 -Encoding UTF8 -ErrorAction SilentlyContinue
    if (($head -join "`n") -match 'CONVERTED') { $need = $false }
  }
  if ($need) { $todo += ,@($f, $rel, $dest) }
}
Write-Output ("TODO {0} files" -f $todo.Count)

$ok = 0; $fail = 0
foreach ($item in $todo) {
  $f = $item[0]; $rel = $item[1]; $dest = $item[2]
  New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
  $tmp = Join-Path $env:TEMP '__w2.txt'
  Remove-Item $tmp -ErrorAction SilentlyContinue
  $cmd = "& { `$w=New-Object -ComObject Word.Application; `$w.Visible=`$false; `$w.DisplayAlerts=0; try{`$w.AutomationSecurity=3}catch{}; `$w.Options.ConfirmConversions=`$false; `$d=`$w.Documents.Open('$($f.FullName)',`$false,`$true,`$false); `$d.SaveAs2('$tmp',2); `$d.Close(0); `$w.Quit() } catch { try{`$w.Quit()}catch{}; exit 9 }"
  $ps = Start-Process -FilePath "powershell.exe" -PassThru -WindowStyle Hidden -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-Command',$cmd)
  $done = $ps.WaitForExit($TimeoutSec * 1000)
  if (-not $done) {
    try { $ps.Kill() } catch {}
    Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Output ("TIMEOUT {0}" -f $rel); $fail++; continue
  }
  if ($ps.ExitCode -eq 0 -and (Test-Path $tmp)) {
    $bytes = [System.IO.File]::ReadAllBytes($tmp)
    $text = [System.Text.Encoding]::GetEncoding(936).GetString($bytes) -replace "`r`n", "`n"
    $header = "# SOURCE: $($f.FullName)`n# SIZE_MB: $([math]::Round($f.Length/1MB,2))`n# CONVERTED: Word COM (wdFormatText, cp936 -> UTF-8)`n`n"
    [System.IO.File]::WriteAllText($dest, $header + $text, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output ("OK {0,8}c  {1}" -f $text.Length, $rel); $ok++
  } else {
    Write-Output ("FAIL(exit={0}) {1}" -f $ps.ExitCode, $rel); $fail++
  }
}
Write-Output ("DONE ok={0} fail={1}" -f $ok, $fail)
