#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把交付目录 `D:\\DOWNLOADS\\app` 同步进仓库内的两处**真实目录**：

  1. `D:\\app project\\app`               —— 版本库里的应用副本
  2. `D:\\app project\\android\\assets\\www` —— 打进 APK 的资产目录

为什么需要：`D:\\app project\\app` 原本是指向交付目录的**目录联接（junction）**，
Git 不会跟随联接，仓库里会变成空条目或指针，所以仓库需要一份**真实**的应用目录。
交付路径 `D:\\DOWNLOADS\\app` 保持不变（使用者双击即用），以上两处都是它的镜像。

安全护栏（必须全部通过才动任何文件）：
  1. 目标若为 junction，其 Target 必须等于交付目录 —— 否则中止；
  2. 移除 junction 只能用 `cmd /c rmdir`（**绝不用递归删除**：递归删除会穿透联接、
     把交付目录的内容真的删掉）；移除后必须确认它已不是联接、且与交付目录 realpath 不同；
  3. 删除多余文件只在目标目录内部、且仅删交付目录里不存在的项；
  4. 镜像后统计目标文件清单，与交付目录清单不一致则报错。
"""
import filecmp
import os
import shutil
import subprocess
import sys

DELIVER = r"D:\DOWNLOADS\app"
# APK 构建直接读仓库内的应用副本（再打成 ASCII 名的 assets/www.zip），
# 因此只需同步这一处即可，无需在 android 下再留一份拷贝。
TARGETS = [
    r"D:\app project\app",
]

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


def assert_safe(target):
    if not os.path.isdir(DELIVER):
        raise SystemExit(f"❌ 交付目录不存在：{DELIVER}")
    if os.path.exists(target):
        if is_junction(target):
            tgt = os.path.realpath(target)
            if os.path.normcase(tgt) != os.path.normcase(os.path.realpath(DELIVER)):
                raise SystemExit(f"❌ 联接指向的不是交付目录：{tgt} ≠ {DELIVER}，已中止")
            print(f"  检测到联接：{target} → {tgt}")
        else:
            if os.path.normcase(os.path.realpath(target)) == \
                    os.path.normcase(os.path.realpath(DELIVER)):
                raise SystemExit(f"❌ 目标与交付目录同一路径，已中止：{target}")
            print(f"  已是真实目录：{target}")


def drop_junction(target):
    if is_junction(target):
        # 只能用 rmdir 移除联接本身（Remove-Item -Recurse 会删掉目标内容）
        r = subprocess.run(["cmd", "/c", "rmdir", target], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"❌ 移除联接失败：{r.stderr.strip() or r.stdout.strip()}")
        print("  已移除联接（未触碰交付目录内容）")
    if is_junction(target):
        raise SystemExit("❌ 联接仍存在，已中止")
    if os.path.isdir(target) and os.path.normcase(os.path.realpath(target)) == \
            os.path.normcase(os.path.realpath(DELIVER)):
        raise SystemExit("❌ realpath 相同，拒绝操作")


def mirror(target):
    """单向镜像：交付目录 → 目标（复制新增/变更，删除多余）。"""
    os.makedirs(target, exist_ok=True)
    added = updated = removed = kept = 0

    deliver_files = {}
    for root, _dirs, files in os.walk(DELIVER):
        for f in files:
            p = os.path.join(root, f)
            deliver_files[os.path.relpath(p, DELIVER)] = p

    for rel, src in deliver_files.items():
        dst = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            added += 1
        elif filecmp.cmp(src, dst, shallow=False):
            kept += 1
        else:
            shutil.copy2(src, dst)
            updated += 1

    repo_files = []
    for root, _dirs, files in os.walk(target):
        for f in files:
            repo_files.append(os.path.relpath(os.path.join(root, f), target))
    for rel in repo_files:
        if rel not in deliver_files:
            os.remove(os.path.join(target, rel))
            removed += 1
    for root, dirs, _files in os.walk(target, topdown=False):
        for d in dirs:
            p = os.path.join(root, d)
            if not os.listdir(p):
                os.rmdir(p)
    return added, updated, removed, kept


def verify_against_deliver(target):
    got = sorted(os.path.relpath(os.path.join(r, f), target)
                 for r, _d, fs in os.walk(target) for f in fs)
    want = sorted(os.path.relpath(os.path.join(r, f), DELIVER)
                  for r, _d, fs in os.walk(DELIVER) for f in fs)
    if got != want:
        missing = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        raise SystemExit(f"❌ 镜像结果与交付目录不一致\n  缺失：{missing[:5]}\n  多余：{extra[:5]}")
    return len(got)


def main():
    print("== 同步 交付目录 → 仓库 app 与 android 资产目录 ==")
    failed = 0
    for target in TARGETS:
        print(f"\n-- {target}")
        try:
            assert_safe(target)
            drop_junction(target)
            added, updated, removed, kept = mirror(target)
            total = verify_against_deliver(target)
            print(f"  新增 {added}｜更新 {updated}｜删除多余 {removed}｜未变 {kept}"
                  f"｜现有 {total} 个文件")
            print("  ✅ 与交付目录逐一致")
        except SystemExit as e:
            print(f"  {e}")
            failed += 1
    if failed:
        raise SystemExit(f"❌ {failed} 个目标同步失败")
    print("\n  ✅ 全部目标同步完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
