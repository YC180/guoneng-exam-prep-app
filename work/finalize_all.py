#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一键重建：题库 → 校验 → 报告 → 覆盖度审计。OCR 补做完成后直接跑这一个命令。

顺序（每一步失败都会**明确报错并停止**，绝不静默吞掉错误）：
  1. build_bank.py           从全部语料（文本 + OCR）重建题库
  2. finalize_bank.py        去重、答案自洽复核、结构自洽复核、写出 APP 题库
  3. integrity_audit.py      校验「已核对」的题是否名副其实（硬错误必须为 0）
  4. bank_stats.py           题库统计
  5. quality_audit.py        结构质量审计
  6. gen_docs.py             写 docs/01
  7. gen_validation_doc.py   写 docs/06（由真实校验结果派生）
  8. gen_coverage_doc.py     写 docs/07（阅读覆盖度审计）
  9. read_coverage.py        防静默覆盖度校验（有任何文件未登记即失败）

用法：
  python finalize_all.py            # 全跑
  python finalize_all.py --skip-build   # 语料没变时，从校验开始跑
"""
import os
import subprocess
import sys
import time

WORK = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ("build_bank.py", "重建题库（解析全部语料）", True),
    ("finalize_bank.py", "去重与三重校验、写出 APP 题库", True),
    ("integrity_audit.py", "「已核对」名副其实性校验", True),
    ("bank_stats.py", "题库统计", False),
    ("quality_audit.py", "结构质量审计", False),
    ("audit_ingest_gap.py", "审计「已读但未入库」的可用题源", False),
    ("gen_docs.py", "生成 docs/01 资料归纳总结", False),
    ("gen_validation_doc.py", "生成 docs/06 题库校验报告", False),
    ("gen_coverage_doc.py", "生成 docs/07 阅读覆盖度审计", False),
    ("gen_exam_analysis.py", "生成 docs/09 历年真题与考情分析", False),
    ("gen_optional_pack.py", "生成可选导入包（专业知识，不入主题库）", False),
    ("read_coverage.py", "防静默覆盖度校验", False),
    ("check_offline.py", "离线自足性与预缓存覆盖校验", False),
    ("verify_readme_claims.py", "交付 README 数字与产物对账", False),
    ("sync_app_to_repo.py", "交付目录 → 仓库 app 镜像（供版本库提交）", False),
]


def main():
    skip_build = "--skip-build" in sys.argv
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    results = []
    t0 = time.time()
    for i, (script, desc, critical) in enumerate(STEPS, 1):
        if skip_build and script == "build_bank.py":
            print(f"[{i}/{len(STEPS)}] 跳过 {script}")
            continue
        path = os.path.join(WORK, script)
        if not os.path.exists(path):
            print(f"[{i}/{len(STEPS)}] ❌ 脚本不存在：{path}")
            return 2
        print(f"\n{'='*72}\n[{i}/{len(STEPS)}] {script} —— {desc}\n{'='*72}")
        t = time.time()
        p = subprocess.run([PY, path], cwd=WORK, env=env)
        dt = time.time() - t
        rc = p.returncode
        # read_coverage.py 的退出码含义：
        #   0 = 全部有文本；2 = 356 份都已登记、但仍有若干份无可用文本（警告级）；
        #   3 = 有文件未被登记（静默漏读，必须视为失败）。
        # 因此只放行 2，绝不放行 3 —— 不静默吞掉真正的漏读。
        ok, warned = rc == 0, False
        if script == "read_coverage.py" and rc == 2:
            ok, warned = True, True
        results.append((script, rc, dt, ok))
        print(f"---- {script} 退出码 {rc}，用时 {dt:.1f}s ----")
        if warned:
            print("⚠️  仍有若干扫描件无可用文本（已全部登记，非静默漏读）——见 docs/07")
        if not ok:
            print(f"❌ 步骤失败：{script}（退出码 {rc}）"
                  f"{'——这是关键步骤，必须修复后再继续' if critical else ''}")
            return rc or 1
    print(f"\n{'='*72}\n全部步骤完成 ✅  总用时 {time.time()-t0:.1f}s\n{'='*72}")
    for script, rc, dt, ok in results:
        print(f"  {'✅' if ok else '❌'} {script:24s} 退出码 {rc}   {dt:6.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
