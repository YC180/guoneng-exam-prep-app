import os, sys
sys.path.insert(0, os.path.abspath("."))
import sync_app_to_repo as S
print("is_junction(D:\\app project\\app) =", S.is_junction(r"D:\app project\app"))
print("is_junction(D:\\DOWNLOADS\\app)  =", S.is_junction(r"D:\DOWNLOADS\app"), "(应为 False)")
print("st_reparse_tag =", hex(getattr(os.lstat(r"D:\app project\app"), "st_reparse_tag", 0)))
