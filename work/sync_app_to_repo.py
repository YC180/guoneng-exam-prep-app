#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把交付目录 `D:\\DOWNLOADS\\app` 同步进仓库内的真实目录 `D:\\app project\\app`。

为什么需要：`D:\\app project\\app` 原本是指向交付目录的**目录联接（junction）**，
Git 不会跟随联接，仓库里会变成空条目或指针，所以仓库需要一份**真实**的应用目录。
交付路径 `D:\\DOWNLOADS\\app` 保持不变（使用者双击即用），仓库内的 `app\\` 是它的镜像。

安全护栏（必须全部通过才动任何文件）：
  1. 目标确实是 junction，且其 Target 必须等于交付目录 —— 否则中止；
  2. 移除 junction 只能用 `cmd /c rmdir`（**绝不用递归删除**：递归删除会穿透联接、
     把交付目录的内容真的删掉）；移除后必须确认它已不是联接、且与交付目录 realpath 不同；
  3. 删除多余文件只在 `app\\` 内部、且仅删交付目录里不存在的项；
  4. 镜像前后统计交付目录文件数，若镜像结果与交付目录清单不一致则报错。
"""
import filecmp
import os
import shutil
import subprocess
import sys

REPO_APP = r"D:\app project\app"
DELIVER = r"D:\DOWNLOADS\app"


IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003


def is_junction(path):
    """Windows 目录联接的可靠探测。

    注意：`os.path.islink()` 对 **junction 返回 False**（junction 在 lstat 里是目录、
    不是符号链接，只有 symlink 才是 S_ISLNK）。必须看重解析标签，
    否则会把联接当成真实目录，进而误判“与交付目录同一路径”。
    """
    if not os.path.isdir(path):
        return False
    try:
        tag = getattr(os.lstat(path), "st_reparse_tag", 0)
        if tag == IO_REPARSE_TAG_MOUNT_POINT:
            return True
    except OSError:
        return False
    try:                      # 兜底：junction 也能被 readlink 读出目标
        return os.readlink(path) is not None and os.path.isdir(path) and tag != 0
    except OSError:
        return False


def assert_safe():
    if not os.path.isdir(DELIVER):
        raise SystemExit(f"❌ 交付目录不存在：{DELIVER}")
    if os.path.exists(REPO_APP):
        if is_junction(REPO_APP):
            tgt = os.path.realpath(REPO_APP)
            if os.path.normcase(tgt) != os.path.normcase(os.path.realpath(DELIVER)):
                raise SystemExit(f"❌ 联接指向的不是交付目录：{tgt} ≠ {DELIVER}，已中止")
            print(f"  检测到联接：{REPO_APP} → {tgt}")
        else:
            # 已经是真实目录：确认它不是交付目录本身（防同一路径双向覆盖）
            if os.path.normcase(os.path.realpath(REPO_APP)) == os.path.normcase(os.path.realpath(DELIVER)):
                raise SystemExit("❌ 仓库 app 是真实目录且与交付目录同一路径，已中止")
            print(f"  已是真实目录：{REPO_APP}")


def drop_junction():
    if is_junction(REPO_APP):
        # 只能用 rmdir 移除联接本身（Remove-Item -Recurse 会删掉目标内容）
        r = subprocess.run(["cmd", "/c", "rmdir", REPO_APP], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"❌ 移除联接失败：{r.stderr.strip() or r.stdout.strip()}")
        print("  已移除联接（未触碰交付目录内容）")
    if is_junction(REPO_APP):
        raise SystemExit("❌ 联接仍存在，已中止")
    if os.path.isdir(REPO_APP) and os.path.normcase(os.path.realpath(REPO_APP)) == \
            os.path.normcase(os.path.realpath(DELIVER)):
        raise SystemExit("❌ realpath 相同，拒绝操作")


def mirror():
    """单向镜像：交付目录 → 仓库 app（复制新增/变更，删除多余）。"""
    os.makedirs(REPO_APP, exist_ok=True)
    added = updated = removed = kept = 0

    deliver_files = {}
    for root, _dirs, files in os.walk(DELIVER):
        for f in files:
            p = os.path.join(root, f)
            deliver_files[os.path.relpath(p, DELIVER)] = p

    # 复制 / 更新
    for rel, src in deliver_files.items():
        dst = os.path.join(REPO_APP, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            added += 1
        elif filecmp.cmp(src, dst, shallow=False):
            kept += 1
        else:
            shutil.copy2(src, dst)
            updated += 1

    # 删除仓库里多出来的文件/空目录（严格限定在 REPO_APP 内部）
    repo_files = []
    for root, _dirs, files in os.walk(REPO_APP):
        for f in files:
            repo_files.append(os.path.relpath(os.path.join(root, f), REPO_APP))
    for rel in repo_files:
        if rel not in deliver_files:
            os.remove(os.path.join(REPO_APP, rel))
            removed += 1
    for root, dirs, files in os.walk(REPO_APP, topdown=False):
        for d in dirs:
            p = os.path.join(root, d)
            if not os.listdir(p):
                os.rmdir(p)

    return added, updated, removed, kept, len(deliver_files)


def main():
    print("== 同步 交付目录 → 仓库 app ==")
    assert_safe()
    drop_junction()
    added, updated, removed, kept, total = mirror()
    # 校验：仓库内文件清单必须与交付目录一致
    repo = []
    for root, _dirs, files in os.walk(REPO_APP):
        for f in files:
            repo.append(os.path.relpath(os.path.join(root, f), REPO_APP))
    if sorted(repo) != sorted(
            os.path.relpath(os.path.join(r, f), DELIVER)
            for r, _d, fs in os.walk(DELIVER) for f in fs):
        raise SystemExit("❌ 镜像结果与交付目录清单不一致，请检查")
    print(f"  新增 {added}｜更新 {updated}｜删除多余 {removed}｜未变 {kept}"
          f"｜仓库 app 现有 {len(repo)} 个文件（交付目录 {total} 个）")
    print("  ✅ 仓库 app 已是真实目录且与交付目录一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
