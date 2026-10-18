<#
  国家能源集团备考学习 APP —— 本地服务器启动脚本（PowerShell 版）
  用法：右键“使用 PowerShell 运行”，或  pwsh -File start.ps1
#>
[CmdletBinding()]
param(
  [int]$Port = 8777,
  [switch]$Lan          # 允许局域网访问（手机同 Wi-Fi 使用）
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath $PSScriptRoot

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host '  国家能源集团备考学习 APP' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host ("  目录：" + (Get-Location).Path)

# 找一个可用端口
$bind = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$chosen = $null
foreach ($p in $Port..($Port + 20)) {
  $busy = $false
  try {
    $busy = [bool](Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue)
  } catch {
    $busy = [bool](netstat -ano | Select-String -Pattern (":$p\s+.*LISTENING"))
  }
  if (-not $busy) { $chosen = $p; break }
}
if (-not $chosen) { $chosen = $Port }
Write-Host ("  端口：$chosen    监听：$bind")
Write-Host ''

# 选择运行时
$python = $null
foreach ($cand in @('python', 'py')) {
  $cmd = Get-Command $cand -ErrorAction SilentlyContinue
  if ($cmd) { $python = $cmd.Source; $pyArgs = @('-m', 'http.server'); break }
}

$urlHost = if ($Lan) { (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -First 1 -ExpandProperty IPAddress) } else { '127.0.0.1' }
$url = "http://${urlHost}:$chosen/index.html"

if ($python) {
  Write-Host "  使用 $python 启动静态服务器…" -ForegroundColor Green
  Write-Host ("  打开：" + $url) -ForegroundColor Yellow
  Write-Host '  关闭本窗口或按 Ctrl+C 停止服务。' -ForegroundColor DarkGray
  Write-Host ''
  Start-Process $url
  & $python -m http.server $chosen --bind $bind
  exit 0
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
  Write-Host '  未找到 Python，改用 Node.js 内置静态服务器…' -ForegroundColor Yellow
  Write-Host ("  打开：" + $url) -ForegroundColor Yellow
  Write-Host ''
  $js = @'
const http=require('http'),fs=require('fs'),path=require('path');
const T={'.html':'text/html;charset=utf-8','.js':'text/javascript;charset=utf-8','.css':'text/css;charset=utf-8','.json':'application/json;charset=utf-8','.webmanifest':'application/manifest+json;charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.md':'text/markdown;charset=utf-8','.txt':'text/plain;charset=utf-8'};
const port=+process.argv[1], host=process.argv[2];
http.createServer((q,s)=>{
  let u=decodeURIComponent(q.url.split('?')[0]); if(u==='/')u='/index.html';
  const fp=path.join(process.cwd(),u);
  fs.readFile(fp,(e,d)=>{
    if(e){s.writeHead(404,{'Content-Type':'text/plain;charset=utf-8'});return s.end('404 Not Found');}
    s.writeHead(200,{'Content-Type':T[path.extname(fp).toLowerCase()]||'application/octet-stream','Cache-Control':'no-cache'});
    s.end(d);
  });
}).listen(port,host,()=>console.log(`serving http://${host}:${port}/`));
'@
  Start-Process $url
  & $node.Source -e $js $chosen $bind
  exit 0
}

Write-Host '  [错误] 未找到 Python 或 Node.js。' -ForegroundColor Red
Write-Host '         可直接双击 index.html 使用（存储会降级，且无法安装为 PWA）。' -ForegroundColor Red
