$dir='D:\app project\work\text'
$p500=Join-Path $dir 'EPI综合能力500题'
$files=@{
 '判断推理-答案'=(Join-Path $p500 'EPI综合能力测试-判断推理-试题答案.txt')
 '思维策略-答案'=(Join-Path $p500 'EPI综合能力测试-思维策略-试题答案.txt')
 '数量关系-答案'=(Join-Path $p500 'EPI综合能力测试-数量关系-试题答案.txt')
 '言语理解-答案'=(Join-Path $p500 'EPI综合能力测试-言语理解-试题答案.txt')
 '资料分析-答案'=(Join-Path $p500 'EPI综合能力测试-资料分析-试题答案.txt')
 '常识200-答案'=(Join-Path $p500 '常识200道试题答案.txt')
}
foreach($k in $files.Keys | Sort-Object){
  $raw=[System.IO.File]::ReadAllText($files[$k],[System.Text.Encoding]::UTF8)
  $found=@{}
  # answer tag followed by option letter
  foreach($m in [regex]::Matches($raw,'(?m)^\s*(\d{1,3})\s*[\.\u3001\uFF0E\uFF09\)]\s*\u3010\u7B54\u6848\u3011')){
    $found[[int]$m.Groups[1].Value]=$true
  }
  foreach($m in [regex]::Matches($raw,'(?m)^\s*(\d{1,3})\s*[\.\u3001\uFF0E\uFF09\)].{0,12}?\u3010\u7B54\u6848\u3011')){
    $found[[int]$m.Groups[1].Value]=$true
  }
  $limit = if($k -like '*常识*'){200}else{100}
  $missing=@(); for($i=1;$i -le $limit;$i++){ if(-not $found.ContainsKey($i)){ $missing+=$i } }
  Write-Output ("$k : ansTagged=$($found.Count) missing=$($missing -join ',')")
}
Write-Output '=== FILE A material structure ==='
$fa=Join-Path $dir '4-7-EPI综合能力题库----资料分析题库+解析_.txt'
$raw=[System.IO.File]::ReadAllText($fa,[System.Text.Encoding]::UTF8)
$lines=$raw -split "`n"
$matRe='^\s*(\u6750\u6599|\u4E00\u3001|\u4E8C\u3001|\u4E09\u3001|\u56DB\u3001|\u4E94\u3001|\u516D\u3001|\u4E03\u3001)'
$i=0
foreach($l in $lines){
  $i++
  if($l -match $matRe -and $l.Length -lt 40){ Write-Output ("  L$i : " + $l.Trim()) }
}
