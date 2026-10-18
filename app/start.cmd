@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set PORT=8777
title 国家能源集团备考学习 - 本地服务器

echo ============================================================
echo   国家能源集团备考学习 APP
echo ============================================================
echo.
echo   工作目录：%CD%
echo   本地端口：%PORT%
echo.

rem 端口被占用时自动向后寻找可用端口
set FOUND=
for /L %%P in (%PORT%,1,8790) do (
  if not defined FOUND (
    netstat -ano | findstr /R /C:"LISTENING" | findstr /C:":%%P " >nul
    if errorlevel 1 set FOUND=%%P
  )
)
if not defined FOUND set FOUND=%PORT%
set PORT=%FOUND%

echo   正在启动本地服务器（端口 %PORT%）...
echo   浏览器将自动打开。关闭本窗口即可停止服务。
echo.

rem 优先使用 Python，其次 Node.js
where python >nul 2>nul
if %errorlevel%==0 (
  set PYTHONIOENCODING=utf-8
  start "" "http://127.0.0.1:%PORT%/index.html"
  python -m http.server %PORT% --bind 127.0.0.1
  goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
  start "" "http://127.0.0.1:%PORT%/index.html"
  py -m http.server %PORT% --bind 127.0.0.1
  goto :end
)

where node >nul 2>nul
if %errorlevel%==0 (
  start "" "http://127.0.0.1:%PORT%/index.html"
  node -e "const h=require('http'),f=require('fs'),p=require('path');const T={'.html':'text/html;charset=utf-8','.js':'text/javascript;charset=utf-8','.css':'text/css;charset=utf-8','.json':'application/json;charset=utf-8','.webmanifest':'application/manifest+json;charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.md':'text/markdown;charset=utf-8','.txt':'text/plain;charset=utf-8'};h.createServer((q,s)=>{let u=decodeURIComponent(q.url.split('?')[0]);if(u==='/')u='/index.html';const fp=p.join(process.cwd(),u);f.readFile(fp,(e,d)=>{if(e){s.writeHead(404,{'Content-Type':'text/plain;charset=utf-8'});return s.end('404 Not Found');}s.writeHead(200,{'Content-Type':T[p.extname(fp).toLowerCase()]||'application/octet-stream','Cache-Control':'no-cache'});s.end(d);});}).listen(%PORT%,'127.0.0.1',()=>console.log('serving http://127.0.0.1:%PORT%/'));"
  goto :end
)

echo [错误] 未找到 Python 或 Node.js。
echo         可直接双击 index.html 使用（存储容量会降级，且无法安装为 PWA）。
echo.
pause

:end
echo.
echo 服务器已停止。
pause
