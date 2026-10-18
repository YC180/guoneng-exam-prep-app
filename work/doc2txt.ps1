# Convert legacy .doc files to UTF-8 .txt using Word COM (one Word instance per file
# is avoided; a single instance is reused but each open is wrapped defensively).
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Out
)

$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force -Path $Out | Out-Null

# Kill any stale Word instances that could hold modal dialogs
Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try { $word.Options.ConfirmConversions = $false } catch {}
try { $word.AutomationSecurity = 3 } catch {}   # msoAutomationSecurityForceDisable
try { $word.Options.SaveInterval = 0 } catch {}

$docs = @(Get-ChildItem -Path $Root -Recurse -File | Where-Object { $_.Extension -eq '.doc' })
Write-Output ("FOUND {0} .doc files" -f $docs.Count)

$n = 0
foreach ($f in $docs) {
  $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
  $dest = Join-Path $Out ([System.IO.Path]::ChangeExtension($rel, '.txt'))
  New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
  $tmp = Join-Path $env:TEMP ("d2t_" + [guid]::NewGuid().ToString("N") + ".txt")
  try {
    $d = $word.Documents.Open($f.FullName, $false, $true, $false)
    $d.SaveAs2($tmp, 2)   # 2 = wdFormatText (ANSI, cp936 on zh-CN)
    $d.Close(0)
  } catch {
    Write-Output ("ERROR-OPEN {0} : {1}" -f $rel, $_.Exception.Message)
    continue
  }
  if (Test-Path $tmp) {
    $bytes = [System.IO.File]::ReadAllBytes($tmp)
    $text = [System.Text.Encoding]::GetEncoding(936).GetString($bytes)
    $text = $text -replace "`r`n", "`n"
    $header = "# SOURCE: $($f.FullName)`n# SIZE_MB: $([math]::Round($f.Length/1MB,2))`n# CONVERTED: Word COM (wdFormatText, cp936 -> UTF-8)`n`n"
    [System.IO.File]::WriteAllText($dest, $header + $text, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output ("OK    {0,8}c  {1}" -f $text.Length, $rel)
    $n++
  } else {
    Write-Output ("ERROR-EMPTY {0}" -f $rel)
  }
  Remove-Item $tmp -ErrorAction SilentlyContinue
}

$word.Quit()
Write-Output ("DONE converted {0} files" -f $n)
