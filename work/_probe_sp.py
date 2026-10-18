import sys, os
print("ARGV0", sys.argv[0])
print("CWD", os.getcwd())
for i, p in enumerate(sys.path):
    print(i, repr(p), "HAS_INSPECT" if os.path.exists(os.path.join(os.path.abspath(p or "."), "inspect.py")) else "")
