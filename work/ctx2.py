import re
MOJIBAKE = ["鍥","锛","鐨","鏂","涓","绗","鐢","鏄","鎴","鏈","鍜","绛","棰","鍏"]
p = r"D:\DOWNLOADS\app\data\questions.js"
t = open(p, encoding="utf-8").read()
n = 0
for ch in MOJIBAKE:
    for m in re.finditer(re.escape(ch), t):
        n += 1
        print(f"{n:2d} [{ch}] …{t[max(0,m.start()-40):m.start()+40]}…")
print("总计", n)
