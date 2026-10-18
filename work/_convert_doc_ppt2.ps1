# Convert interview folders 1、高分表达模板 and 2、高分面试穿搭 sources to UTF-8 .txt.
# .doc  -> Word COM, text read from Document.Content (direct SaveAs2 hangs in this
#          environment), paragraphs split on CR.
# .ppt  -> PowerPoint COM, text frames + tables + notes per slide.
$ErrorActionPreference = 'Continue'

$src = 'D:\DOWNLOADS\26国家能源集团通关资料\11、面试学习资料包'
$out = 'D:\app project\work\text4\面试'
$utf8 = New-Object System.Text.UTF8Encoding($false)

Get-Process WINWORD,POWERPNT -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 700

$subs = @('1、高分表达模板','2、高分面试穿搭')

function Save-Text($path, $header, $body) {
  New-Item -ItemType Directory -Force -Path (Split-Path $path -Parent) | Out-Null
  [System.IO.File]::WriteAllText($path, $header + $body, $utf8)
}

# ---------------- .doc ----------------
$docs = @()
foreach ($s in $subs) { $docs += @(Get-ChildItem -LiteralPath (Join-Path $src $s) -File -Filter *.doc) }
Write-Output ("WORD FOUND {0} .doc files" -f $docs.Count)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try { $word.Options.ConfirmConversions = $false } catch {}
try { $word.AutomationSecurity = 3 } catch {}

foreach ($f in $docs) {
  $rel = $f.FullName.Substring($src.Length).TrimStart('\')
  $dest = Join-Path $out ([System.IO.Path]::ChangeExtension($rel, '.txt'))
  try {
    $d = $word.Documents.Open($f.FullName, $false, $true, $false)
    $raw = $d.Content.Text
    $d.Close(0)
  } catch {
    Write-Output ("ERROR-DOC {0} : {1}" -f $rel, $_.Exception.Message)
    continue
  }
  $body = ($raw -replace "`r`n", "`n") -replace "`r", "`n"
  $header = "# SOURCE: $($f.FullName)`n# SIZE_MB: $([math]::Round($f.Length/1MB,2))`n# CONVERTED: Word COM (Document.Content.Text -> UTF-8)`n`n"
  Save-Text $dest $header $body
  Write-Output ("OK-DOC {0,8}c  {1}" -f $raw.Length, $rel)
}
$word.Quit()
Start-Sleep -Milliseconds 500

# ---------------- .ppt ----------------
$pptFiles = @()
foreach ($s in $subs) { $pptFiles += @(Get-ChildItem -LiteralPath (Join-Path $src $s) -File -Filter *.ppt) }
Write-Output ("PPT FOUND {0} .ppt files" -f $pptFiles.Count)

$ppt = New-Object -ComObject PowerPoint.Application
foreach ($f in $pptFiles) {
  $rel = $f.FullName.Substring($src.Length).TrimStart('\')
  $dest = Join-Path $out ([System.IO.Path]::ChangeExtension($rel, '.txt'))
  $lines = New-Object System.Collections.Generic.List[string]
  $slideCount = 0
  try {
    $pres = $ppt.Presentations.Open($f.FullName, $true, $false, $false)
    $slideCount = $pres.Slides.Count
    $lines.Add("=== SLIDE COUNT: $slideCount ===")
    foreach ($slide in $pres.Slides) {
      $lines.Add("")
      $lines.Add("--- SLIDE $($slide.SlideIndex) ---")
      foreach ($shape in $slide.Shapes) {
        try {
          if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
            $t = $shape.TextFrame.TextRange.Text
            if ($t) { foreach ($ln in ($t -split "`r")) { $lines.Add($ln.TrimEnd()) } }
          }
        } catch {}
        try {
          if ($shape.HasTable -eq -1) {
            $tb = $shape.Table
            for ($r = 1; $r -le $tb.Rows.Count; $r++) {
              $cells = @()
              for ($c = 1; $c -le $tb.Columns.Count; $c++) {
                $cells += ($tb.Cell($r,$c).Shape.TextFrame.TextRange.Text -replace "`r",' ')
              }
              $lines.Add(($cells -join ' | '))
            }
          }
        } catch {}
      }
      try {
        if ($slide.HasNotesPage -eq -1) {
          foreach ($ns in $slide.NotesPage.Shapes) {
            try {
              if ($ns.HasTextFrame -eq -1 -and $ns.TextFrame.HasText -eq -1) {
                $nt = $ns.TextFrame.TextRange.Text
                if ($nt) { $lines.Add("[NOTES] " + ($nt -replace "`r",' ')) }
              }
            } catch {}
          }
        }
      } catch {}
    }
    $pres.Close()
    $header = "# SOURCE: $($f.FullName)`n# SIZE_MB: $([math]::Round($f.Length/1MB,2))`n# CONVERTED: PowerPoint COM (shape text frames + tables + notes -> UTF-8)`n`n"
    Save-Text $dest $header ($lines -join "`n")
    Write-Output ("OK-PPT {0} slides  {1}" -f $slideCount, $rel)
  } catch {
    Write-Output ("ERROR-PPT {0} : {1}" -f $rel, $_.Exception.Message)
  }
}
$ppt.Quit()
Get-Process WINWORD,POWERPNT -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Output 'ALL DONE'
