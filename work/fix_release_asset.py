import json, os, shutil, subprocess
REPO = "YC180/guoneng-exam-prep-app"
SRC = r"D:\DOWNLOADS\国家能源集团备考学习APP_2026-10-19.zip"
ASCII = r"D:\DOWNLOADS\guoneng-exam-prep-app-v1.0.0.zip"
NAME = "guoneng-exam-prep-app-v1.0.0.zip"

def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()

rc, out, err = gh("api", f"repos/{REPO}/releases/tags/v1.0.0")
assert rc == 0, err
rel = json.loads(out)
rid = rel["id"]
print("  release id:", rid, "| 现有附件:", [a["name"] for a in rel["assets"]])

# 删掉被截名的附件
for a in rel["assets"]:
    rc, _o, e = gh("api", "-X", "DELETE", f"repos/{REPO}/releases/assets/{a['id']}")
    print(f"  删除附件 {a['name']}: {'OK' if rc == 0 else e}")

# 复制一份 ASCII 名的包后上传（内容与中文名包完全一致）
shutil.copy2(SRC, ASCII)
print(f"  ASCII 名副本: {ASCII}  {os.path.getsize(ASCII)/1024/1024:.2f} MB"
      f"  (与源同内容: {open(SRC,'rb').read() == open(ASCII,'rb').read()})")

rc, out, err = gh("api", "-X", "POST", "--input", ASCII,
                  "-H", "Content-Type: application/zip",
                  f"https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name={NAME}")
print("  上传:", "OK" if rc == 0 else err[:300])
if rc == 0:
    j = json.loads(out)
    print(f"  附件名: {j['name']}  大小 {j['size']/1024/1024:.2f} MB")
    print(f"  下载地址: {j['browser_download_url']}")
