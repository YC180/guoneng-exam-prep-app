$dir='D:\app project\work\text'
$targets=@()
$targets+=(Join-Path $dir '4-7-EPI综合能力题库----资料分析题库+解析_.txt')
$targets+=(Get-ChildItem -LiteralPath (Join-Path $dir 'EPI综合能力500题') -Filter *.txt | Sort-Object Name | ForEach-Object {$_.FullName})
$qstart='(?m)^\s*(\d{1,3})\s*[\.\u3001\uFF0E\uFF09\)]'
foreach($f in $targets){
  $raw=[System.IO.File]::ReadAllText($f,[System.Text.Encoding]::UTF8)
  Write-Output ("##### " + (Split-Path $f -Leaf))
  # first/last question starts
  $ms=[regex]::Matches($raw,$qstart)
  if($ms.Count -gt 0){
    $first=$ms[0].Value.Trim(); $last=$ms[$ms.Count-1].Value.Trim()
    Write-Output ("  firstQstart='" + $first + "'  lastQstart='" + $last + "'")
    # nums sequence, detect gaps/restarts
    $nums=@(); foreach($m in $ms){ $nums += [int]$m.Groups[1].Value }
    $seq = ($nums | Select-Object -First 25) -join ','
    Write-Output ("  first25nums: " + $seq)
    $seqT = ($nums | Select-Object -Last 20) -join ','
    Write-Output ("  last20nums : " + $seqT)
    $dup = ($nums | Group-Object | Where-Object {$_.Count -gt 1} | ForEach-Object { "$($_.Name)x$($_.Count)" }) -join ' '
    Write-Output ("  repeatedNums: " + $dup)
  } else { Write-Output "  firstQstart=<none>" }
  # option-letter presence check per block
  $idx=@(); foreach($m in $ms){ $idx += $m.Index }
  $blocks=@()
  for($i=0;$i -lt $idx.Count;$i++){
    $end = if($i+1 -lt $idx.Count){$idx[$i+1]}else{$raw.Length}
    $blocks += ,($raw.Substring($idx[$i], $end-$idx[$i]))
  }
  $missing=0; $missList=@()
  for($i=0;$i -lt $blocks.Count;$i++){
    $b=$blocks[$i]
    $ok=$true
    foreach($L in @('A','B','C','D')){
      if($b -notmatch ("(?<![A-Za-z])" + $L + "[\.\uFF0E\u3001]")){ $ok=$false }
    }
    if(-not $ok){ $missing++; if($missList.Count -lt 6){ $missList += $nums[$i] } }
  }
  Write-Output ("  blocks=" + $blocks.Count + " blocksMissingAnOption=" + $missing + " egs=" + ($missList -join ','))
  # answer/explanation tag counts
  $a=([regex]::Matches($raw,'\u3010\u7B54\u6848\u3011')).Count
  $j=([regex]::Matches($raw,'\u3010\u89E3\u6790\u3011')).Count
  $a2=([regex]::Matches($raw,'\u7B54\u6848\uFF1A')).Count
  $j2=([regex]::Matches($raw,'\u89E3\u6790\uFF1A')).Count
  $kp=([regex]::Matches($raw,'\u3010\u77E5\u8BC6\u70B9\u3011')).Count
  Write-Output ("  tags: [ans]=$a [jie]=$j '答案:'=$a2 '解析:'=$j2 [知识点]=$kp")
}
