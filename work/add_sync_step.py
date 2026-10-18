p = "finalize_all.py"
t = open(p, encoding="utf-8").read()
old = '    ("verify_readme_claims.py", "交付 README 数字与产物对账", False),\n]'
new = ('    ("verify_readme_claims.py", "交付 README 数字与产物对账", False),\n'
       '    ("sync_app_to_repo.py", "交付目录 → 仓库 app 镜像（供版本库提交）", False),\n]')
assert old in t, "未找到 verify_readme_claims 步骤行"
t = t.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("✅ finalize_all.py 已加 sync_app_to_repo（共 15 步）")
