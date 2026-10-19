import json, subprocess
raw = subprocess.run(["gh", "api", "repos/YC180/guoneng-exam-prep-app/releases"],
                     capture_output=True, text=True, encoding="utf-8")
rel = json.loads(raw.stdout)
for r in rel:
    print("  tag:", r["tag_name"], "| name:", r["name"])
    print("  url:", r["html_url"], "| published:", r["published_at"])
    for a in r["assets"]:
        print(f"  附件: {a['name']}  {a['size']/1024/1024:.2f} MB  下载数={a['download_count']}")
        print(f"        下载地址: {a['browser_download_url']}")
