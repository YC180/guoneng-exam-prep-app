for p in (r"D:\app project\work\_stray\diag_2021.py",
          r"D:\app project\work\_stray\diag_ocrprog.py"):
    t = open(p, encoding="utf-8").read()
    if "D:\\deepseek harness project" in t:
        open(p, "w", encoding="utf-8", newline="").write(t.replace("D:\\deepseek harness project", "D:\\app project"))
        print("已改写", p)
