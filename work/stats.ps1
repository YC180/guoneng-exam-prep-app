$ErrorActionPreference = 'Stop'
$files = @()
$files += 'D:\app project\work\text\4-7-EPI综合能力题库----资料分析题库+解析_.txt'
$files += (Get-ChildItem -LiteralPath 'D:\app project\work\text\EPI综合能力500题\' -Filter *.txt | ForEach-Object { $_.FullName })
foreach ($f in $files) {
  $raw = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
  $chars = $raw.Length
  $lf = ([regex]::Matches($raw, "`n")).Count
  $crlf = ([regex]::Matches($raw, "`r`n")).Count
  $q = ([regex]::Matches($raw, '(?m)^\s*\d+\s*[\.、）\)]')).Count
  $pages = ([regex]::Matches($raw, '\[\[PAGE \d+\]\]')).Count
  $maxnum = 0
  foreach ($m in [regex]::Matches($raw, '(?m)^\s*(\d+)\s*[\.、）\)]')) { $n = [int]$m.Groups[1].Value; if ($n -gt $maxnum) { $maxnum = $n } }
  $nul = ([regex]::Matches($raw, "`0")).Count
  Write-Output ("FILE=" + (Split-Path $f -Leaf))
  Write-Output ("  chars=$chars lf=$lf crlf=$crlf qmark=$q maxq=$maxnum pages=$pages nul=$nul")
}
