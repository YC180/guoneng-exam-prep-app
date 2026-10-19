#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把离线备考应用打包成 Android APK（手工流水线，不依赖 Gradle）。

流水线：
  1) 由仓库内的应用副本 `D:\\app project\\app` 生成 ASCII 名的归档
     `www.zip` + 版本标记 `www.id`（aapt2 在 Windows 上打不开中文文件名的资产，
     且集中成单个归档后运行时读取更快）
  2) aapt2 compile   资源 → 扁平 zip
  3) aapt2 link      生成 base.apk（含 res、AndroidManifest、assets/www.zip）
  4) javac           编译 Java 源码（对本机 android.jar 编译，target 8）
  5) d8              转成 classes.dex（min-api 21）
  6) 注入 classes.dex 进 base.apk
  7) zipalign        4 字节对齐
  8) keytool + apksigner  生成/复用签名密钥并签名（v1+v2+v3）
  9) 自检：签名证书、badging（包名/minSdk/targetSdk/权限/native-code）、
     APK 内归档条目与应用目录逐一致、题库条目数
     —— 并按归档内容 SHA-256 生成 APK 校验值一并打印

为什么用纯 Java + WebView 且不含原生库：
  没有 .so 就不存在 ABI 限制，32 位与 64 位（arm64-v8a / armeabi-v7a / x86_64）
  手机都能安装运行；badging 里 `native-code` 一栏为空即为「不挑架构」的实证。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import zipfile

SDK = r"D:\android-sdk"
JDK = os.path.join(SDK, "jdk")
BUILD_TOOLS = os.path.join(SDK, "build-tools", "34.0.0")
ANDROID_JAR = os.path.join(SDK, "platforms", "android-34", "android.jar")

PROJ = os.path.abspath(r"D:\app project\android")
APP_SRC = r"D:\app project\app"
BUILD = os.path.join(PROJ, "build")
APK_ASSETS = os.path.join(BUILD, "apk-assets")
RES = os.path.join(PROJ, "res")
SRC = os.path.join(PROJ, "src")
MANIFEST = os.path.join(PROJ, "AndroidManifest.xml")

KEYSTORE_DIR = os.path.join(PROJ, "keystore")
KEYSTORE = os.path.join(KEYSTORE_DIR, "guoneng-release.keystore")
KS_ALIAS = "guoneng"
KS_PASS = "guoneng2026"          # 与仓库一同公开：见 android/README.md 的说明
KS_DNAME = "CN=Guoneng Exam Prep, OU=Personal Study, O=Personal, L=-, ST=-, C=CN"

DELIVER_DIR = r"D:\DOWNLOADS"
APK_NAME_CN = "国家能源集团备考APP-v1.0.0.apk"
APK_NAME_ASCII = "guoneng-exam-prep-app-v1.0.0.apk"

VERSION_CODE = "1"
VERSION_NAME = "1.0.0"
MIN_SDK = "21"
TARGET_SDK = "34"


def tool(name):
    p = os.path.join(BUILD_TOOLS, name)
    if not os.path.isfile(p):
        raise SystemExit(f"❌ 缺少构建工具：{p}")
    return p


def jdk_tool(name):
    p = os.path.join(JDK, "bin", name)
    if not os.path.isfile(p):
        raise SystemExit(f"❌ 缺少 JDK 工具：{p}")
    return p


def run(cmd, label, cwd=None):
    """运行外部命令；.bat/.cmd 走 cmd /c。"""
    env = dict(os.environ)
    env["JAVA_HOME"] = JDK
    env["PATH"] = os.path.join(JDK, "bin") + os.pathsep + env.get("PATH", "")
    if cmd[0].lower().endswith((".bat", ".cmd")):
        cmd = ["cmd", "/c"] + cmd
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, env=env)
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    if r.returncode != 0:
        print(f"❌ {label} 失败（退出码 {r.returncode}）")
        print("  stdout:", out.strip()[-1500:])
        print("  stderr:", err.strip()[-1500:])
        raise SystemExit(1)
    print(f"  ✅ {label}")
    return out


def list_app_files():
    result = []
    for root, _dirs, files in os.walk(APP_SRC):
        for f in files:
            p = os.path.join(root, f)
            result.append((os.path.relpath(p, APP_SRC).replace("\\", "/"), p))
    return sorted(result)


def build_bundle():
    """把应用副本打成 ASCII 名的归档 + 版本标记。"""
    files = list_app_files()
    out_dir = os.path.join(BUILD, "apk-assets")
    os.makedirs(out_dir, exist_ok=True)
    bundle = os.path.join(out_dir, "www.zip")
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, path in files:
            z.write(path, rel)          # 非 ASCII 名字由 zipfile 自动带 UTF-8 标记
    raw = open(bundle, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    stamp = f"{VERSION_NAME} {len(raw)} {digest[:16]}"
    with open(os.path.join(out_dir, "www.id"), "w", encoding="utf-8", newline="\n") as f:
        f.write(stamp + "\n")
    print(f"  ✅ 生成归档 www.zip（{len(files)} 个文件，{len(raw)/1024/1024:.2f} MB）"
          f"与版本标记：{stamp}")
    return out_dir, files, raw


def clean_build():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)


def compile_resources():
    res_zip = os.path.join(BUILD, "res.zip")
    run([tool("aapt2.exe"), "compile", "--dir", RES, "-o", res_zip], "aapt2 compile 资源")
    return res_zip


def link_resources(res_zip, assets_dir):
    base = os.path.join(BUILD, "base.apk")
    gen = os.path.join(BUILD, "gen")
    os.makedirs(gen, exist_ok=True)
    run([tool("aapt2.exe"), "link",
         "-o", base,
         "-I", ANDROID_JAR,
         "--manifest", MANIFEST,
         res_zip,
         "--java", gen,
         "-A", assets_dir,
         "--min-sdk-version", MIN_SDK,
         "--target-sdk-version", TARGET_SDK,
         "--version-code", VERSION_CODE,
         "--version-name", VERSION_NAME], "aapt2 link 生成 base.apk（含 assets/www.zip）")
    return base, gen


def compile_java(gen):
    classes = os.path.join(BUILD, "classes")
    os.makedirs(classes, exist_ok=True)
    sources = []
    for root, _dirs, files in os.walk(SRC):
        sources += [os.path.join(root, f) for f in files if f.endswith(".java")]
    for root, _dirs, files in os.walk(gen):
        sources += [os.path.join(root, f) for f in files if f.endswith(".java")]
    if not sources:
        raise SystemExit("❌ 没有找到 Java 源码")
    run([jdk_tool("javac.exe"),
         "-source", "1.8", "-target", "1.8",
         "-bootclasspath", ANDROID_JAR,
         "-encoding", "UTF-8",
         "-nowarn",
         "-d", classes] + sources, f"javac 编译 {len(sources)} 个源文件")
    classes_jar = os.path.join(BUILD, "classes.jar")
    run([jdk_tool("jar.exe"), "cf", classes_jar, "-C", classes, "."], "打包 classes.jar")
    return classes_jar


def dex(classes_jar):
    dex_dir = os.path.join(BUILD, "dex")
    os.makedirs(dex_dir, exist_ok=True)
    run([tool("d8.bat"), "--release", "--min-api", MIN_SDK,
         "--lib", ANDROID_JAR,
         "--output", dex_dir, classes_jar], "d8 生成 classes.dex")
    dex_file = os.path.join(dex_dir, "classes.dex")
    if not os.path.isfile(dex_file):
        raise SystemExit("❌ 未生成 classes.dex")
    return dex_file


def inject_dex(base_apk, dex_file):
    out = os.path.join(BUILD, "unsigned.apk")
    with zipfile.ZipFile(base_apk, "r") as zin, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "classes.dex":
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.write(dex_file, "classes.dex")
    print("  ✅ 注入 classes.dex")
    return out


def align(apk):
    out = os.path.join(BUILD, "aligned.apk")
    run([tool("zipalign.exe"), "-p", "-f", "4", apk, out], "zipalign 4 字节对齐")
    return out


def ensure_keystore():
    os.makedirs(KEYSTORE_DIR, exist_ok=True)
    if os.path.isfile(KEYSTORE):
        print("  复用已有签名密钥")
        return
    run([jdk_tool("keytool.exe"), "-genkeypair", "-v",
         "-keystore", KEYSTORE,
         "-alias", KS_ALIAS,
         "-keyalg", "RSA", "-keysize", "2048", "-validity", "10950",
         "-storepass", KS_PASS, "-keypass", KS_PASS,
         "-dname", KS_DNAME], "keytool 生成签名密钥（有效期 30 年）")


def sign(aligned):
    out_cn = os.path.join(DELIVER_DIR, APK_NAME_CN)
    run([tool("apksigner.bat"), "sign",
         "--ks", KEYSTORE,
         "--ks-key-alias", KS_ALIAS,
         "--ks-pass", f"pass:{KS_PASS}",
         "--key-pass", f"pass:{KS_PASS}",
         "--v1-signing-enabled", "true",
         "--v2-signing-enabled", "true",
         "--v3-signing-enabled", "true",
         "--out", out_cn, aligned], "apksigner 签名（v1+v2+v3）")
    out_ascii = os.path.join(DELIVER_DIR, APK_NAME_ASCII)
    shutil.copy2(out_cn, out_ascii)
    return out_cn, out_ascii


def verify(apk_cn, apk_ascii, app_files, bundle_raw):
    print("\n== 自检 ==")
    out = run([tool("apksigner.bat"), "verify", "--verbose", "--print-certs", apk_cn],
              "apksigner verify 签名校验")
    for line in out.splitlines():
        if ("Verified using" in line or "Signer #1 certificate DN" in line
                or line.strip().startswith("SHA-256 digest")):
            print("    " + line.strip())

    badging = run([tool("aapt2.exe"), "dump", "badging", apk_cn], "aapt2 dump badging")
    keys = ("package:", "sdkVersion:", "targetSdkVersion:", "application-label",
            "uses-permission:", "native-code", "launchable-activity")
    for line in badging.splitlines():
        if line.startswith(keys):
            print("    " + line.strip())

    expected = {rel for rel, _p in app_files}
    with zipfile.ZipFile(apk_cn) as z:
        for must in ("AndroidManifest.xml", "classes.dex", "resources.arsc",
                     "assets/www.zip", "assets/www.id"):
            if must not in z.namelist():
                raise SystemExit(f"❌ APK 缺少关键条目：{must}")
        inner_raw = z.read("assets/www.zip")
        stamp_asset = z.read("assets/www.id").decode("utf-8").strip()
        with zipfile.ZipFile(io.BytesIO(inner_raw)) as inner:
            got = {n for n in inner.namelist() if not n.endswith("/")}
            qjs = inner.read("data/questions.js").decode("utf-8")

    missing = sorted(expected - got)
    extra = sorted(got - expected)
    print(f"    归档核对：应用 {len(expected)} 个文件｜归档内 {len(got)} 个"
          f"｜缺失 {len(missing)}｜多余 {len(extra)}")
    if missing:
        raise SystemExit(f"❌ 归档内缺失：{missing[:8]}")
    if extra:
        print(f"    ⚠️ 归档内多出：{extra[:8]}")

    inner_digest = hashlib.sha256(inner_raw).hexdigest()
    if inner_digest != hashlib.sha256(bundle_raw).hexdigest():
        raise SystemExit("❌ APK 内归档与构建产物不一致（可能被改动）")
    print(f"    归档内容 SHA-256 与构建产物一致：{inner_digest[:16]}…")
    stamp_expect = f"{VERSION_NAME} {len(bundle_raw)} {inner_digest[:16]}"
    if stamp_asset != stamp_expect:
        raise SystemExit(f"❌ 版本标记不符：{stamp_asset} ≠ {stamp_expect}")
    print(f"    版本标记：{stamp_asset}")

    n = qjs.count('"id":')
    print(f"    题库条目（按 id 计）：{n}")
    if n < 12000:
        raise SystemExit(f"❌ 题库条目异常：{n}")

    print(f"    APK 体积：{os.path.getsize(apk_cn)/1024/1024:.2f} MB"
          f"（ASCII 副本 {os.path.getsize(apk_ascii)/1024/1024:.2f} MB）")
    print("    APK SHA-256:", hashlib.sha256(open(apk_cn, "rb").read()).hexdigest())


def main():
    print("== 构建离线备考 APK ==")
    if not os.path.isdir(APP_SRC):
        raise SystemExit(f"❌ 缺少应用副本 {APP_SRC}（先运行 work/sync_app_to_repo.py）")
    clean_build()
    assets_dir, app_files, bundle_raw = build_bundle()
    res_zip = compile_resources()
    base_apk, gen = link_resources(res_zip, assets_dir)
    classes_jar = compile_java(gen)
    dex_file = dex(classes_jar)
    unsigned = inject_dex(base_apk, dex_file)
    aligned = align(unsigned)
    ensure_keystore()
    apk_cn, apk_ascii = sign(aligned)
    verify(apk_cn, apk_ascii, app_files, bundle_raw)
    print(f"\n✅ 完成\n   中文名：{apk_cn}\n   英文名：{apk_ascii}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
