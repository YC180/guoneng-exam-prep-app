# 国家能源集团备考学习 APP（离线 PWA）＋ 可复现构建流程

面向**个人求职备考**的离线刷题应用：把 `26国家能源集团通关资料` 里的 370 份资料
（含大量扫描件）读完、归纳总结、联网核实过时信息，做成**结构化题库**与**可离线使用的
手机端 Web APP**。全部中文、简体；不调用任何外部 AI 接口。

> **本文性质**：只采用原始资料中真实存在的表述。凡原资料未载明者一律标注
> 「原资料未提供解析」或「待核对」，**不补写、不推测、不编造答案**。

## 一、目录结构

```
app/                 交付给使用者的应用（直接双击 app/index.html 即可用）
  index.html         入口
  js/                store / bank / practice / exam / stats / io / ui / app
  css/app.css        全部样式（含深色主题与响应式）
  data/
    questions.js     window.CE_BANK：结构化题库（12,318 题）
    knowledge.js     window.CE_KNOWLEDGE：联网核实过的企业文化/集团概况
  docs/              9 份整理报告（归纳总结、联网核实、时政、行测、面试与专业知识、
                     题库校验、阅读覆盖度审计、政治理论、历年真题与考情分析）
  可选导入/           可选导入包（专业知识 127 题，**不计入**主题库题量）
  sw.js manifest.webmanifest icons/ start.cmd start.ps1 README.md

android/            Android APK 工程（纯 Java + WebView，**不含原生库** → 32/64 位手机都能装）
  AndroidManifest.xml src/ res/  清单、外壳与内置 127.0.0.1 静态服务、图标与资源配置
  make_icons.py     由应用图标生成 5 种密度图标（含 Android 8+ 自适应图标前景）
  build_apk.py      构建流水线：归档 → aapt2 → javac → d8 → zipalign → apksigner → 自检
  keystore/         签名密钥（随仓库公开，便于后续版本覆盖升级；见 android/README.md）
  README.md         APK 构建、结构取舍、签名说明、侧载步骤与验证边界

work/               构建与审计脚本、抽取文本、OCR 结果、结构化题库与各类审计 JSON
  build_bank.py     解析全部来源 → 统一题库（核心）
  finalize_bank.py  答案自洽复核、结构自洽复核、可作答性强制（破坏性，须重建）
  integrity_audit.py/quality_audit.py/audit_ingest_gap.py   三类质量审计
  gen_docs.py/gen_validation_doc.py/gen_coverage_doc.py/gen_exam_analysis.py
  gen_optional_pack.py  生成可选导入包
  read_coverage.py  防静默覆盖度校验（任何文件漏统计都会报错）
  check_offline.py  离线自足性与预缓存覆盖校验
  verify_readme_claims.py  README 数字 ↔ 产物对账（自维护）
  sync_app_to_repo.py     交付目录 → 仓库 app 的镜像（含联接安全护栏）
  finalize_all.py   一键跑完上述全部 15 步
  text/ text2/ … text7/   各来源的抽取文本（text7 = 2026-10-19 新增 14 份）
  ocr/              扫描件的 OCR 文本与逐文件清单
  bank/             questions.json、校验/质量/覆盖度/反向审计 JSON
  docs_notes/       过程中发现的问题与修复记录（含测试证据）
  domtest/          jsdom 端到端测试（渲染、答题、模拟考、待核对口径、正确率分母）

原始资料/            指向厂商备考资料的目录联接（约 1.76 GB / 370 份）—— **未纳入版本库**
```

## 二、怎么用

**直接打开**：双击 `app/index.html` 即可（经典 `<script>` 加载，无构建步骤，`file://` 下可用）。

**推荐方式**（启用离线缓存 / 可安装到手机主屏）：

```powershell
cd app
.\start.cmd          # 起本地静态服务并打开浏览器
```

`start.ps1` 是对应的 PowerShell 版本。手机使用见 `app/README.md` 第一节（同一 Wi-Fi 访问本机 IP；
iOS/Android 均可「添加到主屏幕」，断网后照常刷题）。

答题记录只存在**本机浏览器**（IndexedDB → localStorage → 内存 三级降级）；
「资料与设置」里可导出**完整备份**，换设备时恢复。

**手机安装成 App（Android，推荐给“要在 64 位手机上用”的场景）**：
用仓库 Release 里的 **`guoneng-exam-prep-app-v1.0.0.apk`**（约 3.9 MB）直接侧载安装，
桌面出现「国家能源备考」，完全离线可用。APK 为纯 Java + WebView 外壳且**不含原生库**，
所以 arm64-v8a / armeabi-v7a 设备都能装（`aapt2 dump badging` 中 `native-code` 一栏为空即为实证）。
构建方法、结构取舍（应用本体打成 ASCII 名 `assets/www.zip` 以绕开 aapt2 中文路径缺陷）、
签名密钥说明、侧载步骤与**验证边界**见 [`android/README.md`](android/README.md)。

## 三、怎么重建

依赖：Python 3（脚本用到 PyMuPDF / pypdf / python-docx；扫描件 OCR 另需
rapidocr-onnxruntime + onnxruntime + opencv）。

```powershell
cd work
python finalize_all.py       # 15 步：解析→复核→审计→生成报告→离线校验→README 对账
```

单独重跑某一步也可以，例如只重建题库与报告：`python build_bank.py`、`python gen_docs.py`。

要**从原始 PDF 重新抽取文本**（需要那份 1.76 GB 资料），把资料放回 `原始资料/`
（或改脚本里的根路径），再执行：

```powershell
python extract.py --roots "<资料目录>" --out text7      # 文本层提取
python ocr_plan.py ; python ocr.py                       # 扫描件 OCR（耗时较长）
```

## 四、数据处理原则（可核对）

- **不静默吞掉任何文件**：`read_coverage.py` 对资料目录逐份判定并在
  `docs/07` 三档列明（有文本 / 靠 OCR 还原 / 纯图片 / 仍无可用文本），
  目录内文件数与登记数不一致就直接报错。
- **“已核对”必须可作答**：答案键必须落在选项内、选项不得重复、题干不得为空；
  结构不成形的题降级为「待核对」，**不计入正确率统计**。
- **答案自洽复核**：当解析里能独立推出结论（如「故本题答案为 X」）时，与答案字段比对，
  冲突者**降级为待核对**（实测一致率 96.6%）。
- **联网核实**：过时的企业与考试信息按官网（ceic.com 等）核对，逐条给出结论与来源链接，
  见 `docs/02`；2025 年官网新版企业文化为准，旧《三色笔记》仅作对照。
- **明确排除**（各有可核对原因，见 `docs/07` 第三、七节）：图形推理 350 题（选项全为
  「如上图所示」，题干图形不可提取）、纯题本（无答案）、水印污染的 2020/2021/2022 真题 OCR 等。

当前题库：**12,318 题**（已核对 11,744 / 待核对 505 / 无答案 69；结构完整 11,274，91.5%），
资料覆盖：**370 份**逐份登记（296 份直接提取正文、68 份靠 OCR 还原、4 份纯图片、2 份内容本身无正文）。

## 五、许可与声明

- 代码与整理成果：供个人备考使用，可自由取用与修改。
- **原始备考资料（PDF/DOCX/PPT）版权归原机构所有**，本仓库**不再分发**，
  仅保留为构建题库所需的抽取文本与结构化数据；请勿将原始资料二次公开传播。
- 题库内容来自原始资料与公开官网信息，可能存在识别讹字或过时表述；
  涉及报考条件、时间、政策等**以官方最新公告为准**。
