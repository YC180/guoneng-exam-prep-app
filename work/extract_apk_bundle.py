import io, os, sys, zipfile
APK = r"D:\DOWNLOADS\国家能源集团备考APP-v1.0.0.apk"
OUT = os.path.join(os.environ["TEMP"], "apk_bundle_check")
os.makedirs(OUT, exist_ok=True)
z = zipfile.ZipFile(APK)
inner = zipfile.ZipFile(io.BytesIO(z.read("assets/www.zip")))
inner.extractall(OUT)
n = sum(len(f) for _r, _d, f in os.walk(OUT))
print(f"  已解出 {n} 个文件 → {OUT}")
print("  版本标记:", z.read("assets/www.id").decode("utf-8").strip())
