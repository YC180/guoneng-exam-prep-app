import importlib, sys
mods = ["cv2", "fitz", "numpy", "onnxruntime", "rapidocr_onnxruntime", "pypdf", "docx", "win32com.client"]
for m in mods:
    try:
        mod = importlib.import_module(m)
        path = getattr(mod, "__file__", None) or "?"
        print(f"  ok   {m:22s} {str(path)[:66]}")
    except Exception as e:
        print(f"  FAIL {m:22s} {e}")
print("python:", sys.version.split()[0])
