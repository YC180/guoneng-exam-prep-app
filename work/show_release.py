import json, subprocess
raw = subprocess.run(["gh", "api", "repos/YC180/guoneng-exam-prep-app/releases/tags/v1.0.0"],
                     capture_output=True, text=True, encoding="utf-8")
r = json.loads(raw.stdout)
print("  tag:", r["tag_name"], "|", r["name"])
print("  url:", r["html_url"])
for a in r["assets"]:
    print(f"  附件: {a['name']}  {a['size']/1024/1024:.2f} MB  下载数={a['download_count']}")
    print(f"        {a['browser_download_url']}")
