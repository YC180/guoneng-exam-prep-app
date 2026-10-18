import re
p = r"D:\DOWNLOADS\app\README.md"
for i, line in enumerate(open(p, encoding="utf-8"), 1):
    if re.search(r"11521|10956|10524|3335|356 份|282 份|约 14 MB|91\.3|498 题|67 题|4462|594|11,521", line):
        print(f"{i:4d}| {line.rstrip()[:150]}")
