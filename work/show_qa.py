import json
qa = json.load(open("bank/quality_audit.json", encoding="utf-8"))
print("顶层键:", list(qa.keys())[:12] if isinstance(qa, dict) else type(qa))
if isinstance(qa, dict):
    for k, v in qa.items():
        if not isinstance(v, (list, dict)):
            print(f"  {k} = {v}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={list(v.keys())[:8]}")
        else:
            print(f"  {k}: list len={len(v)}")
