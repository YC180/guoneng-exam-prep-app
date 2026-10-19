# Android APK 打包（64 位手机可用）

把离线备考应用打成**可安装的 Android 安装包**，供 64 位（arm64-v8a）及 32 位手机使用。

## 一、产物

| 文件 | 说明 |
|---|---|
| `D:\DOWNLOADS\国家能源集团备考APP-v1.0.0.apk` | 交付 APK（约 3.9 MB） |
| `D:\DOWNLOADS\guoneng-exam-prep-app-v1.0.0.apk` | 同名 ASCII 副本（供 GitHub Release 上传，内容完全一致） |

- 包名 `com.guoneng.examprep`｜显示名「国家能源备考」｜`minSdk 21`（Android 5.0+，覆盖 64 位手机绰绰有余）｜`targetSdk 34`
- **不含任何原生库（.so）** → 没有 ABI 限制，arm64-v8a / armeabi-v7a / x86_64 设备都可安装运行
- 离线可用：题库（12,318 题）、知识库、9 份报告、可选导入包全部内置于 APK

## 二、结构与本机实现要点

```
android/
  AndroidManifest.xml          权限（仅 INTERNET，用于本机回环）、activity、自适应图标、网络安全配置
  src/com/guoneng/examprep/
    MainActivity.java          WebView 外壳：加载内置服务、返回键回退、外链交给系统浏览器、
                               失败时在界面直说原因（不白屏、不静默）
    AssetServer.java           内置 127.0.0.1 静态服务（只读归档、拒绝 .. 路径、仅 GET）
  res/                         应用名、主题色、自适应图标前景/背景、network_security_config.xml
  make_icons.py                由应用自带图标生成 5 种密度的传统图标 + 自适应图标前景
  build_apk.py                 构建流水线（见下）
  keystore/                    签名密钥（见第四节）
```

**为什么应用本体打包成 `assets/www.zip` 而不是逐个文件放 assets**
`aapt2` 在 Windows 上无法打开**中文文件名**的资产（实测报
`assets\www\docs\01_资料归纳总结.md: error: failed to open file`），
而应用里有中文名的报告与可选导入包。改为单个 **ASCII 名归档**后：
① 彻底绕开该缺陷；② 15 MB 题库只需一次解包，运行时按需随机读取，比逐文件压缩资产更快。
归档内 11 个非 ASCII 名条目都带 UTF-8（EFS）标记，Android 的 `ZipFile` 能正确解码。

**为什么用 `http://127.0.0.1:<随机端口>` 而不是 `file://` 打开**
`file://` 源在 Android WebView 里 IndexedDB 常被禁用、Service Worker 无法注册；
`http://127.0.0.1` 属于**安全上下文**，应用的「IndexedDB → localStorage → 内存」三级降级
与 `sw.js` 离线缓存都能正常工作。首次启动把归档复制到应用私有目录
（由 `assets/www.id` 版本标记决定是否需要重新复制），再用 `ZipFile` 随机访问。

## 三、重建

前置：JDK 17（`D:\android-sdk\jdk`）＋ Android SDK（`build-tools;34.0.0`、`platforms;android-34`），
本机安装方式见仓库根 `README.md`；路径在 `build_apk.py` 顶部常量中可改。

```powershell
cd "D:\app project"
python android\make_icons.py       # 生成图标（源图标变了才需要重跑）
python work\sync_app_to_repo.py   # 交付目录 → 仓库 app（构建读的是这一份）
python android\build_apk.py       # 出 APK 并自检
```

`build_apk.py` 流水线：生成 `www.zip`+`www.id` → `aapt2 compile` → `aapt2 link`（`-A` 打入归档）
→ `javac`（对 `android.jar`，target 8）→ `d8`（min-api 21）→ 注入 `classes.dex`
→ `zipalign -p -f 4` → `keytool`/`apksigner`（v1+v2+v3）→ 自检。

自检内容（任一不通过即构建失败）：
签名方案与证书、`badging` 的包名/版本/minSdk/targetSdk/权限/**native-code 为空**、
APK 内归档条目数与仓库应用目录**逐一致**、归档 SHA-256 与构建产物一致、
版本标记一致、题库条目数（≥12,000，当前 12,318）。

## 四、签名密钥（重要，请读完）

`keystore/guoneng-release.keystore`，别名 `guoneng`，口令 **`guoneng2026`**，
有效期 30 年（RSA 2048），DN 为 `CN=Guoneng Exam Prep, OU=Personal Study, O=Personal, C=CN`。

- **它随仓库一起公开**：这样你（或任何人）以后重建的 APK 与原包**签名相同**，
  手机上可以**直接覆盖升级**，不必先卸载。私钥本就只用于这一个个人应用，风险很低。
- 代价：知道口令的人可以为 `com.guoneng.examprep` 签出「同签名」的包。
  只要你只安装来自你自己构建/本仓库 Release 的 APK，就没有实际影响。
- 若你希望改成私有保管：删掉 `keystore/` 并把它从版本库移除，自行
  `keytool -genkeypair` 生成并**离线备份**；此后升级必须使用同一密钥，
  否则用户需先卸载旧版（会丢失本机答题记录，可用应用内「导出备份」先留存）。

## 五、安装到手机（侧载）

1. 把 `国家能源集团备考APP-v1.0.0.apk` 传到手机（数据线、微信文件传输助手、网盘均可）。
2. 在手机上点开该 APK；首次会提示「不允许安装未知应用」→ 到设置里允许该来源（浏览器/文件管理器）。
3. 安装完成后桌面出现「国家能源备考」。
4. 首次启动会把内置归档解包到应用私有目录（一次性，约 15 MB），随后完全离线可用。

若要在电脑上用 adb 安装（需手机开启 USB 调试）：

```powershell
& "D:\android-sdk\platform-tools\adb.exe" install -r "D:\DOWNLOADS\国家能源集团备考APP-v1.0.0.apk"
```

## 六、验证边界（务必了解）

**已实证**（构建自检 + 独立审计脚本）：
- 签名 v1/v2/v3 均通过；证书、包名、版本、minSdk 21 / targetSdk 34、仅 INTERNET 权限
- `badging` **无 `native-code` 行** → 不含原生库，不受 64 位/ABI 限制
- `classes.dex` 内确含 `MainActivity` / `AssetServer` 与 `R` 类
- APK 内 `assets/www.zip` 的 **31 个文件与交付应用逐字节一致**（该份内容已通过
  冒烟测试、jsdom 端到端测试、编码检查与离线自足检查）
- 归档内中文名条目均带 UTF-8 标记；`www.id` 版本标记与归档 SHA-256 对应

**未实证（本机条件所限，如实说明）**：
- **未在真机/模拟器上实际运行过**：本机 `HypervisorPresent=False`（未启用 Windows
  Hypervisor Platform / WHPX），Android 模拟器要么需开启系统功能并**重启**、要么无硬件加速
  （几乎不可用）；也没有连接的实体设备。因此「启动后 WebView 正常渲染、答题记录可持久化」
  属于**合理推断**（标准 ServerSocket/WebView/ZipFile 用法）而非实测。
- 若首次启动出现问题，应用不会白屏：会直接显示失败原因文本；请把该文本反馈给我。

## 七、版本

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0.0 | 2026-10-19 | 首个 APK：题库 12,318 题 / 资料 370 份 / 9 份报告 / 可选导入包 127 题 |
